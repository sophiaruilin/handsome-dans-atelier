# Handsome Dan's Atelier: Campus Customs (HW 4)

**Campus Customs**, home of *Yale Bulldog Blue*, is a web shop for officially licensed Yale apparel, with an AI shopping assistant called **Handsome Dan**.

- **Front end:** React + Vite + TypeScript. It has a product catalogue with school, fit, color and size filters, product pages, saved items, a bag, and a "reserve for pickup" checkout.
- **Back end:** FastAPI. It serves the catalogue, accounts, orders and the chat.
- **Shopping assistant:** a **PydanticAI agent** that answers from the shop database, never from memory: prices, stock by size, similar styles, waitlist and account questions.

> The product database and product photos (the **data pack**) are **not** in this repo. See [Place the data pack](#1-place-the-data-pack) below.

---

## File layout

```
hw4/
├── AI_prompts.md          # log of the prompts used for each problem
├── README.md              # this file
├── requirements.txt       # Python packages for the back end
├── .env.example           # copy to .env and add your key (placeholders only)
├── .gitignore             # keeps .env, data/, .venv/, node_modules/ out of git
├── frontend/              # Vite React TypeScript app
│   ├── src/               #   pages, components, chat widget, Handsome Dan (Dan.tsx)
│   ├── public/art/        #   Victorian engravings of Yale landmarks + toile wallpaper
│   └── scripts/build_art.py   # regenerates the engravings
├── backend/               # FastAPI app: run with  uvicorn main:app --reload --port 8000
│   ├── main.py            #   API routes (products, auth, chat, orders, waitlist)
│   ├── agent.py           #   the PydanticAI agent (instructions, 7 tools, fact-checker, audit)
│   ├── models.py          #   Pydantic / PydanticAI types
│   ├── tools.py           #   database reads used by the agent and the API
│   ├── prompts/
│   │   └── prompt.md      #   Handsome Dan's instructions and safety rules
│   ├── auth.py  orders.py  catalog_meta.py  audit.py   # supporting modules (see harness.md)
│   ├── tests/             #   40 pytest tests (no AI calls)
│   └── .env.example
├── output/
│   ├── harness.md         # how the whole system works: specs, tools, models, safety, audit
│   ├── design.md          # Problem 10 storefront design
│   ├── usability.md       # Problem 9 usability improvements
│   ├── app_check.html     # Problem 11 live-site check (double-click to open)
│   ├── app_check_images/  # screenshots linked from app_check.html
│   └── audit_trail.json   # append-only log of agent-loop activity
└── data/                  # NOT IN GIT: place the data pack here (see below)
    ├── campus_customs.db
    └── products/          # images referenced by the catalogue
```

**The agent itself is four files** under `backend/`: `prompts/prompt.md`, `agent.py`, `tools.py` and `models.py`. `main.py` is the FastAPI app that serves it. The remaining back-end files (`auth.py`, `orders.py`, `catalog_meta.py`, `audit.py`) support the website: logins, pickup orders, the school filters and the audit trail.

---

## How to run it

**You'll need:**

- **Python 3.12+**
- **Node.js 20+** (includes `npm`)
- a **Portkey API key** for the AI model
- the course **data pack**

### 1. Place the data pack

Put the course data pack inside `hw4/data/`, so the folder looks like this:

```
hw4/data/campus_customs.db
hw4/data/products/2025-yale-vs-harvard-t-shirt.jpg   (and the other product images)
```

The back end reads `data/campus_customs.db` and serves the images from `data/products/`.

### 2. Add your API key

From `hw4/`:

```bash
cp .env.example .env          # Windows PowerShell:  Copy-Item .env.example .env
```

Open `.env` and replace `your-portkey-api-key-here` with your Portkey key. `.env` is git-ignored.

### 3. Start the back end (FastAPI, port 8000)

From `hw4/`, create a virtual environment **in `hw4/.venv`** and install the packages. (Keep the environment outside `backend/`, so `--reload` doesn't restart in a loop when library files change.)

```bash
python -m venv .venv
```

Activate it:

- **Mac/Linux:** `source .venv/bin/activate`
- **Windows (Git Bash):** `source .venv/Scripts/activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`. If script running is blocked, skip activation and call `.venv\Scripts\python` and `.venv\Scripts\uvicorn` directly.

Then:

```bash
python -m pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it at http://127.0.0.1:8000/api/health (should say `"products": 102`). API docs are at http://127.0.0.1:8000/docs.

### 4. Start the front end (Vite, port 5173)

In a **second terminal**, from `hw4/frontend/`:

```bash
npm install
npm run dev
```

Open **http://localhost:5173**. Vite forwards `/api/...` and `/media/...` requests to the back end on port 8000, so start the back end first.

### 5. Try it

- **Chat with Handsome Dan** (bottom right). For example: *"What hoodies do you have?"*, *"Is the Saybrook College Crewneck in stock in L?"* or *"Gift ideas for my mom under $60"*.
- **Shop:** filter by **Affiliation** (residential college, graduate school, varsity team, family), **Fit**, **Color**, **Style** and **My size**.
- **Buy:** on a product page, pick a size → **Add to bag** (Dan jumps) → **Bag** → optional toile gift wrap → **Reserve for pickup** (Dan cartwheels, then a telegram receipt). There's no online payment: items are held for 3 days at 57 Broadway.
- **Test login:** `test@campuscustoms.yale.edu` / `password` (a seeded user in the data pack), or create your own account. Logged-in chats are saved and remembered.
- **Footer → "Dan's wardrobe":** preview Seasonal Dan (fall, winter, spring, summer, Game week).

---

## Tests and checks

From `hw4/backend/` with the virtual environment active (the data pack must be in place):

```bash
python -m pytest -q        # 40 passed: tool results vs SQL, filters, price fact-checker,
                           # card masking, waitlist, pickup orders, audit trail
```

From `hw4/frontend/`:

```bash
npm run build              # TypeScript type-check + production build
npm run lint               # oxlint
```

---

## Where to read more

| File | What's in it |
|---|---|
| [`output/harness.md`](output/harness.md) | **Start here.** Architecture, how to run it, specs (model, loop limits, result caps), the 7 agent tools, every field in `models.py` and why, safety rules, audit trail, and the build log for every problem |
| [`output/usability.md`](output/usability.md) | Problem 9: 4 front-end and 4 agent/back-end improvements, with evidence |
| [`output/design.md`](output/design.md) | Problem 10: the storefront design, Handsome Dan, Seasonal Dan, the telegram receipt |
| [`output/app_check.html`](output/app_check.html) | Problem 11: live-site checks with screenshots (download and double-click to open) |
| [`output/audit_trail.json`](output/audit_trail.json) | Problem 12: append-only log of agent-loop activity (time, tool, short args and results, stop reason) |
| [`backend/prompts/prompt.md`](backend/prompts/prompt.md) | Handsome Dan's instructions and safety rules |
| [`AI_prompts.md`](AI_prompts.md) | The prompts used for each problem |

**Model:** `gpt-6-astra` through the Portkey gateway (OpenAI Responses API). To use a different model, set `OPENAI_MODEL` in `.env`.
