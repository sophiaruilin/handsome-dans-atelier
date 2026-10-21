"""PydanticAI Campus Customs shop agent, called by the /api/chat route in main.py.

run_agent(message, history, product_id, user) -> ChatResponse with the reply, the product
cards to show under it, on-page search results (when the shopper is browsing), and which tools ran.

- Instructions: prompts/prompt.md (re-read each message), plus a short per-request context (the product page the
  shopper is on, and their first name if logged in).
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
    PageResults,
    ProductInfo,
    ProductSearchResult,
    SearchFilters,
    ShopReply,
    StockCheck,
    User,
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
    product_id: str | None = None  # product page the shopper is viewing
    first_name: str | None = None  # set when logged in
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
def page_context(ctx: RunContext[ShopState]) -> str:
    lines = ["## Context for this message"]
    if ctx.deps.product_id and (p := tools.get_product(ctx.deps.product_id)):
        lines.append(f"The shopper is viewing **{p.name}** (product_id `{p.product_id}`).")
    else:
        lines.append("The shopper is not on a product page.")
    if ctx.deps.first_name:
        lines.append(f"The shopper is logged in as {ctx.deps.first_name}. You may greet them by first name.")
    else:
        lines.append("The shopper is browsing as a guest.")
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
def catalogue_overview(ctx: RunContext[ShopState]) -> CatalogueOverview:
    """Garment types (with counts), colors, sizes and price range the shop carries."""
    ctx.deps.tools_used.append("catalogue_overview")
    return tools.catalogue_overview()


def _history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Website chat log -> PydanticAI message history (most recent turns only)."""
    out: list[ModelMessage] = []
    for m in messages[-MAX_HISTORY_MESSAGES:]:
        if m.role == "user":
            out.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            out.append(ModelResponse(parts=[TextPart(content=m.content)]))
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
    product_id: str | None = None,
    user: User | None = None,
) -> ChatResponse:
    state = ShopState(product_id=product_id, first_name=user.first_name if user else None)
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
