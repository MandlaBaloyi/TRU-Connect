# TruConnect

**Business tools for South Africa's informal economy, with the suppliers they already buy from.**

TruConnect is part of the wider TruePoint platform. It is an **ecosystem, not a marketplace**. The business tools are the product. Suppliers are something a business can add, never something it needs first.

---

## Who it is for

Anyone who trades without a formal storefront: spaza shops, kota and food vendors, salons and barbers, street and market traders, tuck shops, home-based sellers, students reselling to other students.

Spaza shops are the biggest and best-documented group. There are more than 150,000 of them, carrying 30–40% of the country's food spending, and only about 1% accept electronic payment. Most keep no stock records. That missing record is the problem TruConnect starts from.

## The principle: tools stand alone

A business that only ever uses the Order Book, and never buys a thing through TruConnect, is a complete user. It is not half a user or a funnel stage.

- No tool needs a supplier connection to work.
- No tool is locked until the business places an order.
- Onboarding does not assume the business wants to buy stock from us.
- A business gets full value on day one with **zero** suppliers on the platform.

This is why TruConnect onboards businesses first. A business needs only something better than a paper notebook. A supplier needs capital, a move off systems that already work, and trust we have not earned yet. The businesses using the app are the asset, and suppliers come later to reach them.

## What a business gets

| Tool | What it replaces |
|---|---|
| **Order Book** | The paper book where customer orders get written down |
| **Loan Book** | The month-end credit tab: who owes what, and when it was paid |
| **Community tab** | A feed built from the shop's own trading: stock to reorder, what is moving fast, suppliers near enough to collect from, and suppliers who sell what the shop actually buys |
| **Category browse** | Stock across every verified supplier, narrowed by search, supplier type and "my suppliers" |
| **Stock ordering** | Ordering from connected suppliers, with a real record of every order |

## What a supplier gets

- A shopfront and product catalogue, with bulk import
- Inventory and minimum-order controls
- Incoming connection requests and stock-order management
- A web portal (`frontend/web`) as well as the mobile app

## Trust is built in

- **The verification curtain.** Buyers cannot see or order from an unverified supplier. The rule lives in one file, and architecture tests enforce it.
- **Recourse.** A digital order carries an invoice, an amount and a date. A shop that pays and gets nothing has proof, and the platform has grounds to suspend that supplier.
- **Honest ranking.** What a shop buys always outranks what a supplier pays for. A paid plan can only break ties between suppliers who are already equally relevant. It never buys a place above a better match.
- **Cash is allowed on purpose.** Businesses start where they are. Nobody carries R10,000 in cash, so larger orders move to digital payment naturally.

## The long view

Informal businesses are often shut out of finance because nobody has records of how they trade, not because they trade badly. Every order placed and paid through TruConnect adds to a verifiable trading history that informal businesses have never had.

We treat that history as a result of building useful tools well. We do not build features only to collect it. Every feature has to solve a real problem for the people using it today.

---

## Repository

```
backend/            Flask + PostgreSQL API (domain-driven, multi-schema)
frontend/mobile/    Expo / React Native app (Expo Router, TypeScript)
frontend/web/       Next.js supplier portal
docs/               Product and architecture specs (v2/ holds current thinking)
agents/             Working contract and task briefs for AI coding agents
```

### Backend

Code is organised by domain: `src/domains/<area>/<domain>/` with `api/`, `services/`, `repositories/`, `models/` and `schemas/`. The areas are auth, business, supplier, network, catalogue, verification, trust, platform, security and marketplace. Shared infrastructure (finance, media, audit, notifications, queue, scheduling) lives in `src/shared/` and never depends on a domain. Tests under `tests/architecture/` read the code and fail the build if a domain crosses one of these boundaries.

```bash
cd backend
python app.py                               # dev server on 0.0.0.0:5000
flask db upgrade                            # apply migrations
python scripts/run_tests.py                 # the ONLY supported way to run tests
python scripts/run_tests.py tests/architecture
```

> Bare `pytest` does not work. The runner sets the environment and the test database, and runs one directory at a time. See `CLAUDE.md`.

### Mobile

```bash
cd frontend/mobile
npx expo start --dev-client     # needs a development build; Expo Go cannot run this app
npm run typecheck
```

The app runs against mock data by default. Set `EXPO_PUBLIC_USE_MOCK_API=false` to use the real backend.

### Web

```bash
cd frontend/web
npm run dev
```

The web portal accepts supplier accounts only.

---

## Documentation

Start with `docs/v2/V2_03_THE_MARKET_AND_THE_THESIS.txt`. Every later design document builds on its reasoning. `CLAUDE.md` is the authority on commands and conventions.

## Team

Mandla Baloyi

© TruConnect. All rights reserved. This code may not be copied or used without permission.
