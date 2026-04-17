# MTG Personal App — Planning Summary (v2)

## Overview

A personal, self-hosted Magic: The Gathering web app built on the Scryfall API and `@scryfall/api-types`. Goal: consolidate collection management, deck building, price tracking, and EDHRec recommendations under one roof with no rate-limit concerns.

**Architecture**: React + Apollo Client → GraphQL API (Strawberry + FastAPI) → Python services → PostgreSQL

---

## Tech Stack

| Layer | Choice |
|---|---|
| Framework | React + TypeScript (Vite SPA) |
| UI | shadcn/ui + Tailwind |
| Data fetching | Apollo Client (GraphQL) |
| API layer | FastAPI + Strawberry (GraphQL) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL (local Docker) |
| Background jobs | Celery + Redis |
| Auth | FastAPI-Users (self-hosted, single user) |
| Card types | `@scryfall/api-types` (TS) / Pydantic models (Python) |
| CSV parsing | papaparse (TS frontend) + Python csv module |
| Charts | Recharts |
| HTTP client (Python) | httpx (async) |

---

## Features

### 1. Universal Converter ✅ Most buildable

Converts between **Manabox ↔ Moxfield ↔ Archidekt** using `scryfall_id` as the universal pivot key.

- All formats support `scryfall_id` as an identifier
- Internal canonical form: `{ scryfallId, quantity, foil, condition, language, purchasePrice? }`
- Any format → canonical → any target format (never direct format-to-format)
- Biggest pain point: condition scale differences (7 levels vs 6) and promo/special set naming
- Resolving `scryfall_id` first from local bulk data eliminates all naming ambiguity

### 2. Deck Builder ⚠️ Scope carefully

Worth building:

- Card search (proxy Scryfall syntax search against local DB)
- Deck boards: mainboard, sideboard, maybeboard, commander
- Categories/tags per card (Archidekt-style)
- Visual grouping by type, CMC curve, color pips
- Commander legality checking (color identity from Scryfall)
- Export to various formats

Skip for personal use:

- Social features, comments, public decks
- Real-time collaboration
- Playtesting simulator (separate module if wanted later)

### 3. Price Tracking ⚠️ Scryfall-only, 24h granularity

- Scryfall syncs TCGPlayer market price + Cardmarket trend price once per day
- Bulk data includes `prices.usd`, `usd_foil`, `usd_etched`, `eur`
- Store daily snapshots in `price_history` table → trend charts over time
- Track total collection value over time, set price alerts
- **Cannot do**: real-time prices, TCGPlayer buylist, Card Kingdom (no public APIs)

### 4. EDHRec Integration ⚠️ Scraping, not a real API

- EDHRec has no official API — data available via undocumented JSON endpoints
- Pattern: `https://json.edhrec.com/pages/commanders/[slug].json`
- Strategy: read-through cache with TTL in `edhrec_cache` table
- Overlay collection ownership status on top of recommendations
- Risk: JSON structure can change; isolate behind an adapter layer in Python

---

## Architecture

```
Frontend (React + Apollo Client)
  └── Feature modules: Converter · Deck Builder · Price Tracker · EDHRec

GraphQL API (Strawberry + FastAPI)
  ├── CardQuery / CollectionMutation
  ├── ConverterMutation
  ├── DeckMutation / DeckQuery
  └── PriceQuery

Python Services (FastAPI + Celery)
  ├── Scryfall Sync Service   — bulk upsert → cards table (daily)
  ├── Format Converter        — CSV parse/emit, scryfallId pivot
  └── Price Aggregator        — daily price snapshots + history

Database (PostgreSQL + SQLAlchemy 2.0)
  ├── cards          — Scryfall bulk cache
  ├── decks          — user decks
  ├── collection     — owned cards + quantities
  ├── price_history  — time-series price data
  └── edhrec_cache   — recommendations by commander

Background Jobs (Celery + Redis)
  ├── Scryfall bulk sync      — daily @ 06:00 UTC
  ├── Price snapshot          — daily @ 07:00 UTC
  └── EDHRec cache refresh    — weekly

External Sources
  ├── Scryfall API      — cards, prices, bulk data (free, rate-limited)
  ├── EDHRec JSON       — unofficial endpoints, scraped + cached
  ├── Manabox CSV       — import/export
  └── Moxfield/Archidekt CSV — import/export
```

---

## Project Structure

