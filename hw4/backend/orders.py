"""Reserve-for-pickup orders (Problem 10).

The shop takes no payments online. A shopper's bag becomes a reservation that is held for 3 days at
57 Broadway: the stock is taken off the shelf straight away (inventory goes down), so nobody else can
buy the last one while they're on their way. Prices always come from the catalogue, never the browser.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone

import tools
from models import Order, OrderItem, OrderRequest

HOLD_DAYS = 3


class OrderError(ValueError):
    """A reservation that can't be made (e.g. not enough stock). The message is safe to show the shopper."""


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(tools.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'reserved',
            gift_wrap INTEGER NOT NULL DEFAULT 0,
            gift_note TEXT NOT NULL DEFAULT '',
            subtotal REAL NOT NULL,
            created_at TEXT NOT NULL,
            pickup_by TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id TEXT NOT NULL,
            size TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES catalogue(product_id)
        )"""
    )
    return conn


def order_number(order_id: int) -> str:
    return f"CC-{order_id:05d}"


def create_order(req: OrderRequest, user_id: int | None = None) -> Order:
    # Merge duplicate lines (same product and size) and normalise sizes ("large" -> "L").
    wanted: Counter[tuple[str, str]] = Counter()
    for item in req.items:
        size = tools.normalize_size(item.size)
        if not size:
            raise OrderError(f"We don't make size {item.size!r}.")
        wanted[(item.product_id, size)] += item.quantity

    conn = _db()
    try:
        # BEGIN IMMEDIATE takes the write lock first, so two shoppers can't both reserve the last one.
        conn.execute("BEGIN IMMEDIATE")
        lines: list[OrderItem] = []
        for (pid, size), qty in wanted.items():
            product = conn.execute(
                "SELECT name, price, image_file_path FROM catalogue WHERE product_id = ?", (pid,)
            ).fetchone()
            if not product:
                raise OrderError(f"Unknown product {pid!r}.")
            row = conn.execute(
                "SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (pid, size)
            ).fetchone()
            left = row["quantity"] if row else 0
            if left < qty:
                name = product["name"]
                raise OrderError(f"Only {left} left of {name} in size {size}." if left else f"{name} is sold out in size {size}.")
            conn.execute(
                "UPDATE inventory SET quantity = quantity - ? WHERE product_id = ? AND size = ?", (qty, pid, size)
            )
            lines.append(
                OrderItem(
                    product_id=pid,
                    name=product["name"],
                    size=size,
                    quantity=qty,
                    unit_price=product["price"],
                    image_url="/media/" + product["image_file_path"],
                )
            )
        subtotal = round(sum(line.unit_price * line.quantity for line in lines), 2)
        now = datetime.now(timezone.utc)
        created = now.strftime("%Y-%m-%d %H:%M:%S")
        pickup_by = (now + timedelta(days=HOLD_DAYS)).strftime("%Y-%m-%d")
        cur = conn.execute(
            "INSERT INTO orders (user_id, name, email, gift_wrap, gift_note, subtotal, created_at, pickup_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, req.name.strip(), req.email.lower(), int(req.gift_wrap), req.gift_note.strip(), subtotal, created, pickup_by),
        )
        order_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO order_items (order_id, product_id, size, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
            [(order_id, line.product_id, line.size, line.quantity, line.unit_price) for line in lines],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return Order(
        order_number=order_number(order_id),
        name=req.name.strip(),
        email=req.email.lower(),
        status="reserved",
        items=lines,
        subtotal=subtotal,
        gift_wrap=req.gift_wrap,
        gift_note=req.gift_note.strip(),
        created_at=created,
        pickup_by=pickup_by,
    )


def orders_for_user(user_id: int, limit: int = 10) -> list[Order]:
    conn = _db()
    try:
        result = []
        for o in conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)).fetchall():
            items = [
                OrderItem(
                    product_id=i["product_id"],
                    name=i["name"],
                    size=i["size"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                    image_url="/media/" + i["image_file_path"],
                )
                for i in conn.execute(
                    "SELECT oi.*, c.name, c.image_file_path FROM order_items oi JOIN catalogue c USING (product_id) "
                    "WHERE oi.order_id = ? ORDER BY oi.id",
                    (o["id"],),
                ).fetchall()
            ]
            result.append(
                Order(
                    order_number=order_number(o["id"]),
                    name=o["name"],
                    email=o["email"],
                    status=o["status"],
                    items=items,
                    subtotal=o["subtotal"],
                    gift_wrap=bool(o["gift_wrap"]),
                    gift_note=o["gift_note"],
                    created_at=o["created_at"],
                    pickup_by=o["pickup_by"],
                )
            )
        return result
    finally:
        conn.close()
