"""Shop data helpers: read products and stock from data/campus_customs.db.

Used by main.py (product pages) and by the agent's tools in agent.py. Product tables are only
ever opened read-only.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import catalog_meta
from models import (
    CatalogueOverview,
    CustomerProfile,
    MyAccount,
    Product,
    ProductInfo,
    ProductSearchResult,
    ProductSummary,
    SearchFilters,
    SizeAvailability,
    SizeStock,
    StockCheck,
    StockStatus,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"
# Waitlist sign-ups live in their own file so the shop's product tables are never written.
WAITLIST_DB = Path(__file__).resolve().parent / "waitlist.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK_PER_SIZE = 5    # a size with 1-5 left is "selling fast"
LOW_STOCK_PER_STYLE = 25  # a style with 1-25 left across all sizes is "selling fast"
MAX_RESULTS = 8           # products one search returns to the agent


def shop_db() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
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
        tags = json.loads(r["search_tags"])
        aff = catalog_meta.affiliation(r["product_id"], r["name"], tags)
        products.append(
            Product(
                product_id=r["product_id"],
                name=r["name"],
                garment_type=r["garment_type"],
                description=r["description"],
                colors=json.loads(r["colors"]),
                search_tags=tags,
                image_url="/media/" + r["image_file_path"],
                price=r["price"],
                total_stock=total,
                stock_status=style_status(total),
                inventory=sizes,
                affiliation_group=aff[0] if aff else None,
                affiliation=aff[1] if aff else None,
                fit=catalog_meta.fit(r["name"], tags),
                dan_note=catalog_meta.dan_note(r["product_id"]),
            )
        )
    return products


def get_product(product_id: str) -> Product | None:
    found = load_products(product_id)
    return found[0] if found else None


def get_products(product_ids: list[str]) -> list[Product]:
    """Products for these ids, in the same order, skipping unknown ids."""
    by_id = {p.product_id: p for p in load_products()}
    return [by_id[i] for i in dict.fromkeys(product_ids) if i in by_id]


# --- Search --------------------------------------------------------------------------------

def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


# The catalogue's garment_type is free text ("pullover hoodie", "hooded sweatshirt", ...). These
# categories group it the same way as the Products page filters, so "hoodie" finds every hooded
# style and "t-shirt" doesn't match "sweatshirt".
GARMENT_CATEGORIES: dict[str, Callable[[str], bool]] = {
    "hoodie": lambda g: "hood" in g,
    "crewneck": lambda g: "crew" in g and "t-shirt" not in g and "hood" not in g,
    "t-shirt": lambda g: "t-shirt" in g or ("shirt" in g and "sweat" not in g),
    "quarter-zip": lambda g: "quarter-zip" in g,
    "jacket": lambda g: "jacket" in g or "fleece" in g,
    "sweatshirt": lambda g: "sweatshirt" in g,
}
GARMENT_ALIASES = {
    "hoodies": "hoodie", "hoody": "hoodie", "hooded": "hoodie", "hood": "hoodie", "hooded sweatshirt": "hoodie",
    "crewnecks": "crewneck", "crew": "crewneck", "crew neck": "crewneck", "crewneck sweatshirt": "crewneck",
    "t-shirts": "t-shirt", "tshirt": "t-shirt", "tshirts": "t-shirt", "tee": "t-shirt", "tees": "t-shirt",
    "shirt": "t-shirt", "shirts": "t-shirt",
    "quarter-zips": "quarter-zip", "quarter zip": "quarter-zip", "quarterzip": "quarter-zip", "1/4 zip": "quarter-zip",
    "jackets": "jacket", "fleece": "jacket", "fleeces": "jacket",
    "sweatshirts": "sweatshirt",
}


def garment_matches(garment_type: str, wanted: str) -> bool:
    """Does a catalogue garment_type fit what the shopper asked for ("hoodies", "tee", ...)?"""
    w = wanted.strip().lower()
    category = GARMENT_CATEGORIES.get(GARMENT_ALIASES.get(w, w))
    if category:
        return category(garment_type.lower())
    return all(_matches(word, garment_type.lower()) for word in _words(wanted))


def _matches(word: str, haystack: str) -> bool:
    # "hoodies" should find "hoodie", "tees" should find "tee".
    return word in haystack or (len(word) > 3 and word.endswith("s") and word[:-1] in haystack)


def search_products(
    query: str = "",
    garment_type: str = "",
    color: str = "",
    max_price: float | None = None,
    size: str = "",
    in_stock_only: bool = False,
) -> ProductSearchResult:
    """Filter the catalogue and return the first MAX_RESULTS matches as summaries (for the agent)."""
    results, note = _search(query, garment_type, color, max_price, size, in_stock_only)
    shown = results[:MAX_RESULTS]
    if len(results) > len(shown):
        note = (note + " " if note else "") + f"Showing {len(shown)} of {len(results)}; add filters to narrow down."
    return ProductSearchResult(
        total_matches=len(results), showing=len(shown), products=[summary(p) for p in shown], note=note
    )


def search_all(filters: SearchFilters) -> list[Product]:
    """Every match for a search, as full products (for the on-page results)."""
    return _search(**filters.model_dump())[0]


def _search(
    query: str = "",
    garment_type: str = "",
    color: str = "",
    max_price: float | None = None,
    size: str = "",
    in_stock_only: bool = False,
) -> tuple[list[Product], str]:
    shop_size = normalize_size(size) if size else None
    note = ""
    if size and not shop_size:
        note = f"We don't carry size {size!r}; sizes are {', '.join(SIZE_ORDER)}. Size filter ignored."
    results = []
    for p in load_products():
        text = " ".join([p.name, p.garment_type, p.description, *p.colors, *p.search_tags]).lower()
        if query and not all(_matches(w, text) for w in _words(query)):
            continue
        if garment_type and not garment_matches(p.garment_type, garment_type):
            continue
        # colors[0] is the garment itself; the rest are lettering and graphics. "Navy crewnecks"
        # means navy sweatshirts, not gray ones with navy lettering.
        if color and not (p.colors and color.lower() in p.colors[0].lower()):
            continue
        if max_price is not None and p.price > max_price:
            continue
        if shop_size and not any(s.size == shop_size and s.quantity > 0 for s in p.inventory):
            continue
        if in_stock_only and p.stock_status == "sold_out":
            continue
        results.append(p)
    # In-stock styles first, so the page and the agent lead with things the shopper can buy.
    results.sort(key=lambda p: p.stock_status == "sold_out")
    return results, note


def catalogue_overview() -> CatalogueOverview:
    """Garment types, colors, sizes and price range in the shop, so the agent can pick search filters."""
    products = load_products()
    return CatalogueOverview(
        product_count=len(products),
        garment_types=dict(Counter(p.garment_type.lower() for p in products).most_common()),
        colors=sorted({c.lower() for p in products for c in p.colors}),
        sizes=SIZE_ORDER,
        price_min=min(p.price for p in products),
        price_max=max(p.price for p in products),
    )


# --- Lookups for the agent -------------------------------------------------------------------

SIZE_ALIASES = {
    "xs": "XS", "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL", "double xl": "XXL",
}


def normalize_size(size: str) -> str | None:
    """'large' -> 'L', '2XL' -> 'XXL'. None if the shop doesn't carry that size (e.g. 3XL)."""
    return SIZE_ALIASES.get(re.sub(r"\s+", " ", size.strip().lower()))


