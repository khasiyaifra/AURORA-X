# AURORA X Architecture Audit

**Audit date:** 2026-11-17  
**Scope:** Read-only review of the current React/Vite prototype and its baseline build/lint checks. No application behavior was changed as part of this audit.

## Executive Summary

AURORA X is a working, client-only marketplace prototype. It demonstrates buyer discovery and checkout, seller product/store flows, and support/chat surfaces using a local catalogue and browser storage. The existing README accurately discloses that these are demos, not production integrations.

The current structure is suitable for continued prototyping, but not for real multi-user commerce. `App.tsx` owns routing-like page state, catalogue/search logic, cart/order operations and data wiring. Pages own large collections of presentation and workflow state. There is no API/service layer, database, authentication, payment processing, test suite, or server-side trust boundary.

## Existing Functionality

- Marketplace home with product sections for featured, trending, discounted and high-review-count items; recently viewed items appear after opening product details.
- Eight category views and a local product catalogue containing 12 seed products across 10 demo seller IDs.
- Local search across product names, categories, seller names, descriptions and specification text. Search supports basic synonyms, price limits including `k` shorthand, a simple token-match score, and relevance/price/rating sorting.
- Product detail dialog with specifications, sample seller and rating data, delivery and related products.
- Cart add/remove/quantity controls, stock-capped quantity changes, totals and savings, browser-local checkout confirmation and order history.
- Wishlist and product comparison, with a three-product comparison limit. Recently viewed IDs, cart, wishlist, products, one store, buyer display name and buyer order history persist in `localStorage`.
- Seller demo session toggle; local product create/edit/delete and inventory editing; illustrative revenue and sales stats; simulated recent orders with editable statuses.
- Store creator with category, description, brand personality and colour choices; preview and browser-local publishing to a storefront view.
- Shopping-assistant prompt examples and local catalogue recommendations; seller copy, pricing and campaign suggestions use local template/calculation logic.
- Buyer/seller conversation with locally persisted messages and a labelled translation preview; locally persisted support tickets with editable priority/status.
- Responsive layouts, mobile quick navigation, product actions, and a product detail dialog.

All catalogue ratings, reviews, seller signals, fulfilment metrics, sample orders and support queue entries are demo data. The voice controls insert sample text; there is no speech-recognition integration. Assistant and translation behavior is not connected to an external model or translation service.

## Structure and Data Flow

- `src/App.tsx` is the application coordinator. It holds page state, search and ranking logic, shared buyer state, checkout, notifications and product/store callbacks.
- `src/pages/` contains marketplace, commerce, assistant, seller and support views. Several files render multiple page modes through `Page` conditionals rather than distinct route components.
- `src/components/` contains the shared header and product card/detail dialog. The product grid and the card-handler wiring are repeated in the marketplace, assistant and wishlist views.
- `src/data/products.ts` is the in-memory seed catalogue. There is no repository/API service boundary yet.
- `src/hooks/usePersistentState.ts` reads JSON from and writes JSON to `window.localStorage`. It catches storage and parse errors, but performs no schema validation or migration.
- `src/types.ts` contains the shared product, store, cart and page types.
- `src/App.css` holds most application styling; `ProductCard.css` and `SellerPage.css` add small component/page-specific rules. `src/index.css` imports fonts from Google Fonts.

## Baseline Checks

- `npm run build`: passed. TypeScript project build and Vite production build completed successfully (Vite 8.3.8).
- `npm run lint`: passed with no Oxlint diagnostics.
- Automated test coverage: no test/spec files were found, and `package.json` has no test script. Previous manual browser checks are not a repeatable test suite.

## Findings

### High: Browser state is not a production trust boundary

Products, seller data, cart quantities, buyer orders, messages, support tickets and the seller demo-session flag are stored or managed in one browser. The seller session is a local boolean, not authentication. Any values in browser storage can be inspected or edited by the user. No order, seller identity, inventory, price, rating, or trust decision may be accepted as authoritative by a future backend based on these client values.

Relevant files: [src/hooks/usePersistentState.ts](../src/hooks/usePersistentState.ts), [src/App.tsx](../src/App.tsx), [src/pages/SellerPage.tsx](../src/pages/SellerPage.tsx), [src/pages/SupportPage.tsx](../src/pages/SupportPage.tsx).

### High: No real commerce or multi-tenant backend exists

Checkout records a local buyer order, clears the local cart and displays a confirmation. It does not reserve/decrement inventory, create a seller order, notify a seller, process a payment, or calculate/settle the proposed 3% commission. Seller revenue is an illustrative inventory estimate; seller orders and metrics are seeded demo values. The one `aurora-store` key represents one editable store in this browser, not independently authenticated seller accounts.

