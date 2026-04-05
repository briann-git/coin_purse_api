# Budget App API — Copilot Instructions

A personal finance management REST API built with FastAPI. The end goal is cloud deployment with a Kotlin Android/mobile app as the primary client.

## Tech Stack

- **Python 3.12+** managed by [Poetry](https://python-poetry.org/) (virtualenv in `.venv/`)
- **FastAPI** with **Uvicorn** — runs on `0.0.0.0:8000`
- **SQLAlchemy 2.0+** (modern `Mapped[]` / `mapped_column()` style) + **Alembic** migrations
- **SQLite** (`./budget_app.db`) — dev database; UUID generation uses `gen_random_uuid()` (PostgreSQL-compatible for future migration)
- **Pydantic v2** schemas with `model_config = ConfigDict(from_attributes=True)` for ORM ↔ schema conversion

## Build & Run

```bash
# Install dependencies
poetry install

# Run dev server
python main.py           # or: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

> No test suite configured yet. `Base.metadata.create_all()` runs automatically on startup.

## Architecture

```
models/models.py        — All SQLAlchemy ORM models (single file)
schemas/                — Pydantic request/response schemas (one file per resource)
routes/                 — FastAPI routers (one file per resource)
common/db/config.py     — Engine, SessionLocal, get_db() dependency
common/errors/errors.py — Global exception handlers (HTTP, validation, generic)
helpers/db_utils.py     — Reusable query helpers (active_query, get_active_or_404, etc.)
helpers/kinds.py        — TransactionKind resolver
alembic/versions/       — Migration scripts
```

All routes are registered in `main.py` and follow the prefix pattern `/users/{user_id}/resource`.

## Conventions

### Models (`models/models.py`)
All models inherit from `TimestampMixin` and `Base`:
```python
class MyModel(TimestampMixin, Base):
    __tablename__ = "my_models"  # plural snake_case
    # Fields use Mapped[] + mapped_column()
    # id, created_at, updated_at, is_active come from TimestampMixin
    # Soft-delete: set is_active = False — never hard-delete rows
```

### Schemas (`schemas/`)
- Inherit from mixins in `schemas/common.py` (`APIModel`, `ReadBase`, `UUIDMixin`, etc.)
- Naming: `ResourceCreate`, `ResourceRead`, `ResourceUpdate`
- `ReadBase` already provides `id`, `created_at`, `updated_at`, `is_active`

### Routes (`routes/`)
Follow the established pattern in any existing route file:
```python
router = APIRouter(prefix="/users/{user_id}/resource", tags=["resource"])
# Always accept user_id: UUID as path param for ownership scoping
# Use Depends(get_db) for DB session
# Use helpers from helpers/db_utils.py for ownership + active checks
```

### DB Helpers (`helpers/db_utils.py`)
Always use these instead of raw queries:
- `active_query(db, Model)` — filters `is_active = True`
- `get_active_or_404(db, Model, id)` — raises 404 if not found or inactive
- `require_owned_active(db, Model, id, user_id)` — enforces ownership + active state
- `soft_delete(db, Model, id)` — sets `is_active = False`, never deletes rows

### Error Handling
Errors are returned as `ErrorResponse` (see `schemas/errors.py`) with machine-readable `error` codes (`not_found`, `unauthorized`, `validation_error`). Use `HTTPException` with appropriate status codes; the global handlers in `common/errors/errors.py` format all responses consistently.

### Lookup Tables
`TransactionKind` is a seeded lookup table (`income`, `expense`, `transfer`, `refund`). Routes accept `kind_name: KindName` (a `Literal` type), resolved to a DB ID using `resolve_kind_id_or_400()` from `helpers/kinds.py`. Follow this pattern for any future lookup/enum tables.

## Future Deployment Considerations
- Target: cloud-hosted (containerised), consumed by a Kotlin mobile app
- Auth: no auth layer yet — design endpoints to be JWT-ready (user scoping via `user_id` path param is already in place)
- Database: SQLite → PostgreSQL migration is anticipated; avoid SQLite-specific syntax
- All UUIDs use `gen_random_uuid()` server default — compatible with PostgreSQL