def summary(p: Product) -> ProductSummary:
    return ProductSummary(
        product_id=p.product_id,
        name=p.name,
        garment_type=p.garment_type,
        price=p.price,
        colors=p.colors,
        stock_status=p.stock_status,
        sizes_in_stock=[s.size for s in p.inventory if s.quantity > 0],
        affiliation=p.affiliation,
        dan_pick=p.dan_note is not None,
    )


def product_info(p: Product) -> ProductInfo:
    return ProductInfo(
        product_id=p.product_id,
        name=p.name,
        garment_type=p.garment_type,
        description=p.description,
        price=p.price,
        colors=p.colors,
        stock_status=p.stock_status,
        affiliation=p.affiliation,
        dan_note=p.dan_note,
        total_stock=p.total_stock,
        sizes=[
            SizeAvailability(size=s.size, quantity=s.quantity, status=s.status, in_stock=s.quantity > 0)
            for s in p.inventory
        ],
        sizes_in_stock=[s.size for s in p.inventory if s.quantity > 0],
        sizes_sold_out=[s.size for s in p.inventory if s.quantity == 0],
    )


def stock_check(p: Product, size_asked: str) -> StockCheck:
    in_stock = [s.size for s in p.inventory if s.quantity > 0]
    size = normalize_size(size_asked)
    row = next((s for s in p.inventory if s.size == size), None)
    others = [s for s in in_stock if s != size]
    if row is None:
        message = (
            f"We don't carry {p.name} in size {size_asked}. "
            f"It comes in {', '.join(s.size for s in p.inventory)}."
        )
        return StockCheck(
            product_id=p.product_id, name=p.name, size_asked=size_asked, size=None, carried=False,
            quantity=0, status=None, in_stock=False, other_sizes_in_stock=in_stock, message=message,
        )
    if row.quantity == 0:
        message = f"{p.name} is SOLD OUT in size {row.size}."
        message += f" In stock in: {', '.join(others)}." if others else " It is sold out in every size."
    elif row.status == "selling_fast":
        message = f"{p.name} in size {row.size}: only {row.quantity} left (selling fast)."
    else:
        message = f"{p.name} in size {row.size}: {row.quantity} in stock."
    return StockCheck(
        product_id=p.product_id, name=p.name, size_asked=size_asked, size=row.size, carried=True,
        quantity=row.quantity, status=row.status, in_stock=row.quantity > 0,
        other_sizes_in_stock=others, message=message,
    )


