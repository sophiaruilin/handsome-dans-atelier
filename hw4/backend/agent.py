"""PydanticAI Campus Customs shop agent, called by the /api/chat route in main.py.

run_agent(message, history, product_id, user) -> ChatResponse with the reply, the product
cards to show under it, and which tools ran.

- Instructions: prompts/prompt.md, plus a short per-request context (the product page the
  shopper is on, and their first name if logged in).
- Model: gpt-6-astra via Portkey (PORTKEY_API_KEY in .env), through the OpenAI Responses API.
  Override with OPENAI_MODEL=...
- Tools: thin wrappers over tools.py, which reads the shop database read-only.

Try it without the website:  python agent.py "Do you have navy hoodies under $70?"
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import MAX_CARDS, MAX_HISTORY_MESSAGES, ChatMessage, ChatResponse, ShopReply, User

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


agent = Agent(
    deps_type=ShopState,
    output_type=ShopReply,
    instructions=PROMPT_PATH.read_text(encoding="utf-8"),
)


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


@agent.tool
def search_products(
    ctx: RunContext[ShopState],
    query: str = "",
    garment_type: str = "",
    color: str = "",
    max_price: float | None = None,
    size: str = "",
    in_stock_only: bool = False,
) -> dict:
    """Search the Campus Customs catalogue. Every filter is optional; combine only what the shopper asked for.

    Args:
        query: keywords that must all appear in the name, description, colors or tags, e.g. "hockey" or "Saybrook".
        garment_type: e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: e.g. "navy", "gray", "white".
        max_price: highest price in US dollars.
        size: only products with this size in stock: XS, S, M, L, XL or XXL.
        in_stock_only: skip styles that are sold out in every size.
    """
    ctx.deps.tools_used.append("search_products")
    total, found = tools.search_products(query, garment_type, color, max_price, size, in_stock_only)
    return {"total_matches": total, "showing": len(found), "products": [tools.for_agent(p) for p in found]}


@agent.tool
def get_product(ctx: RunContext[ShopState], product_id: str) -> dict:
    """Full details and stock by size for one product_id (from search results or the page context)."""
    ctx.deps.tools_used.append("get_product")
    p = tools.get_product(product_id)
    return tools.for_agent(p) if p else {"error": f"No product with id {product_id!r}. Search first."}


@agent.tool
def catalogue_overview(ctx: RunContext[ShopState]) -> dict:
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
        default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"},
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
    # Cards come from the database, not the model, so prices and stock are always current.
    cards = tools.get_products(result.output.product_ids)[:MAX_CARDS]
    return ChatResponse(reply=result.output.reply, products=cards, tools_used=state.tools_used)


if __name__ == "__main__":
    import asyncio
    import sys

    question = " ".join(sys.argv[1:]) or "Do you have navy hoodies under $70?"
    response = asyncio.run(run_agent(question))
    print(response.reply)
    print("cards:", [p.name for p in response.products], "| tools:", response.tools_used)
