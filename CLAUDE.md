# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal, self-hosted Magic: The Gathering web app. Goal: consolidate collection management, deck building, price tracking, and EDHRec recommendations using Scryfall as the canonical data source.

This is a two-language stack: Python backend + React/TypeScript frontend communicating via GraphQL.

---

## Commands

### Frontend (`frontend/`)

```bash
npm run dev          # Start Vite dev server
npm run build        # Production build
npm run lint         # ESLint
npm run codegen      # Regenerate TypeScript types from GraphQL schema (run after every schema change)
```

### Backend (`backend/`)

```bash
# Start the FastAPI server
uvicorn app.main:app --reload

# Run type checking (do both before committing)
mypy app/
pyright app/

# Alembic migrations — manage these yourself, do not delegate to Claude
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Celery worker
celery -A celery_worker worker --loglevel=info

# Celery beat scheduler
celery -A celery_worker beat --loglevel=info
```

### Infrastructure

```bash
docker compose up -d          # Start PostgreSQL + Redis
docker compose down           # Stop services
docker compose logs -f        # Follow logs
```

---

## Architecture

``` text
Frontend (React + Vite + Apollo Client)
  └── Feature modules: Converter · Deck Builder · Collection · Price Tracker · EDHRec

GraphQL API (Strawberry + FastAPI)
  ├── CardQuery / CollectionMutation
  ├── ConverterMutation
  ├── DeckMutation / DeckQuery
  └── PriceQuery

Python Services
  ├── Scryfall Sync   — bulk upsert → cards table (daily @ 06:00 UTC)
  ├── Format Converter — CSV parse/emit, scryfall_id pivot
  └── Price Aggregator — daily snapshots @ 07:00 UTC

PostgreSQL (via SQLAlchemy 2.0 async + Alembic)
  ├── cards          — Scryfall bulk cache
  ├── collection     — owned cards + quantities
  ├── decks / deck_cards
  ├── price_history  — time-series (integer cents, never floats)
  └── edhrec_cache   — commander recommendations, weekly TTL

Background Jobs (Celery + Redis)
```

### Key data flow

Strawberry auto-generates the GraphQL schema from Python type annotations. GraphQL Codegen reads the schema and generates TypeScript types for the frontend. This makes Python the single source of truth for types — **run codegen after every schema change**.

### Universal Converter

All import/export formats (Manabox, Moxfield, Archidekt) convert through a canonical intermediate form using `scryfall_id` as the universal pivot. Never convert directly between formats. Canonical form: `{ scryfallId, quantity, foil, condition, language, purchasePrice? }`.

### EDHRec

No official API — uses undocumented JSON endpoints (`https://json.edhrec.com/pages/commanders/[slug].json`). All access goes through a Python adapter layer with a read-through cache in `edhrec_cache`. Treat the JSON structure as fragile; isolate parsing behind the adapter.

---

## Critical Constraints

- **Scryfall rate limits**: bulk data updates every 12h, prices once per day — do not poll more frequently. Must comply with Scryfall's Fan Content Policy.
- **Prices as integer cents**: store and pass prices as integers (cents) everywhere — never floats.
- **`scryfall_id` is the universal card identifier** — use it as the join key across all tables and formats.
- **Celery tasks must be JSON-serializable** — never pass SQLAlchemy model instances as task arguments.
- **Strawberry + async SQLAlchemy** requires careful dependency injection; use a `get_db` async dependency, not global sessions.
- **GraphQL N+1**: use `strawberry.dataloader` for card lookups inside deck/collection resolvers.
- **`@scryfall/api-types`** (npm) provides TypeScript types for Scryfall card objects on the frontend. Pydantic models on the Python side should mirror these — keep them in sync.

---

## Session Discipline

- Run `mypy` + `pyright` before committing — Python type errors compound quickly.
- Run `npm run codegen` after every GraphQL schema change.
- Manage Alembic migrations manually — do not ask Claude to generate or apply them autonomously.
- Paste relevant SQLAlchemy models and Strawberry types into backend sessions for context.