# --- The logged-in shopper's own account (for the agent's get_my_account tool) ---------------

def my_account(customer: CustomerProfile) -> MyAccount:
    """Read-only summary of one shopper's own data. Always keyed by the session's user, never by model input."""
    with shop_db() as conn:
        saved = conn.execute("SELECT count(*) FROM chat_messages WHERE user_id = ?", (customer.user_id,)).fetchone()[0]
    waitlist: list[str] = []
    if WAITLIST_DB.exists():
        with sqlite3.connect(f"file:{WAITLIST_DB.as_posix()}?mode=ro", uri=True) as conn:
            rows = conn.execute(
                "SELECT product_id, size FROM waitlist WHERE email = ? ORDER BY id", (customer.email.lower(),)
            ).fetchall()
        names = {p.product_id: p.name for p in get_products([r[0] for r in rows])}
        waitlist = [f"{names.get(pid, pid)}{f' (size {size})' if size else ''}" for pid, size in rows]
    import orders  # local import: orders imports tools

    reservations = [
        f"{o.order_number} ({o.created_at[:10]}, pick up by {o.pickup_by}): "
        + ", ".join(f"{i.quantity}x {i.name} ({i.size})" for i in o.items)
        for o in orders.orders_for_user(customer.user_id, limit=5)
    ]
    return MyAccount(
        orders=reservations,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=customer.email,
        member_since=customer.member_since,
        saved_messages=saved,
        waitlist=waitlist,
    )


# --- Similar products (agent tool + "You might also like" on product pages) -----------------

def garment_category(garment_type: str) -> str | None:
    g = garment_type.lower()
    return next((name for name, match in GARMENT_CATEGORIES.items() if name != "sweatshirt" and match(g)), None)


def similar_products(
    product_id: str, limit: int = 4, color: str = "", max_price: float | None = None, size: str = ""
) -> list[Product]:
    """Styles most like this one: same garment category first, then shared tags and colors, in stock first.

    Optional filters narrow the alternatives, e.g. a different color or a size that is in stock.
    """
    base = get_product(product_id)
    if not base:
        return []
    shop_size = normalize_size(size) if size else None
    base_tags = {t.lower() for t in base.search_tags} - {"yale", "campus customs", "yale merch", "college apparel"}
    base_category = garment_category(base.garment_type)
    scored = []
    for p in load_products():
        if p.product_id == base.product_id or p.stock_status == "sold_out":
            continue
        if color and not (p.colors and color.lower() in p.colors[0].lower()):
            continue
        if max_price is not None and p.price > max_price:
            continue
        if shop_size and not any(s.size == shop_size and s.quantity > 0 for s in p.inventory):
            continue
        score = 0.0
        if base_category and garment_category(p.garment_type) == base_category:
            score += 5
        score += 1.5 * len(base_tags & {t.lower() for t in p.search_tags})
        if p.colors and base.colors and p.colors[0].lower() == base.colors[0].lower():
            score += 2
        score -= abs(p.price - base.price) / 20  # similar price point
        scored.append((score, p.name, p))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [p for _, _, p in scored[:limit]]


# --- Waitlist (website form + agent tool) ---------------------------------------------------

def add_to_waitlist(product_id: str, email: str, size: str | None = None) -> tuple[bool, str]:
    """Save a back-in-stock request. Returns (ok, message for the shopper)."""
    product = get_product(product_id)
    if not product:
        return False, f"No product has product_id {product_id!r}."
    shop_size = normalize_size(size) if size else None
    if size and not shop_size:
        return False, f"We don't make {product.name} in size {size}."
    if shop_size:
        row = next(s for s in product.inventory if s.size == shop_size)
        if row.quantity > 0:
            return False, f"{product.name} is in stock in size {shop_size} ({row.quantity} left), so no waitlist is needed."
    with sqlite3.connect(WAITLIST_DB) as conn:
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
        conn.execute(
            "INSERT OR IGNORE INTO waitlist (product_id, size, email, created_at) VALUES (?, ?, ?, datetime('now'))",
            (product_id, shop_size, email.lower()),
        )
    in_size = f" in size {shop_size}" if shop_size else ""
    return True, f"You're on the list! We'll email {email} when {product.name}{in_size} is back."


# --- Sensitive data ---------------------------------------------------------------------------

_CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")


def _luhn_ok(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def redact_card_numbers(text: str) -> tuple[str, bool]:
    """Mask anything that looks like a payment card number (13-19 digits passing the Luhn check)."""
    changed = False

    def mask(m: re.Match) -> str:
        nonlocal changed
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            changed = True
            return f"[card number removed •••• {digits[-4:]}]"
        return m.group()

    return _CARD_CANDIDATE.sub(mask, text), changed
