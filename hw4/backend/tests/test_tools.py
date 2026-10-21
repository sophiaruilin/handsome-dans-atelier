"""Check that the agent's lookup tools return exactly what campus_customs.db says.

Run from backend/:  python -m pytest -q
No model calls: these test tools.py directly against the database.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import tools  # noqa: E402


def db() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{tools.DB_PATH.as_posix()}?mode=ro", uri=True)


def sql_price(product_id: str) -> float:
    with db() as conn:
        return conn.execute("SELECT price FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()[0]


def sql_stock(product_id: str) -> dict[str, int]:
    with db() as conn:
        rows = conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,))
        return dict(rows.fetchall())


def first_with_quantity(condition) -> tuple[str, str, int]:
    """(product_id, size, quantity) of the first inventory row matching the condition."""
    with db() as conn:
        for pid, size, qty in conn.execute("SELECT product_id, size, quantity FROM inventory ORDER BY id"):
            if condition(qty):
                return pid, size, qty
    raise AssertionError("no matching inventory row")


def test_product_info_matches_database_for_every_product():
    for product in tools.load_products():
        info = tools.product_info(product)
        assert info.price == sql_price(product.product_id)
        assert {s.size: s.quantity for s in info.sizes} == sql_stock(product.product_id)
        assert info.total_stock == sum(sql_stock(product.product_id).values())
        assert set(info.sizes_in_stock) == {s for s, q in sql_stock(product.product_id).items() if q > 0}
        assert set(info.sizes_sold_out) == {s for s, q in sql_stock(product.product_id).items() if q == 0}


def test_check_stock_sold_out_size_says_so_clearly():
    pid, size, _ = first_with_quantity(lambda q: q == 0)
    result = tools.stock_check(tools.get_product(pid), size)
    assert result.carried and not result.in_stock
    assert result.quantity == 0 and result.status == "sold_out"
    assert "SOLD OUT" in result.message and size in result.message
    assert size not in result.other_sizes_in_stock


def test_check_stock_low_and_normal_quantities():
    pid, size, qty = first_with_quantity(lambda q: 1 <= q <= tools.LOW_STOCK_PER_SIZE)
    low = tools.stock_check(tools.get_product(pid), size)
    assert low.quantity == qty and low.status == "selling_fast" and f"only {qty} left" in low.message

    pid, size, qty = first_with_quantity(lambda q: q > tools.LOW_STOCK_PER_SIZE)
    ok = tools.stock_check(tools.get_product(pid), size)
    assert ok.quantity == qty and ok.status == "in_stock" and ok.in_stock


@pytest.mark.parametrize(
    ("typed", "expected"),
    [("L", "L"), ("large", "L"), (" Extra Large ", "XL"), ("2XL", "XXL"), ("xs", "XS"), ("3XL", None), ("youth M", None)],
)
def test_normalize_size(typed, expected):
    assert tools.normalize_size(typed) == expected


def test_check_stock_size_we_dont_make():
    product = tools.load_products()[0]
    result = tools.stock_check(product, "3XL")
    assert not result.carried and result.size is None and result.quantity == 0
    assert "don't carry" in result.message


def test_search_finds_by_keyword_and_respects_filters():
    result = tools.search_products(garment_type="hoodie", color="navy", max_price=70, size="large")
    assert result.total_matches > 0
    for s in result.products:
        assert "hood" in s.garment_type.lower()
        assert "navy" in s.colors[0].lower()
        assert s.price <= 70
        assert "L" in s.sizes_in_stock
        assert s.price == sql_price(s.product_id)


def test_search_unknown_size_is_flagged_not_silently_ignored():
    result = tools.search_products(query="hoodie", size="3XL")
    assert "don't carry size" in result.note


def test_search_no_match():
    result = tools.search_products(query="snorkel")
    assert result.total_matches == 0 and result.products == []


@pytest.mark.parametrize(
    ("asked", "must_contain", "must_not_contain"),
    [
        ("hoodies", "hood", None),
        ("t-shirt", None, "sweatshirt"),
        ("tee", None, "sweatshirt"),
        ("crewneck", "crew", "hood"),
        ("quarter zip", "quarter-zip", None),
    ],
)
def test_garment_categories(asked, must_contain, must_not_contain):
    found = tools.search_all(tools.SearchFilters(garment_type=asked))
    assert found
    for p in found:
        g = p.garment_type.lower()
        if must_contain:
            assert must_contain in g
        if must_not_contain:
            assert must_not_contain not in g


def test_hoodie_search_finds_every_hooded_style():
    with db() as conn:
        expected = conn.execute("SELECT count(*) FROM catalogue WHERE lower(garment_type) LIKE '%hood%'").fetchone()[0]
    assert len(tools.search_all(tools.SearchFilters(garment_type="hoodie"))) == expected


def test_color_filter_uses_main_garment_color_not_lettering():
    found = tools.search_all(tools.SearchFilters(garment_type="crewneck", color="navy"))
    assert found and all("navy" in p.colors[0].lower() for p in found)
    # e.g. a light gray crewneck with navy lettering is not a "navy crewneck"
    assert not any(p.colors[0].lower().startswith("light gray") for p in found)
