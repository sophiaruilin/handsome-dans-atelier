"""FastAPI back end for the Campus Customs website (the file uvicorn runs).

- Products: catalogue, stock by size and product images from data/campus_customs.db (tools.py).
- Accounts: create account / log in / log out with session cookies (auth.py).
- Chat: /api/chat runs the PydanticAI shop agent (agent.py) and saves logged-in shoppers' chats.
- Waitlist: back-in-stock email sign-ups.

Run:  cd backend && uvicorn main:app --reload --port 8000
Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

import auth
import tools
from agent import run_agent
from models import (
    MAX_HISTORY_MESSAGES,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    Product,
    SignupRequest,
    User,
    WaitlistRequest,
)

log = logging.getLogger("campus-customs")

# Waitlist sign-ups go in their own file so the shop's product tables are never written.
WAITLIST_DB = Path(__file__).resolve().parent / "waitlist.db"
# Cookies need HTTPS when deployed; local development runs on plain http://localhost.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

app = FastAPI(title="Campus Customs API")

# Let the Vite dev server call this API directly too (it normally goes through the Vite proxy).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=True,
)
app.mount("/media/products", StaticFiles(directory=tools.PRODUCTS_DIR), name="product-images")


def users_db() -> sqlite3.Connection:
    """Writable connection for accounts, sessions and chat history. Product tables are only ever read."""
    conn = sqlite3.connect(tools.DB_PATH)
    conn.row_factory = sqlite3.Row
    auth.ensure_sessions_table(conn)
    return conn


def waitlist_db() -> sqlite3.Connection:
    conn = sqlite3.connect(WAITLIST_DB)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            size TEXT,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE (product_id, size, email)
        )"""
    )
    return conn


# --- Products ------------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"ok": True, "products": len(tools.load_products())}


@app.get("/api/products", response_model=list[Product])
def list_products():
    return tools.load_products()


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    product = tools.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product


# --- Accounts ------------------------------------------------------------------------------

def to_user(row: sqlite3.Row) -> User:
    # Seeded rows may predate first_name/last_name, so fall back to splitting the full name.
    first, _, last = row["name"].partition(" ")
    return User(
        id=row["id"],
        first_name=row["first_name"] or first,
        last_name=row["last_name"] or last,
        name=row["name"],
        email=row["email"],
    )


def current_user(conn: sqlite3.Connection, token: str | None) -> User | None:
    user_id = auth.session_user_id(conn, token)
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None
    return to_user(row) if row else None


def start_session(response: Response, conn: sqlite3.Connection, user_id: int) -> None:
    token = auth.create_session(conn, user_id)
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=auth.SESSION_DAYS * 24 * 3600,
        httponly=True,  # page scripts can't read it, so injected JS can't steal the session
        samesite="lax",  # not sent on cross-site form posts
        secure=COOKIE_SECURE,
    )


@app.post("/api/auth/signup", response_model=User, status_code=201)
def signup(body: SignupRequest, response: Response):
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.lower()
    if body.password != body.confirm_password:
        raise HTTPException(400, "Passwords don't match.")
    problems = auth.password_problems(body.password, email, first, last)
    if problems:
        raise HTTPException(400, " ".join(problems))
    with users_db() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists. Try logging in.")
        cur = conn.execute(
            "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", first, last, email, auth.hash_password(body.password)),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        start_session(response, conn, row["id"])
    return to_user(row)


@app.post("/api/auth/login", response_model=User)
def login(body: LoginRequest, request: Request, response: Response):
    email = body.email.lower()
    limit_key = f"{email}|{request.client.host if request.client else ''}"
    if auth.too_many_failures(limit_key):
        raise HTTPException(429, "Too many attempts. Please wait 15 minutes and try again.")
    with users_db() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        if row:
            ok = auth.verify_password(body.password, row["password_hash"])
        else:
            auth.verify_dummy(body.password)
            ok = False
        if not ok:
            auth.record_failure(limit_key)
            # Same message either way, so the form doesn't reveal which emails have accounts.
            raise HTTPException(401, "Email or password is incorrect.")
        auth.clear_failures(limit_key)
        start_session(response, conn, row["id"])
    return to_user(row)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response, cc_session: str | None = Cookie(default=None)):
    with users_db() as conn:
        auth.delete_session(conn, cc_session)
    response.delete_cookie(auth.SESSION_COOKIE)


@app.get("/api/auth/me", response_model=User | None)
def me(cc_session: str | None = Cookie(default=None)):
    with users_db() as conn:
        return current_user(conn, cc_session)


# --- Chat ----------------------------------------------------------------------------------

def save_message(conn: sqlite3.Connection, user_id: int, role: str, content: str, products: list[Product]) -> None:
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
        (user_id, role, content, products_json),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, cc_session: str | None = Cookie(default=None)):
    with users_db() as conn:
        user = current_user(conn, cc_session)
    product_id = body.product_id if body.product_id and tools.get_product(body.product_id) else None
    try:
        result = await run_agent(body.message, body.history, product_id, user)
    except UsageLimitExceeded:
        raise HTTPException(429, "That question needed too many steps. Try asking something more specific.")
    except (ModelHTTPError, RuntimeError):
        log.exception("chat failed")
        raise HTTPException(502, "The shop assistant is unavailable right now. Please try again in a moment.")
    if user:
        with users_db() as conn:
            save_message(conn, user.id, "user", body.message, [])
            save_message(conn, user.id, "assistant", result.reply, result.products)
    return result


@app.get("/api/chat/history", response_model=list[ChatMessage])
def chat_history(cc_session: str | None = Cookie(default=None)):
    """A logged-in shopper's recent chat, so the widget picks up where they left off."""
    with users_db() as conn:
        user = current_user(conn, cc_session)
        if not user:
            return []
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user.id, MAX_HISTORY_MESSAGES),
        ).fetchall()
    messages = []
    for r in reversed(rows):
        # Re-read saved cards from the catalogue so prices and stock are current.
        ids = [p["product_id"] for p in json.loads(r["products_json"] or "[]")]
        messages.append(ChatMessage(role=r["role"], content=r["content"], products=tools.get_products(ids)))
    return messages


# --- Waitlist ------------------------------------------------------------------------------

@app.post("/api/waitlist")
def join_waitlist(body: WaitlistRequest):
    product = get_product(body.product_id)
    if body.size and body.size not in {s.size for s in product.inventory}:
        raise HTTPException(400, "Unknown size for this product")
    with waitlist_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO waitlist (product_id, size, email, created_at) VALUES (?, ?, ?, ?)",
            (body.product_id, body.size, body.email.lower(), datetime.now(timezone.utc).isoformat()),
        )
    size = f" in size {body.size}" if body.size else ""
    return {"ok": True, "message": f"You're on the list! We'll email {body.email} when {product.name}{size} is back."}
