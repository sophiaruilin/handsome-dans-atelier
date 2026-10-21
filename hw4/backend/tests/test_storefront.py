"""Problem 10 storefront: affiliation / fit filters, Handsome Dan's Picks, reserve-for-pickup orders.

Run from backend/:  python -m pytest -q
Order tests run on a temporary copy of the database, so real stock is never touched.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import catalog_meta  # noqa: E402
import orders  # noqa: E402
import tools  # noqa: E402
from models import OrderItemIn, OrderRequest  # noqa: E402


def test_affiliations_cover_colleges_schools_teams_and_family():
    by_id = {p.product_id: p for p in tools.load_products()}
    assert by_id["saybrook-college-crewneck"].affiliation == "Saybrook"
    assert by_id["saybrook-college-crewneck"].affiliation_group == "college"
    assert by_id["school-of-medicine-1-4-zip"].affiliation == "School of Medicine"
    assert by_id["the-forest-school-hoodie"].affiliation_group == "school"
    assert by_id["yale-sports-hoodie-hockey"].affiliation == "Ice Hockey"
    assert by_id["yale-grandma-hoodie"].affiliation == "Grandma"
    assert by_id["basic-hoodie-big-yale"].affiliation is None  # general Yale gear
    assert by_id["brooks-brothers-bomber-jacket-yale"].affiliation is None  # "Brooks Brothers" is a brand, not a brother
    assert by_id["yale-brother-crewneck"].affiliation == "Brother"
    groups = {p.affiliation_group for p in by_id.values()}
    assert {"college", "school", "team", "family"} <= groups


def test_fit_is_inferred_and_mostly_unisex():
    by_id = {p.product_id: p for p in tools.load_products()}
    assert by_id["yale-mom-hoodie"].fit == "womens"
    assert by_id["ua-mens-tech-l-s-2-0"].fit == "mens"
    assert by_id["basic-hoodie-big-yale"].fit == "unisex"
    assert sum(p.fit == "unisex" for p in by_id.values()) > 80


def test_dan_picks_exist_and_reach_the_agent():
    for pid in catalog_meta.DAN_PICKS:
        p = tools.get_product(pid)
        assert p and p.dan_note
        assert tools.product_info(p).dan_note == p.dan_note
        assert tools.summary(p).dan_pick


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    copy = tmp_path / "campus_customs.db"
    shutil.copy(tools.DB_PATH, copy)
    monkeypatch.setattr(tools, "DB_PATH", copy)
    return copy


def _stock(db: Path, pid: str, size: str) -> int:
    with sqlite3.connect(db) as conn:
        return conn.execute("SELECT quantity FROM inventory WHERE product_id = ? AND size = ?", (pid, size)).fetchone()[0]


def test_reservation_holds_stock_and_uses_catalogue_prices(temp_db):
    before = _stock(temp_db, "basic-hoodie-big-yale", "XXL")
    req = OrderRequest(
        items=[
            OrderItemIn(product_id="basic-hoodie-big-yale", size="XXL", quantity=1),
            OrderItemIn(product_id="basic-hoodie-big-yale", size="2xl", quantity=1),  # same line, other spelling
        ],
        name="Ada Lovelace",
        email="Ada@Yale.edu",
        gift_wrap=True,
        gift_note="Boola boola!",
    )
    order = orders.create_order(req)
    assert order.order_number.startswith("CC-")
    assert len(order.items) == 1 and order.items[0].quantity == 2 and order.items[0].size == "XXL"
    assert order.subtotal == 2 * tools.get_product("basic-hoodie-big-yale").price
    assert order.email == "ada@yale.edu" and order.gift_wrap and order.gift_note == "Boola boola!"
    assert _stock(temp_db, "basic-hoodie-big-yale", "XXL") == before - 2


def test_cannot_reserve_more_than_is_left_and_nothing_changes(temp_db):
    pid, size = "basic-hoodie-big-yale", "XL"
    left = _stock(temp_db, pid, size)
    other_before = _stock(temp_db, pid, "XXL")
    req = OrderRequest(
        items=[OrderItemIn(product_id=pid, size="XXL", quantity=1), OrderItemIn(product_id=pid, size=size, quantity=left + 1)],
        name="Greedy Grad",
        email="g@yale.edu",
    )
    with pytest.raises(orders.OrderError, match=f"Only {left} left"):
        orders.create_order(req)
    # The whole reservation is rolled back, including the line that would have fit.
    assert _stock(temp_db, pid, size) == left and _stock(temp_db, pid, "XXL") == other_before


def test_sold_out_size_cannot_be_reserved(temp_db):
    req = OrderRequest(items=[OrderItemIn(product_id="champion-reverse-weave-crewneck", size="L", quantity=1)], name="A", email="a@yale.edu")
    with pytest.raises(orders.OrderError, match="sold out"):
        orders.create_order(req)
