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

import os
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
    SearchFilters,
    ShopReply,
    StockCheck,
)

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
DEFAULT_MODEL = "gpt-6-astra"
MAX_REQUESTS = 8  # model calls per chat turn (bounds cost if the agent loops on tools)

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


agent = Agent(deps_type=ShopState, output_type=ShopReply)


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
        lines += [
            f"They are on the product page for **{p.name}** (product_id `{p.product_id}`): {p.garment_type}, "
            f"${p.price:.2f}, colors: {', '.join(p.colors)}.",
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
    return result


@agent.tool
def get_product_info(ctx: RunContext[ShopState], product_id: str) -> ProductInfo:
    """Full description, price, colors and units in stock for every size of one product.

    Use for "tell me about", "how much is" and "which sizes do you have" questions.
    """
    ctx.deps.tools_used.append("get_product_info")
    return tools.product_info(_lookup(product_id))


@agent.tool
def check_stock(ctx: RunContext[ShopState], product_id: str, size: str) -> StockCheck:
    """Is one size of one product in stock, and how many are left?

    Args:
        product_id: from search results or the page context.
        size: the size the shopper asked about, as they wrote it, e.g. "L", "large" or "2XL".
    """
    ctx.deps.tools_used.append("check_stock")
    return tools.stock_check(_lookup(product_id), size)


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
    state = ShopState(customer=customer, page=page or PageContext())
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
    # Cards come from the database, not the model, so prices and stock are always current.
    cards = tools.get_products(out.product_ids)[:MAX_CARDS]
    return ChatResponse(
        reply=out.reply,
        products=cards,
        page_results=_page_results(out, state, message),
        tools_used=state.tools_used,
    )


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
