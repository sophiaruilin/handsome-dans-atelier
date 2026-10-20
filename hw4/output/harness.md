# HW 4 — Harness notes

## Problem 2 — Analyze the database

The shop database is `data/campus_customs.db` (SQLite). It has four tables: `catalogue`, `inventory`, `users` and `chat_messages`. SQLite also creates an internal `sqlite_sequence` table to track auto-increment IDs. It holds no shop data, so it is left out below.

### `catalogue` — 102 rows, one per product

Important to show the whole library or universe of options and choices.

| Field | Type | Why it matters |
|---|---|---|
| `product_id` | TEXT, primary key | Unique key that links each product to its stock and to the products the chatbot shows. |
| `name` | TEXT | The name the chatbot uses when it recommends a product. |
| `garment_type` | TEXT | Lets shoppers filter by type, such as "show me hoodies". |
| `description` | TEXT | Gives the chatbot detail to answer questions about style and design. |
| `colors` | TEXT (JSON list) | Answers color questions such as "do you have it in navy?" |
| `search_tags` | TEXT (JSON list) | Matches loose requests such as "hockey gift" to the right products. |
| `image_file_path` | TEXT | Shows the product photo next to the chat. |
| `price` | REAL | Answers price questions and supports budget filters. |

### `inventory` — 612 rows, one per product and size

Important to know how many are left of each product, or whether it is out of stock.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Unique row key. |
| `product_id` | TEXT, foreign key → `catalogue` | Links each stock count back to its product. |
| `size` | TEXT | Shoppers buy by size, from XS to XXL. Each product and size pair appears only once. |
| `quantity` | INTEGER | Shows whether a size is in stock or sold out, so the chatbot does not recommend sold-out sizes. |

### `users` — 3 rows, one per account

Important to know who the customers are. Right now the table holds account details only, not customer types.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Links each user to their chat history. |
| `name` | TEXT | The user's full name, for display. |
| `first_name` | TEXT | Lets the chatbot greet the user personally. |
| `last_name` | TEXT | Completes the user's name for account records. |
| `email` | TEXT, unique | The login ID. Being unique stops duplicate accounts. |
| `password_hash` | TEXT | Supports secure login. Only a salted hash is stored, never the password itself. |
| `created_at` | TEXT (date and time) | Shows when a user signed up, which separates new customers from returning ones. |

### `chat_messages` — 22 rows, one per message

Important for the chatbot to remember each conversation and what it already showed.

| Field | Type | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key | Unique message key that also keeps messages in order. |
| `user_id` | INTEGER, foreign key → `users` | Ties each message to the user's own conversation. |
| `role` | TEXT (`user` or `assistant`) | Tells the shopper's messages apart from the chatbot's replies. |
| `content` | TEXT | The message text. Lets the chatbot follow up on context such as "do you have this in pink?" |
| `products_json` | TEXT (JSON, optional) | The products the chatbot showed, including price and stock at that moment. |
| `created_at` | TEXT (date and time) | Puts the conversation in time order and shows when customers are active. |

### How the tables connect

- `inventory.product_id` → `catalogue.product_id`: stock for each product and size.
- `chat_messages.user_id` → `users.id`: each user's conversation history.

### Fields worth adding later

- `catalogue.category` (such as sport, residential college or school) and `catalogue.is_active`, for better filtering.
- `users.customer_type` (such as student, alum or parent), so the chatbot can tailor recommendations to each audience.
- An `orders` table, since the database has no record of purchases yet.

## Problem 3 — Build the Campus Customs website

### How it fits together

- **Front end:** `frontend/`, built with React, Vite and TypeScript, plus `react-router-dom` for pages. The Vite dev server forwards `/api` and `/media` requests to the back end, so the browser only talks to one address.
- **Back end:** `backend/main.py`, built with FastAPI. It opens `data/campus_customs.db` **read-only** and serves the products, stock by size and product images. Waitlist sign-ups go to a separate `backend/waitlist.db`, so the shop database is never changed.

| Route | What it does |
|---|---|
| `GET /api/products` | All 102 products, each with colors, tags, price, stock for every size, total stock and a stock status |
| `GET /api/products/{product_id}` | One product, used by the single-item page |
| `GET /media/products/{file}.jpg` | Product photos, using the `image_file_path` from `catalogue` |
| `POST /api/waitlist` | Saves a shopper's email for a sold-out product or size |
| `POST /api/chat` | A stub that returns a placeholder reply. Problem 5 replaces it with the shop agent |

### Pages

- **Nav bar:** Home, Products, About Us, Log in, Create account.
- **Home and About Us:** the text from `output/site_copy.md`, written for students and their families around pride, belonging and connection, with the store address.
- **Products:** a grid of cards with the photo, garment type, name, a one-sentence description, price, stock badge and color swatches, plus type filters and search. Clicking a card opens the product's own page.
- **Single-item page:** a large photo on the left. On the right: full description, price, colors, a button for each size showing how many are left (greyed out when sold out), and search tags.
- **Log in and Create account:** forms only for now. The sign-up fields match the `users` table.

### Stock rules

| Status | Per size | Per style (all sizes together) | What the shopper sees |
|---|---|---|---|
| In stock | 6 or more | 26 or more | Green "In stock" |
| Selling fast | 1–5 | 1–25 | 🔥 "Selling fast!" in red |
| Sold out | 0 | 0 | Grey, crossed-out size button, plus an email field and **Add to waitlist** button |

Sold-out styles show the waitlist form right on their product card. On the single-item page, choosing a sold-out size shows the waitlist form for that size.

### Chat

A floating panel in the bottom-right corner, on every page. I chose a floating panel over a separate chat page because shoppers can ask about the item they're looking at without leaving it. The panel sends the current product's id along with the message, so the Problem 5 agent can answer "does this come in pink?" The panel already calls `POST /api/chat`, so connecting the agent needs no front-end changes.

### Run it

```
cd backend && .venv/Scripts/uvicorn main:app --port 8000
cd frontend && npm run dev
```