Relevant files: [src/App.tsx](../src/App.tsx), [src/pages/CommercePage.tsx](../src/pages/CommercePage.tsx), [src/pages/SellerPage.tsx](../src/pages/SellerPage.tsx).

### Medium: Product deletion can leave dangling commerce references

Deleting a product filters it out of `products`, but does not remove its ID from `cart`, `wishlist` or `recentlyViewed`. Cart display filters missing products while the header cart count is derived from all cart lines, so these views can disagree after deletion. Stale wishlist/recent IDs also remain in storage. Cart add should also reject an unavailable item when its stock is zero; current add logic can create a quantity-one line for such an item.

Relevant code: [src/App.tsx](../src/App.tsx#L78), [src/App.tsx](../src/App.tsx#L108), [src/App.tsx](../src/App.tsx#L136), [src/pages/CommercePage.tsx](../src/pages/CommercePage.tsx).

### Medium: Navigation is state-only

The `Page` value selects content in `App.tsx`, but is not reflected in the URL or browser history. Reloading returns to Home, and views cannot be deep-linked or shared. Compare selections, search text, sort and category are also in-memory only. Persistent commerce data survives refresh as documented, but transient navigation state does not.

Relevant code: [src/App.tsx](../src/App.tsx#L26), [src/App.tsx](../src/App.tsx#L74), [src/types.ts](../src/types.ts).

### Medium: Search is a local heuristic, not semantic discovery

The current ranking tokenizes user text, removes a fixed stop-word list, applies a small synonym map, checks substring matches against local product fields and applies a fixed hit threshold. It does not provide robust specification parsing, true semantic relevance, external-store crawling, result provenance, or per-product explanation evidence. This is appropriate for the disclosed demo catalogue but should be isolated behind a search interface before adding a real index or AI service.

Relevant code: [src/App.tsx](../src/App.tsx#L18), [src/App.tsx](../src/App.tsx#L19), [src/App.tsx](../src/App.tsx#L44), [src/App.tsx](../src/App.tsx#L46).

### Low: Some support controls are inert

The “More chat options” and “Support info” controls render as buttons without click handlers. They look actionable but currently do nothing. Most other primary navigation and commerce controls are wired to local demo actions.

Relevant code: [src/pages/SupportPage.tsx](../src/pages/SupportPage.tsx#L37), [src/pages/SupportPage.tsx](../src/pages/SupportPage.tsx#L38).

### Low: UI responsibilities and product-grid wiring are duplicated

`MarketplacePage.tsx`, `CommercePage.tsx` and `AssistantPage.tsx` each repeat product-card rendering and handler wiring. `SellerPage.tsx` combines dashboard, creator, storefront, inventory editor, order desk and seller assistant behavior. These are understandable at prototype scale, but adding more workflows here will make changes harder to isolate and verify.

Relevant files: [src/pages/MarketplacePage.tsx](../src/pages/MarketplacePage.tsx), [src/pages/CommercePage.tsx](../src/pages/CommercePage.tsx), [src/pages/AssistantPage.tsx](../src/pages/AssistantPage.tsx), [src/pages/SellerPage.tsx](../src/pages/SellerPage.tsx).

### Low: Browser persistence has no schema/version contract

The persistence hook catches invalid JSON and unavailable storage, then falls back to initial state. It does not validate parsed shapes, version keys, migrate old data or synchronize changes across tabs. A parseable but structurally invalid value can still break downstream rendering. This matters more as persisted models evolve.

Relevant file: [src/hooks/usePersistentState.ts](../src/hooks/usePersistentState.ts).

### Low: Dialog accessibility is incomplete

The product details surface uses `role="dialog"` and has a close button, but does not currently implement focus placement/trapping, Escape-to-close or focus restoration. Automated accessibility checks are not configured.

Relevant file: [src/components/ProductCard.tsx](../src/components/ProductCard.tsx).

## Security and Production Boundary

This audit is a code/architecture review, not a penetration test. The app has no server endpoints or credential/payment flow to assess. React renders normal product/user text as text, but future integrations still need server-side validation and authorization, secure session handling, rate limits, privacy/data-retention controls, CSP/security headers, image upload validation, audit logging and threat modeling. Do not treat demo seller scores or browser-local state as fraud or identity verification.

## Next Evolution Gate

The supplied V2 request ends immediately after asking the audit to record “Existing functionality.” This document covers that visible audit request and the associated repository review. The remaining V2 requirements and acceptance criteria were not present, so no additional product architecture or behavior changes were inferred or applied. A production evolution should first define backend/API ownership, identity and tenancy, order/inventory state transitions, payment and commission rules, AI provider boundaries, security requirements and measurable acceptance tests.