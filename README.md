# AURORA X

One search. Every store. The right deal.

A responsive React + TypeScript marketplace prototype for independent sellers and curious buyers. It runs locally with a curated demo catalogue; it is not connected to a production marketplace backend.

## Run locally

Requirements: Node.js 20.19+ or 22.12+, npm.

```powershell
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). To create a production build, run `npm run build`; to serve that build locally, run `npm run preview`.

## What works

- Marketplace home, category directory, catalogue search, category filtering, price/rating sorting, and natural-language budget/spec matching against the local catalogue.
- Product detail dialog with specifications, seller profile, delivery and related products.
- Cart quantity/removal, totals, savings, local demo checkout, order confirmation and order history.
- Wishlist, product comparison (up to three products), recently viewed products and responsive quick navigation.
- Seller demo sign-in/out, catalogue add/edit/delete, local inventory, sales overview and seller messages entry point.
- Store creator with brand personality and colour choices, live preview, local publishing and a separate storefront page.
- Shopping assistant, seller copy helper and TrustShield indicators clearly marked as demo/simulated.
- Buyer/seller messaging, translation preview, suggested replies and an editable human-support dispatch queue.
- Buyer display name and relevant demo state persist in browser `localStorage`.

## Demo boundaries

Search ranks only the products in `src/data/products.ts`. The voice button fills a sample request; it does not use microphone speech recognition. AI assistant responses and seller copy use local demo logic, not an AI service. Translation is a labelled preview and is not connected to a translation provider. Seller scores, reviews, operational metrics, support tickets and dispatch timings are illustrative, not verified or live. Demo sign-in does not authenticate a real account. Store publication is local to this prototype and does not create a public site. Checkout records an order in browser storage only; it does not contact a seller, process payments, or collect payment credentials.

## Production integrations still needed

- API and database for users, seller/store profiles, product catalogue, inventory, orders, messaging and support cases.
- Authentication, authorization, seller onboarding/KYC, moderation and real trust/risk signals.
- Payment provider, seller payout/commission ledger, tax, refunds and order fulfillment integrations before real commerce.
- Search infrastructure and configured AI/translation providers for live discovery, assistant responses, seller tools and multilingual communication.
- Image storage/CDN and observability, security, privacy, accessibility and operational review.

## Project layout

```text
src/
  components/   shared product cards, product detail, site header
  data/         local demo product catalogue
  hooks/        browser-persisted state helper
  pages/        marketplace, assistant, commerce, seller and support views
  types.ts      shared domain types
  App.tsx       navigation and local demo state
  App.css       responsive component and page styles
  index.css     global typography and document styles
```

Demo data is stored in this browser under `aurora-*` localStorage keys. Clear the site's local storage to return to the initial demo state.

## Stage 2 backend

The production-oriented API is under `backend/`. It uses FastAPI, SQLAlchemy 2, Alembic, PostgreSQL and Argon2 password hashing. JWT tokens include a server-side user token version, and logout increments that version to invalidate existing tokens.

### Start PostgreSQL with Docker

```powershell
docker compose up -d postgres
copy backend\.env.example backend\.env
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m alembic upgrade head
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Docker is optional. For a local PostgreSQL installation, create a database and user, set `DATABASE_URL` in `backend/.env`, then run the Alembic and Uvicorn commands above.

### Run the API tests

```powershell
cd backend
pytest -q
```

Tests use isolated SQLite databases and run migration upgrade testing in a temporary database. PostgreSQL persistence is configured by `DATABASE_URL`; Docker's database credentials are development defaults only.

### Run the frontend

Create `.env` from `.env.example` if the API is not at `http://localhost:8000/api`. The frontend keeps its local catalogue when the API is unavailable or before it has loaded. When a live product response is received, live products replace the demo catalogue; cart and seller demo flows remain explicitly local until wired to authenticated backend mutations.

```powershell
npm install
npm run dev
npm run build
npm run lint
```

API documentation is available at `http://localhost:8000/docs` while the backend is running.

## Stage 3 commerce

The backend now includes persistent buyer carts, multi-seller checkout, parent orders, seller suborders, Decimal commission records, inventory movements, demo payment records, shipments and status history. Buyer, seller and admin ownership is enforced server-side.

Stage 3 uses SQLite for automated tests. PostgreSQL has been configured for application use but was unavailable for verification in this environment, so PostgreSQL compatibility remains unverified.

Commerce documentation:

- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- [docs/COMMERCE_FLOW.md](docs/COMMERCE_FLOW.md)

## Stage 4 AI and search

Stage 4 adds a deterministic local AI fallback, optional OpenAI-compatible provider abstraction, actual-catalogue semantic-style search, explainable product ranking, shopping copilot, comparisons, seller listing tools, category/purchase recommendations and explainable TrustShield signals.

No external AI provider is required. If no provider is configured, APIs remain available in clearly labelled deterministic local fallback mode.

AI documentation:

- [docs/AI_ARCHITECTURE.md](docs/AI_ARCHITECTURE.md)
- [docs/SEARCH_ENGINE.md](docs/SEARCH_ENGINE.md)
- [docs/AI_SAFETY.md](docs/AI_SAFETY.md)
- [docs/AI_PROVIDER_SETUP.md](docs/AI_PROVIDER_SETUP.md)

## Stage 5 communication and operations

Stage 5 adds persistent buyer-seller conversations, authenticated WebSockets, private attachments, notifications, support tickets, disputes, verification/moderation queues, explainable TrustShield alerts and audit logs.

Translation is provider-ready but unavailable unless `TRANSLATION_API_URL` and credentials are configured. Real-time chat works through WebSocket and REST history; PostgreSQL remains unverified in this environment.

Stage 5 documentation:

- [docs/STAGE5_IMPLEMENTATION.md](docs/STAGE5_IMPLEMENTATION.md)
- [docs/MESSAGING_ARCHITECTURE.md](docs/MESSAGING_ARCHITECTURE.md)
- [docs/TRANSLATION_ARCHITECTURE.md](docs/TRANSLATION_ARCHITECTURE.md)
- [docs/TRUSTSHIELD_V2.md](docs/TRUSTSHIELD_V2.md)
- [docs/SUPPORT_OPERATIONS.md](docs/SUPPORT_OPERATIONS.md)
- [docs/DISPUTE_WORKFLOW.md](docs/DISPUTE_WORKFLOW.md)
- [docs/ADMIN_SECURITY.md](docs/ADMIN_SECURITY.md)

## Stage 6–9 release status

Database-derived platform and seller analytics are available through `/api/admin/analytics`, `/api/seller/analytics` and `/api/admin/analytics/export`. Values are calculated from stored orders and records; missing history is reported as empty or unavailable rather than fabricated.

The account page includes buyer/seller registration, login and logout. Signed-in API operations replace browser-local state where a backend endpoint exists. The checkout address UI currently uses a default address until the address-entry form is connected; it must not be presented as collecting verified delivery data.

Private verification and dispute document downloads are intentionally disabled: no public or unauthorised private-document route is exposed.

PostgreSQL, external AI credentials, translation credentials and Docker availability remain deployment-time verification items. No real payment, payout or refund integration is claimed.