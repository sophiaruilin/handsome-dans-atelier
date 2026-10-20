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


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[ChatMessage] = Field(default_factory=list, max_length=100)
    product_id: str | None = None  # the product page the shopper is viewing, if any


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


class ChatResponse(BaseModel):
    reply: str
    products: list[Product] = Field(default_factory=list)  # shown as cards under the reply
    tools_used: list[str] = Field(default_factory=list)
