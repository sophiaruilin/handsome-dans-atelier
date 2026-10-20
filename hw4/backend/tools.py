"""Shop data helpers: read products and stock from data/campus_customs.db.

Used by main.py (product pages) and by the agent's tools in agent.py. Product tables are only
ever opened read-only.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path

from models import (
    CatalogueOverview,
    Product,
    ProductInfo,
    ProductSearchResult,
    ProductSummary,
    SizeAvailability,
    SizeStock,
    StockCheck,
    StockStatus,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"

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
    """Filter the catalogue and return the first MAX_RESULTS matches as summaries."""
    shop_size = normalize_size(size) if size else None
    note = ""
    if size and not shop_size:
        note = f"We don't carry size {size!r}; sizes are {', '.join(SIZE_ORDER)}. Size filter ignored."
    results = []
    for p in load_products():
        text = " ".join([p.name, p.garment_type, p.description, *p.colors, *p.search_tags]).lower()
        if query and not all(_matches(w, text) for w in _words(query)):
            continue
        if garment_type and not all(_matches(w, p.garment_type.lower()) for w in _words(garment_type)):
            continue
        if color and not any(color.lower() in c.lower() for c in p.colors):
            continue
        if max_price is not None and p.price > max_price:
            continue
        if shop_size and not any(s.size == shop_size and s.quantity > 0 for s in p.inventory):
            continue
        if in_stock_only and p.stock_status == "sold_out":
            continue
        results.append(p)
    shown = results[:MAX_RESULTS]
    if len(results) > len(shown):
        note = (note + " " if note else "") + f"Showing {len(shown)} of {len(results)}; add filters to narrow down."
    return ProductSearchResult(
        total_matches=len(results), showing=len(shown), products=[summary(p) for p in shown], note=note
    )


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
