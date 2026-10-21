"""Problem 9 back-end improvements: similar products, waitlist rules, card redaction, price fact-checker.

Run from backend/:  python -m pytest -q   (no model calls)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

import agent  # noqa: E402
import tools  # noqa: E402
from models import ShopReply  # noqa: E402
from pydantic_ai import ModelRetry  # noqa: E402


def test_similar_products_are_in_stock_alternatives_of_the_same_kind():
    base = tools.get_product("basic-hoodie-big-yale")
    similar = tools.similar_products(base.product_id, limit=4)
    assert len(similar) == 4
    assert base.product_id not in {p.product_id for p in similar}
    assert all(p.stock_status != "sold_out" for p in similar)
    assert all(tools.garment_category(p.garment_type) == "hoodie" for p in similar)


def test_similar_products_respect_filters():
    found = tools.similar_products("basic-hoodie-big-yale", color="gray", max_price=70, size="XL")
    assert found
    for p in found:
        assert "gray" in p.colors[0].lower() and p.price <= 70
        assert any(s.size == "XL" and s.quantity > 0 for s in p.inventory)


def test_waitlist_rules(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "WAITLIST_DB", tmp_path / "waitlist.db")
    # Size that is in stock: no waitlist needed.
    ok, msg = tools.add_to_waitlist("basic-hoodie-big-yale", "a@yale.edu", "XXL")
    assert not ok and "in stock" in msg
    # Size we don't make.
    ok, msg = tools.add_to_waitlist("basic-hoodie-big-yale", "a@yale.edu", "3XL")
    assert not ok
    # Sold-out size: added (and adding twice doesn't duplicate).
    ok, msg = tools.add_to_waitlist("champion-reverse-weave-crewneck", "A@Yale.edu", "large")
    assert ok and "size L" in msg
    tools.add_to_waitlist("champion-reverse-weave-crewneck", "a@yale.edu", "L")
    customer = SimpleNamespace(user_id=-1, first_name="A", last_name="B", email="a@yale.edu", member_since="2026-01-01")
    assert tools.my_account(customer).waitlist == ["Champion Reverse Weave Crewneck (size L)"]


@pytest.mark.parametrize(
    ("text", "masked"),
    [
        ("card 4111 1111 1111 1111 please", True),
        ("4111-1111-1111-1111", True),
        ("378282246310005", True),  # Amex test number
        ("call 203-555-0100", False),
        ("order 12345678901234", False),  # long number that fails the Luhn check
    ],
)
def test_card_redaction(text, masked):
    out, changed = tools.redact_card_numbers(text)
    assert changed is masked
    if masked:
        assert "card number removed" in out and "4111 1111 1111 1111" not in out


def _ctx(prices, message):
    deps = agent.ShopState(shopper_message=message)
    deps.saw(*prices)
    return SimpleNamespace(deps=deps)


def test_price_checker_accepts_real_prices_and_the_shoppers_budget():
    ctx = _ctx([58.0, 68.0], "anything under $60?")
    reply = ShopReply(reply="The crewneck is **$58.00** (under your $60 budget); the hoodie is $68.")
    assert agent.check_prices(ctx, reply) is reply


def test_price_checker_rejects_an_invented_price():
    ctx = _ctx([58.0], "how much is it?")
    with pytest.raises(ModelRetry, match=r"\$49\.99"):
        agent.check_prices(ctx, ShopReply(reply="It's on sale for $49.99 today!"))
    assert ctx.deps.price_corrections == 1
