"""FastAPI back end for the Campus Customs website.

Serves the product catalogue, stock by size and product images from data/campus_customs.db,
handles create-account / login / logout (see auth.py), records waitlist sign-ups, and has a
stub chat route that Problem 5 will turn into the agent.

Run:  cd backend && .venv/Scripts/uvicorn main:app --port 8000
Docs: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import Cookie, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field

import auth

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"
# Waitlist sign-ups go in their own file so the shop database stays read-only.
WAITLIST_DB = Path(__file__).resolve().parent / "waitlist.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_PER_SIZE = 5    # a size with 1-5 left is "selling fast"
LOW_STOCK_PER_STYLE = 25  # a style with 1-25 left across all sizes is "selling fast"

StockStatus = Literal["in_stock", "selling_fast", "sold_out"]


class SizeStock(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    total_stock: int
    stock_status: StockStatus
    inventory: list[SizeStock]


class WaitlistRequest(BaseModel):
    product_id: str
    size: str | None = None
    email: EmailStr


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(max_length=auth.PASSWORD_MAX)
    confirm_password: str = Field(max_length=auth.PASSWORD_MAX)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=auth.PASSWORD_MAX)


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    name: str
    email: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[dict[str, str]] = Field(default_factory=list)
    product_id: str | None = None  # the product page the shopper is viewing, if any


class ChatResponse(BaseModel):
    reply: str
    products: list[Product] = Field(default_factory=list)


app = FastAPI(title="Campus Customs API")

# Let the Vite dev server (port 5173, or 5174+ if taken) call this API (port 8000).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="product-images")


def shop_db() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def users_db() -> sqlite3.Connection:
    """Writable connection for accounts and sessions. Product tables are only ever read."""
    conn = sqlite3.connect(DB_PATH)
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


def size_status(quantity: int) -> StockStatus:
    if quantity == 0:
        return "sold_out"
    return "selling_fast" if quantity <= LOW_STOCK_PER_SIZE else "in_stock"


def style_status(total: int) -> StockStatus:
    if total == 0:
        return "sold_out"
    return "selling_fast" if total <= LOW_STOCK_PER_STYLE else "in_stock"


def load_products(product_id: str | None = None) -> list[Product]:
    with shop_db() as conn:
        where, args = ("WHERE product_id = ?", (product_id,)) if product_id else ("", ())
        rows = conn.execute(f"SELECT * FROM catalogue {where} ORDER BY name", args).fetchall()
        stock: dict[str, list[SizeStock]] = {}
        for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            stock.setdefault(r["product_id"], []).append(
                SizeStock(size=r["size"], quantity=r["quantity"], status=size_status(r["quantity"]))
            )
    products = []
    for r in rows:
        sizes = sorted(
            stock.get(r["product_id"], []),
            key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else len(SIZE_ORDER),
        )
        total = sum(s.quantity for s in sizes)
        products.append(
            Product(
                product_id=r["product_id"],
                name=r["name"],
                garment_type=r["garment_type"],
                description=r["description"],
                colors=json.loads(r["colors"]),
                search_tags=json.loads(r["search_tags"]),
                image_url="/media/" + r["image_file_path"],
                price=r["price"],
                total_stock=total,
                stock_status=style_status(total),
                inventory=sizes,
            )
        )
    return products


@app.get("/api/health")
def health():
    return {"ok": True, "products": len(load_products())}


@app.get("/api/products", response_model=list[Product])
def list_products():
    return load_products()


@app.get("/api/products/{product_id}", response_model=Product)
def get_product(product_id: str):
    found = load_products(product_id)
    if not found:
        raise HTTPException(404, "Product not found")
    return found[0]


# --- Accounts ---------------------------------------------------------------------------

# Cookies need HTTPS when deployed; local development runs on plain http://localhost.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


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
        user_id = auth.session_user_id(conn, cc_session)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None
    return to_user(row) if row else None


# --- Waitlist and chat -------------------------------------------------------------------

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


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    # Stub until Problem 5 wires in the shop agent.
    return ChatResponse(
        reply="Thanks for your message! Our shop assistant is still in training. "
        "Soon I'll help you find sizes, colors and gifts. "
        "For now, browse the Products page or visit us at 57 Broadway, New Haven."
    )
