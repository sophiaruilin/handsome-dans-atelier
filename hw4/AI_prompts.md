# HW 4 — AI prompt log

This log records the AI-assisted work for every problem in HW 4. Each entry has the problem number and title, at least one prompt I wrote in my own words, and a follow-up prompt when one was needed, with one sentence on what the first response was missing.

<!--
Template for each problem (copy for each new problem):

## Problem N — Title

**Prompt (my own words):**

> ...

**Follow-up prompt:**

> ...

**What was lacking before:** One sentence.
-->

## Problem 1 — Vibe Coder Prompts

**Prompt (my own words):**

> create new folder hw4 - i am starting hw4 assignment

**Follow-up prompt:**

> same rules as our prior problems for homeworks, like problme number and name and instructions, etc. do you remember?

**What was lacking before:** The first response only set up the folder and did not apply the prompt-log conventions from earlier homeworks.

## Problem 2 — Analyze the Database

**Prompt (my own words):**

> Look at the database in the hw4 data folder data/campus_customs.db . start file output/harness.md and write down each table and its fields, and one short line on why each field matters for the shop or chatbot.
> catalogue - important to show whole library or universe of options and choices
> inventory - important to know how many quantities are left, or even if a product is out.
> users - important to know types of audiences or customers.
>
> before we commit this, i want you to 1) give me feedback on how strong these are and if there are any other relevant fields you would include, and 2) tell me which program to ideally open up this file to view the fields myself, if you recommend i open it to see the fields myself.

**Follow-up prompt:**

> Yes, write output/harness.md with all four tables and a line for every field, building on my notes.

**What was lacking before:** My first notes covered only three tables at a high level and missed `chat_messages` and the field-by-field reasons the assignment asks for.

## Problem 3 — Build the Campus Customs Website

**Prompt (my own words):**

> Create Problem 3: Build the Campus Customs Website.
> I need to do this next step. What do you need to scaffold this?
>
> *(screenshot: Scaffold a React + Vite + TypeScript front end for Campus Customs. Put a nav bar at the top that links to the main pages: Home, Products, About Us, Log in, Create account)*

**Follow-up prompt:**

> Before you execute the command, please incorporate  Campus Customs-style wording from yalebulldogblue.com for Home and About Us but write these pages in my own voice so give me a chance to work on the text.. give me the text and allow me chance to modify before you run the full command with this info.
>
> In addition, on the Products page that you create, show the product images from the catalogue (use the image paths in the database) with basic product info (at least including name, price, short description - let me know if any other basic product info you reocmmend including and why). make each product open a single-item page (large image on one side, full product text on the other - description, price, sizes/stock when you have them). clicking a card on products should take the shopper there.
>
> add a chat interface in the bottom right of the side, floating chat panel is fine - let me know if you recommend one way or another and why. it does not need to talk to an agent yet, a stub that will call my backend later is enough for this problem.
>
> I will need a small API soon to read the database. it is fine to start a simple fastAPI app in backend/main.py just to serve products and images then grow it into the agent backend in Problem 5.

**What was lacking before:** The first plan scaffolded only empty pages with a nav bar, without shop wording, product pages, a chat panel or a backend to read the database.

**Second follow-up prompt:**

> for the wording, you can edit the text to be fun, cool, fit for unviersity students, yet also intellectual given they're a bright group and their praents and loved ones invested in their sucess are also checking out the site for gear. appeal to emotions, fitting in, representing the school proudly, as poitn fo connection of peers int he community. include all factual information that would be uesful like the address. show me the sample text draft of this style of text for this home and about us section before confirming it.
>
> Include the extra porduct info for color and how in stock the style is. for low stock, include a flame and red font with text "selling fast!" and for sold out, add an email field and button to "add to waitlist" and be notified when back in stock.
>
> on eaah single-item page, that sounds good to me on the buttons with stock counts and greyed out when sold out; implement the chang eabove here on low stock and waitlist.
>
> chat: go ahead wit hthe floating panel.
>
> i'm ready - build everything!

**What was lacking before:** The first text draft was plain and factual, without the emotional pull of belonging and school pride, and the product pages had no low-stock or waitlist features.

**Third follow-up prompt:**

> Wow I love it! Move ahead with the text!

## Problem 4 — Create account and login

**Prompt (my own words):**