```
mtg-app/
├── frontend/                   # React + TypeScript (Vite)
│   ├── src/
│   │   ├── components/         # shadcn/ui components
│   │   ├── features/
│   │   │   ├── converter/
│   │   │   ├── deck-builder/
│   │   │   ├── collection/
│   │   │   └── price-tracker/
│   │   ├── graphql/            # Generated types + queries
│   │   ├── lib/
│   │   │   └── types.ts        # CanonicalCard, DeckCard, etc.
│   │   └── apollo.ts           # Apollo Client setup
│   └── codegen.ts              # GraphQL codegen config
│
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── graphql/            # Strawberry schema + resolvers
│   │   │   ├── schema.py
│   │   │   ├── types.py        # Strawberry types
│   │   │   └── resolvers/
│   │   ├── models/             # SQLAlchemy models
│   │   │   └── models.py
│   │   ├── services/
│   │   │   ├── scryfall_sync.py
│   │   │   ├── converter.py
│   │   │   └── price_snapshot.py
│   │   ├── tasks/              # Celery tasks
│   │   │   └── tasks.py
│   │   ├── db.py               # SQLAlchemy async engine
│   │   └── main.py             # FastAPI app entry
│   ├── alembic/                # DB migrations
│   ├── requirements.txt
│   └── celery_worker.py
│
└── docker-compose.yml          # PostgreSQL + Redis
```

---

## Recommended Build Order

1. **Infrastructure** — Docker Compose (Postgres + Redis), Python env, React scaffold
2. **SQLAlchemy models + Alembic migrations** — foundation for everything
3. **Scryfall bulk sync** — Celery task, seeds the `cards` table
4. **GraphQL API skeleton** — Strawberry schema, FastAPI mount, Apollo Client wired
5. **Universal Converter** — highest unique value, lowest dependency risk
6. **Deck Builder** — schema first (models), then GraphQL, then UI
7. **Price tracking** — needs ~2 weeks of snapshots before trends are useful
8. **EDHRec integration** — cache layer hooked into deck builder as suggestions panel

---

## Key Differences from v1 (tRPC + Next.js)

| Concern | v1 | v2 |
|---|---|---|
| Framework | Next.js 15 App Router | Vite SPA (React) |
| API layer | tRPC (RPC-style) | GraphQL (Strawberry) |
| API client | TanStack Query + tRPC | Apollo Client |
| Backend language | TypeScript (Node) | Python (FastAPI) |
| ORM | Drizzle ORM | SQLAlchemy 2.0 async |
| Migrations | drizzle-kit | Alembic |
| Background jobs | pg-boss (Postgres) | Celery + Redis |
| Auth | Better Auth | FastAPI-Users |
| Type generation | Native TypeScript | GraphQL Codegen → TS types |

### Why GraphQL over tRPC here

- Strawberry auto-generates the schema from Python type annotations — single source of truth
- GraphQL Codegen turns the schema into TypeScript types for the frontend automatically
- Easier to query nested relationships (deck → cards → prices) in a single request
- Introspection tooling (GraphiQL) useful for exploring data while building

---

## Vibe Coding Estimates (v2)

**Total: ~450k–900k tokens across multiple sessions**

| Phase | Est. tokens |
|---|---|
| Infrastructure + scaffold | 20–35k |
| SQLAlchemy models + Alembic | 25–40k |
| Scryfall sync (Python) | 20–35k |
| GraphQL schema + resolvers | 40–70k |
| Apollo Client setup + codegen | 15–25k |
| CSV converter (Python) | 35–60k |
| Deck builder (backend + API) | 30–50k |
| Deck builder (UI) | 60–120k |
| Price tracking + charts | 30–50k |
| EDHRec cache + display | 20–40k |
| Bug fixing / refinement | 80–150k |

### Session discipline for Python + GraphQL

- **One feature per session** — don't let conversations grow past ~50 turns
- **Lock types early** — paste Strawberry types AND TypeScript `CanonicalCard` into every session
- **Paste relevant SQLAlchemy models** at the top of each backend session
- **Run `mypy` + `pyright`** before committing — Python type errors compound fast
- **Run codegen after every schema change** — keep TS types in sync
- **Learn `alembic` commands yourself** — don't let Claude manage migrations

### Known pain points

- Strawberry + async SQLAlchemy sessions require careful dependency injection (use `get_db` dependency)
- Celery task serialization: always use JSON-serializable payloads, not SQLAlchemy models
- GraphQL N+1 queries: use `strawberry.dataloader` for card lookups inside deck resolvers
- EDHRec scraping breaks when their JSON structure changes
- Recharts + complex data shapes requires many UI iterations
- Context length compounds cost in later sessions — start fresh often

---

## Key Constraints & Notes

- Scryfall bulk data updates every 12h; prices update once per day — don't poll more than that
- Must comply with Scryfall's Fan Content Policy: no paywalling data, no repackaging/proxying without added value
- `@scryfall/api-types` gives full TypeScript types for Scryfall card objects — use on frontend
- Pydantic models mirror `@scryfall/api-types` on the Python side — keep them in sync
- Realistic timeline: **3–5 weekends** to a working personal tool (slightly longer than v1 due to two-language stack)
- Prices stored as integer cents in both Python (SQLAlchemy `Integer`) and TypeScript — never floats
