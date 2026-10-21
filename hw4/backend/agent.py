"""PydanticAI Campus Customs shop agent, called by the /api/chat route in main.py.

run_agent(message, history, page, customer) -> ChatResponse with the reply, the product
cards to show under it, on-page search results (when the shopper is browsing), and which tools ran.

- Instructions: prompts/prompt.md (re-read each message), plus two per-message blocks built from
  the deps: who is chatting (CustomerProfile, logged-in shoppers only) and where they are
  (PageContext; product facts looked up from the database).
- Model: gpt-6-astra via Portkey (PORTKEY_API_KEY in .env), through the OpenAI Responses API.
  Override with OPENAI_MODEL=...
- Tools: search_products, get_product_info, check_stock and catalogue_overview. Thin wrappers
  over tools.py, which reads the shop database read-only, returning typed results (models.py).

Try it without the website:  python agent.py "Do you have navy hoodies under $70?"
"""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import (
    MAX_CARDS,
    MAX_HISTORY_MESSAGES,
    CatalogueOverview,
    ChatMessage,
    ChatResponse,
    CustomerProfile,
    MyAccount,
    PageContext,
    PageResults,
    ProductInfo,
    ProductSearchResult,
    ProductSummary,
    SearchFilters,
    ShopReply,
    StockCheck,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
DEFAULT_MODEL = "gpt-6-astra"
MAX_REQUESTS = 8  # model calls per chat turn (bounds cost if the agent loops on tools)
USAGE_LOG = BACKEND_DIR / "logs" / "chat_usage.jsonl"  # per-turn speed/token log (git-ignored)

# .env may live in backend/, hw4/ or the class folder. Never commit it.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")
load_dotenv(BACKEND_DIR.parent.parent / ".env")


@dataclass
class ShopState:
    """Agent deps: who is chatting and where they are. Built by main.py from the session and the request."""

    customer: CustomerProfile | None = None  # None for guests
    page: PageContext = field(default_factory=PageContext)
    tools_used: list[str] = field(default_factory=list)
    # Each search_products call and its match count, so the page can show the agent's search.
    searches: list[tuple[SearchFilters, int]] = field(default_factory=list)
    # Every price the tools (or the page context) returned this turn; the fact-checker allows only these.
    known_prices: set[float] = field(default_factory=set)
    shopper_message: str = ""
    price_corrections: int = 0

    def saw(self, *prices: float) -> None:
        self.known_prices.update(round(p, 2) for p in prices)


agent = Agent(deps_type=ShopState, output_type=ShopReply, retries=2)


@agent.instructions
def shop_prompt() -> str:
    # Read on every message: `uvicorn --reload` only watches .py files, so edits to prompt.md
    # take effect without a restart.
    return PROMPT_PATH.read_text(encoding="utf-8")


@agent.instructions
def customer_context(ctx: RunContext[ShopState]) -> str:
    """Who is chatting. Name only; the email stays behind the get_my_account tool until it's needed."""
    c = ctx.deps.customer
    if not c:
        return (
            "## Who you're talking to\nA guest (not logged in). Their chat isn't saved; if they want you to "
            "remember them next time, they can create an account."
        )
    return (
        f"## Who you're talking to\nA logged-in customer: **{c.first_name} {c.last_name}**, member since "
        f"{c.member_since}. Greet them by first name. Earlier messages in this chat come from their saved history, "
        "so you can refer back to them (\"the hoodie you asked about last time\"). For their email, waitlist or "
        "account details, call `get_my_account`."
    )


@agent.instructions
def page_context(ctx: RunContext[ShopState]) -> str:
    """Where the shopper is. The browser sends only ids; the facts come from the database."""
    page = ctx.deps.page
    lines = ["## Where the shopper is", f"Page: `{page.path}`"]
    p = tools.get_product(page.product_id) if page.product_id else None
    if p:
        ctx.deps.saw(p.price)
        stock = ", ".join(
            f"{s.size} SOLD OUT" if s.quantity == 0
            else f"{s.size} {s.quantity} left" + (" (selling fast)" if s.status == "selling_fast" else "")
            for s in p.inventory
        )
        lines += [
            f"They are on the product page for **{p.name}** (product_id `{p.product_id}`): {p.garment_type}, "
            f"${p.price:.2f}, colors: {', '.join(p.colors)}.",
            f"Live stock for this product, read from the database for this message: {stock}. Answer price and "
            "size questions about this product from this line; no tool call is needed.",
            "\"This\", \"it\", \"this one\" and \"the one I'm looking at\" mean this product. Use its product_id with "
            "get_product_info or check_stock; don't ask which item they mean.",
            "Colors are fixed per product (there are no color options), so for \"do you have this in pink?\" say "
            "which colors this one comes in, then search for similar items in the color they asked for.",
        ]
    elif page.results_title:
        lines.append(f'The Products page is showing chat search results titled "{page.results_title}".')
    else:
        lines.append("They are not on a product page.")
    return "\n".join(lines)


def _lookup(product_id: str):
    """Product for an id, or ask the model to search first (it retries with a real id)."""
    p = tools.get_product(product_id)
    if not p:
        raise ModelRetry(f"No product has product_id {product_id!r}. Call search_products to find the right id.")
    return p


@agent.tool
def search_products(
    ctx: RunContext[ShopState],
    query: str = "",
    garment_type: str = "",
    color: str = "",
    max_price: float | None = None,
    size: str = "",
    in_stock_only: bool = False,
) -> ProductSearchResult:
    """Find products. Every filter is optional; combine only what the shopper asked for.

    Returns summaries (price, colors, which sizes are in stock). For exact stock counts or the full
    description, follow up with get_product_info or check_stock.

    Args:
        query: keywords that must all appear in the name, description, colors or tags, e.g. "hockey" or "Saybrook".
        garment_type: e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: the garment's main color, e.g. "navy", "gray", "white" (ignores lettering/graphic colors).
        max_price: highest price in US dollars.
        size: only products with this size in stock, e.g. "L" or "large".
        in_stock_only: skip styles that are sold out in every size.
    """
    ctx.deps.tools_used.append("search_products")
    result = tools.search_products(query, garment_type, color, max_price, size, in_stock_only)
    filters = SearchFilters(
        query=query, garment_type=garment_type, color=color, max_price=max_price, size=size, in_stock_only=in_stock_only
    )
    ctx.deps.searches.append((filters, result.total_matches))
    ctx.deps.saw(*(p.price for p in result.products))
    return result


@agent.tool
def get_product_info(ctx: RunContext[ShopState], product_id: str) -> ProductInfo:
    """Full description, price, colors and units in stock for every size of one product.

    Use for "tell me about", "how much is" and "which sizes do you have" questions.
    """
    ctx.deps.tools_used.append("get_product_info")
    p = _lookup(product_id)
    ctx.deps.saw(p.price)
    return tools.product_info(p)


@agent.tool
def check_stock(ctx: RunContext[ShopState], product_id: str, size: str) -> StockCheck:
    """Is one size of one product in stock, and how many are left?

    Args:
        product_id: from search results or the page context.
        size: the size the shopper asked about, as they wrote it, e.g. "L", "large" or "2XL".
    """
    ctx.deps.tools_used.append("check_stock")
    p = _lookup(product_id)
    ctx.deps.saw(p.price)
    return tools.stock_check(p, size)


@agent.tool
def find_similar_products(
    ctx: RunContext[ShopState], product_id: str, color: str = "", max_price: float | None = None, size: str = ""
) -> list[ProductSummary]:
    """Up to 4 in-stock styles most like this product (same garment type, shared themes, similar price).

    Use for "anything like this?", "something similar in gray?", or when the asked-for size or color isn't
    available and you want to offer alternatives.

    Args:
        product_id: the product to find alternatives for.
        color: only alternatives whose main color matches, e.g. "gray".
        max_price: only alternatives at or under this price.
        size: only alternatives with this size in stock.
    """
    ctx.deps.tools_used.append("find_similar_products")
    _lookup(product_id)
    found = tools.similar_products(product_id, color=color, max_price=max_price, size=size)
    ctx.deps.saw(*(p.price for p in found))
    return [tools.summary(p) for p in found]


@agent.tool
def join_waitlist(ctx: RunContext[ShopState], product_id: str, size: str = "") -> str:
    """Add the logged-in shopper to the back-in-stock email list for a sold-out product or size.

    Only call this when the shopper asks to be notified or agrees to join. Uses the email on their
    account. Guests should use the waitlist form on the product page or log in.
    """
    ctx.deps.tools_used.append("join_waitlist")
    if not ctx.deps.customer:
        return "The shopper is a guest. Ask them to log in, or use the waitlist form on the product page."
    _lookup(product_id)
    ok, message = tools.add_to_waitlist(product_id, ctx.deps.customer.email, size or None)
    return message if ok else f"Not added: {message}"


@agent.tool
def get_my_account(ctx: RunContext[ShopState]) -> MyAccount | str:
    """The logged-in shopper's own details: name, email, member-since date, saved chat size and waitlist.

    Use when they ask about their account, email or waitlist. Only ever returns the current shopper's data.
    """
    ctx.deps.tools_used.append("get_my_account")
    if not ctx.deps.customer:
        return "The shopper is a guest (not logged in), so there is no account to look up."
    return tools.my_account(ctx.deps.customer)


@agent.tool
def catalogue_overview(ctx: RunContext[ShopState]) -> CatalogueOverview:
    """Garment types (with counts), colors, sizes and price range the shop carries."""
    ctx.deps.tools_used.append("catalogue_overview")
    return tools.catalogue_overview()


_PRICE = re.compile(r"\$\s?(\d{1,4}(?:,\d{3})*(?:\.\d{1,2})?)")


@agent.output_validator
def check_prices(ctx: RunContext[ShopState], output: ShopReply) -> ShopReply:
    """Fact-check: every $ amount in the reply must be a price a tool returned this turn (or a number the
    shopper wrote, like a budget). Otherwise the model must correct it, so a made-up price never reaches a shopper."""
    allowed = set(ctx.deps.known_prices)
    allowed.update(round(float(n.replace(",", "")), 2) for n in re.findall(r"\d+(?:,\d{3})*(?:\.\d{1,2})?", ctx.deps.shopper_message))
    found = {m for m in _PRICE.findall(output.reply)}
    unknown = sorted(m for m in found if round(float(m.replace(",", "")), 2) not in allowed)
    if unknown:
        ctx.deps.price_corrections += 1
        raise ModelRetry(
            f"Your reply mentions {', '.join('$' + u for u in unknown)}, which is not the price of any product a tool "
            "returned this turn. Look the price up with get_product_info (or remove it), then answer again."
        )
    return output


def _history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Chat log -> PydanticAI message history (most recent turns only).

    Assistant turns get a note of the products their cards showed, so "the second one" or
    "the hoodie you showed me" resolves to a real product_id.
    """
    out: list[ModelMessage] = []
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        if m.role == "user":
            out.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            shown = "; ".join(f"{i}. {p.name} ({p.product_id})" for i, p in enumerate(m.products, 1))
            text = f"{m.content}\n\n[Product cards shown: {shown}]" if shown else m.content
            out.append(ModelResponse(parts=[TextPart(content=text)]))
    return out


def _client_and_model() -> tuple[AsyncOpenAI, OpenAIResponsesModel]:
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Add it to .env")
    client = AsyncOpenAI(
        api_key="unused",  # Portkey authenticates with the header below
        base_url=PORTKEY_BASE_URL,
        default_headers={
            "x-portkey-api-key": api_key,
            "x-portkey-provider": "openai",
            # The class Portkey key caches identical requests. A replayed answer could quote stock
            # that has since changed, so always ask for a fresh response.
            "x-portkey-cache-force-refresh": "true",
        },
    )
    model = OpenAIResponsesModel(
        os.getenv("OPENAI_MODEL") or DEFAULT_MODEL,
        provider=OpenAIProvider(openai_client=client),
    )
    return client, model


async def run_agent(
    message: str,
    history: list[ChatMessage] | None = None,
    page: PageContext | None = None,
    customer: CustomerProfile | None = None,
) -> ChatResponse:
    state = ShopState(customer=customer, page=page or PageContext(), shopper_message=message)
    started = time.perf_counter()
    client, model = _client_and_model()
    async with client:
        result = await agent.run(
            message,
            model=model,
            deps=state,
            message_history=_history(history or []),
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS),
        )
    out = result.output
    _log_usage(state, result.usage, time.perf_counter() - started, out)
    # Cards come from the database, not the model, so prices and stock are always current.
    cards = tools.get_products(out.product_ids)[:MAX_CARDS]
    return ChatResponse(
        reply=out.reply,
        products=cards,
        page_results=_page_results(out, state, message),
        suggestions=[s.strip() for s in out.suggested_replies if s.strip()][:3],
        tools_used=state.tools_used,
    )


def _log_usage(state: ShopState, usage, seconds: float, out: ShopReply) -> None:
    """One JSON line per chat turn: speed, model requests, tokens and tools. No message text (privacy)."""
    USAGE_LOG.parent.mkdir(exist_ok=True)
    record = {
        "run_id": uuid.uuid4().hex[:8],
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "customer": "logged_in" if state.customer else "guest",
        "page": "product" if state.page.product_id else state.page.path,
        "seconds": round(seconds, 2),
        "model_requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "tools": state.tools_used,
        "price_corrections": state.price_corrections,
        "show_on_page": out.show_on_page,
    }
    with USAGE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _page_results(out: ShopReply, state: ShopState, message: str) -> PageResults | None:
    """Re-run the agent's last successful search with no result cap, for the website to show on the page."""
    if not out.show_on_page:
        return None
    last = next((f for f, total in reversed(state.searches) if total > 0), None)
    if last is None:
        return None
    products = tools.search_all(last)
    return PageResults(
        title=out.page_title or "Matches from your chat",
        shopper_message=message,
        filters=last,
        total_matches=len(products),
        products=products,
    )


if __name__ == "__main__":
    import asyncio
    import sys

    question = " ".join(sys.argv[1:]) or "Do you have navy hoodies under $70?"
    response = asyncio.run(run_agent(question))
    print(response.reply)
    print("cards:", [p.name for p in response.products], "| tools:", response.tools_used)