> Build a normal create-account / login flow.
>
> Create account: first name, last name, email, password (confirm password is a nice touch - they can write it again and make sure the passwords align, and also, that the password meets certain complexity best practices you recommend)
>
> Log in: email and password
>
> new accounts go into the users table. make sure to store passwords super securely so hackers, human or AI, cannot access them. tell me best practices for doing so and what you reocmmend and why.
>
> seed database already has test user you can use while building, see image.
>
> how login checks password:
> never un-hash the stored value. re-hash what user typed and comprae.
>
> read the salt out of stored string (middle piece) - do not make a new one at login.
> hash typed password with same salt, then compare to stored hash. use constant-time compare.
>
> signup and login must use same hash settings (same funciton, salt handling, iteraciton count) - if differ even right password will not match.
>
> surest check: log in as the seeded test user adn as a brand new acconut you just created in your own app.
>
> confirm you can log in as that user and that branmd new account you create also works.
>
> update output/harness.md with how auth works (what you store for a user and how passwords are protected)
>
> *(screenshot: test user test@campuscustoms.yale.edu / password; hash function PBKDF2-HMAC-SHA256, 120,000 iterations, stored as pbkdf2_sha256$salt$hash)*

**Follow-up prompt:**

> great!! may in confirm first, is it safe to have typed the actual hash function hree? how will you 'hide' it from records so it is safe and not accessed or used again by someone else, only if it is needed, and without revealing the hash? if that is best practice, that is.

**What was lacking before:** The first write-up explained how passwords are hashed but not which parts must stay secret (passwords, hashes, session tokens, keys) and which parts are safe to publish (the algorithm and its settings).

## Problem 5 — PydanticAI agent backend

**Prompt (my own words):**

> problem 5: pydanticAI agent backend
>
> build shop chatbot as a pydanticAI agent behind fastAPI plugged into front-end chat widget. put api app in backend/main.py the file i run with uvicorn. keep agent as these four file s next to it, same idea as hw3.
>
> do the above, as well as in main.py, expose a chat route so message from website returns with replay from agent, and whatever else you need for products/auth. you will need your ai model api key for the agent.
>
> put campus customs voice and safety basics into prompts/prompt.md (you will expand tools and safety later). start or update types in models.py for chat replies/product cards as needed.
>
> in output/harness.md, note how front end talks to fastapi and how agent is loaded (prompt file + model).
>
> make sure backend runs from backend/ folder like this
> uvicorn main:app --reload --port 8000
>
> *(screenshot: backend/prompts/prompt.md — system prompt (grow this same file later); backend/agent.py — agent entry / wiring; backend/tools.py — tools the agent can call; backend/models.py — Pydantic / PydanticAI structured types)*

## Problem 6 — Tools: Product info and stock

**Prompt (my own words):**

> Great! Problem 6: Tools: Produc tinfo and stock
>
> Give the agent tools that look up real info from campus_customs.db
> product description, price, how many are in stock by size when customer asks
>
> the agent must use the database - it should not invent prices or quantities. if size is out of stock, say so clearly.
>
> expand prompts/prompt.md so agent knows to call these tools for price and stock questions. add or update return types in models.py
>
> in output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

## Problem 7 — Chat search that updates the page

**Prompt (my own words):**

> Problem 7: chat search that updates the page
>
> now we will add a neat feature to the site. when customer asks about type of item, like what hoods do you have, the agent should search catalogue - and the website should dynamically show those matching items as product cards (image, name, price, short info). this is an API contract: agent returns structured product matches and then the front end renders them on te ewbsite, it looks really cool.
>
> after the dynamic product cards are loaded by new feature, make sure same single-item page behavior you built in problem 3 still works: each product card - including ones the chat just put on the page - should still open the detail view (larg eimage + full info) when clicked. update prompts/prompt.md and output/harness.md so it is clear how search results reach the page.

## Problem 8 — Customer memory

**Prompt (my own words):**

> Problem 8: Customer memory
>
> WHen a shopper is logged in, save their chat hitsory in database in apropratie table and reload when they return. agent should know WHO is chatting (name, email) - put that in agent deps (or an equivalent clear pattern, whatever you recommend) and/or tools that the agent can call.
>
> Also pass enough page context that if someone is on a product page and asks do you have this in pink, etc. the agent knows which item they mean. (hint you can put code into the agent context - what do you recommend / best practices for tthis to achieve?)
>
> guests can still chat, but history only needs to persist for logged-in users. document in output/harness.md: how user chat history is stored, what customer fields the agent sees, and how page context is passed.
