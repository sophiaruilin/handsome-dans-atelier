"""Pydantic / PydanticAI types for the Campus Customs back end: products, accounts and chat."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field

import auth

StockStatus = Literal["in_stock", "selling_fast", "sold_out"]

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_MESSAGES = 20  # only the most recent turns go to the model
MAX_CARDS = 6              # product cards shown under one chat reply


# --- Products ------------------------------------------------------------------------------

class SizeStock(BaseModel):
    size: str
    quantity: int
    status: StockStatus


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    total_stock: int
    stock_status: StockStatus
    inventory: list[SizeStock]


# --- Agent tool results ----------------------------------------------------------------------
# What the agent's tools return. Every number here comes straight from campus_customs.db, so the
# agent can quote prices and stock instead of guessing them.

class SizeAvailability(BaseModel):
    size: str
    quantity: int = Field(description="Units left in this size, from the inventory table")
    status: StockStatus
    in_stock: bool


class ProductInfo(BaseModel):
    """get_product_info: everything a shopper might ask about one product."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float = Field(description="Price in US dollars, from the catalogue table")
    colors: list[str]
    stock_status: StockStatus = Field(description="Overall status across all sizes")
    total_stock: int
    sizes: list[SizeAvailability]
    sizes_in_stock: list[str]
    sizes_sold_out: list[str]


class StockCheck(BaseModel):
    """check_stock: availability of one size of one product."""

    product_id: str
    name: str
    size_asked: str = Field(description="The size as the shopper wrote it")
    size: str | None = Field(description="Matching shop size (XS-XXL), or null if we don't carry that size")
    carried: bool = Field(description="False if the shop doesn't make this product in that size")
    quantity: int
    status: StockStatus | None
    in_stock: bool
    other_sizes_in_stock: list[str] = Field(description="Sizes of the same product that are in stock")
    message: str = Field(description="Plain-English summary to base the answer on")


class ProductSummary(BaseModel):
    """One search hit: enough to pick products, not the full detail."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    stock_status: StockStatus
    sizes_in_stock: list[str]


class ProductSearchResult(BaseModel):
    total_matches: int
    showing: int
    products: list[ProductSummary]
    note: str = ""


class CatalogueOverview(BaseModel):
    product_count: int
    garment_types: dict[str, int]
    colors: list[str]
    sizes: list[str]
    price_min: float
    price_max: float


class WaitlistRequest(BaseModel):
    product_id: str
    size: str | None = None
    email: EmailStr


# --- Accounts ------------------------------------------------------------------------------

class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: EmailStr
    password: str = Field(max_length=auth.PASSWORD_MAX)
    confirm_password: str = Field(max_length=auth.PASSWORD_MAX)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(max_length=auth.PASSWORD_MAX)


class User(BaseModel):
    id: int
    first_name: str
    last_name: str
    name: str
    email: str


# --- Chat ----------------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    # Assistant replies can run long; user turns are capped by MAX_MESSAGE_CHARS on the way in.
    content: str = Field(max_length=8000)
    products: list[Product] = Field(default_factory=list)


class PageContext(BaseModel):
    """Where the shopper is on the website. Ids only: the server looks up the facts itself."""

    path: str = Field(default="/", max_length=200, description="Website path, e.g. /products/basic-hoodie-big-yale")
    product_id: str | None = Field(default=None, max_length=200, description="Product page being viewed, if any")
    results_title: str | None = Field(
        default=None, max_length=200, description="Heading of chat search results showing on the page, if any"
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Used for guests only. For logged-in shoppers the server loads history from the database.
    history: list[ChatMessage] = Field(default_factory=list, max_length=100)
    page: PageContext = Field(default_factory=PageContext)


class CustomerProfile(BaseModel):
    """Who is chatting (logged-in shoppers only). Lives in the agent's deps."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    member_since: str = Field(description="Date the account was created, YYYY-MM-DD")


class MyAccount(BaseModel):
    """get_my_account tool result: the logged-in shopper's own details."""

    first_name: str
    last_name: str
    email: str
    member_since: str
    saved_messages: int = Field(description="Messages in their saved chat history")
    waitlist: list[str] = Field(description="Products (and sizes) they asked to be emailed about")


class ShopReply(BaseModel):
    """The agent's structured answer (PydanticAI output_type)."""

    reply: str = Field(description="The message to the shopper, in Markdown. Friendly, short and accurate.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id of each product the reply recommends or discusses, best match first, "
            f"at most {MAX_CARDS}. Only ids returned by the tools. Empty if no product is relevant."
        ),
    )
    show_on_page: bool = Field(
        default=False,
        description=(
            "True when the shopper is browsing a kind of item (e.g. 'what hoodies do you have?', 'navy gifts "
            "under $60') and you ran search_products for it: the website then shows every match of your last "
            "search as product cards on the page. False for questions about one specific product, stock/price "
            "checks, or anything that isn't a product search."
        ),
    )
    page_title: str = Field(
        default="",
        description="Short heading for the on-page results when show_on_page is true, e.g. 'Navy hoodies under $70'.",
    )
    suggested_replies: list[str] = Field(
        default_factory=list,
        description=(
            "2-3 short follow-up messages the shopper might send next, written as the shopper "
            "(e.g. 'Show me similar styles', 'Is M in stock?'). Max 6 words each. Shown as tap-to-send buttons."
        ),
    )


class SearchFilters(BaseModel):
    """The search_products arguments the agent used, so the page can show exactly that search."""

    query: str = ""
    garment_type: str = ""
    color: str = ""
    max_price: float | None = None
    size: str = ""
    in_stock_only: bool = False


class PageResults(BaseModel):
    """Search matches for the website to render as product cards on the page (Problem 7)."""

    title: str
    shopper_message: str = Field(description="What the shopper asked, shown under the heading")
    filters: SearchFilters
    total_matches: int
    products: list[Product]  # every match, full records from the database


class ChatResponse(BaseModel):
    reply: str
    products: list[Product] = Field(default_factory=list)  # small cards under the reply in the chat
    page_results: PageResults | None = None  # when set, the website shows these as cards on the page
    suggestions: list[str] = Field(default_factory=list)  # quick-reply buttons under the reply
    redacted_message: str | None = None  # the shopper's message with card numbers masked, if any were found
    tools_used: list[str] = Field(default_factory=list)
