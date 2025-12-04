# Backend `app/` Structure — File-by-File Guide

This document explains each file within `backend/app/` in plain language and shows how the pieces fit together. It's written for someone new to FastAPI and databases.

## Quick map

```
backend/app/
├─ main.py                 # FastAPI app + CORS and health endpoint
├─ api/
│  └─ endpoints/
│     └─ messages.py       # Simple REST endpoints for Message model
├─ db/
│  ├─ base_class.py        # SQLAlchemy declarative Base helper
│  ├─ base.py              # Imports models so Alembic can detect them
│  └─ session.py           # DB engine + session factory + get_db dependency
└─ models/
   └─ message.py           # SQLAlchemy Message model
```

---

## Goals of this guide

- Explain what each file does and why it's needed
- Show how requests flow from HTTP → DB → response
- Provide commands to run and test locally
- Describe common next steps (migrations, auth, async)

---

## `main.py`

Path: `backend/app/main.py`

Purpose:
- Creates the FastAPI application object (`app`) that runs the API server
- Configures CORS so your frontend (Vite / Vercel) can call the API from the browser
- Exposes a simple `/health` endpoint used for quick checks and monitoring

Key lines explained:
- `app = FastAPI(title="Life Story Game API")` — creates the web app
- `origins = ["http://localhost:5173", "https://your-vercel-app.vercel.app"]` — allowed browser origins
- `app.add_middleware(CORSMiddleware, ...)` — applies the CORS rules
- `@app.get('/health')` — a GET endpoint that returns status JSON

How to run locally using Uvicorn (development):

```bash
# From repository root
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Then visit `http://localhost:8000/health`.

Security note:
- Don't add `allow_origins=["*"]` in production for authenticated endpoints. Be explicit about allowed domains.

---

## `api/endpoints/messages.py`

Path: `backend/app/api/endpoints/messages.py`

Purpose:
- Defines a small REST API router for creating and reading `Message` records in the database
- Demonstrates use of a Pydantic model for request validation and `Depends(get_db)` to obtain a DB session

Key pieces:
- `router = APIRouter()` — a router that can later be mounted in `main.py` under a prefix like `/api/messages`
- `class MessageCreate(BaseModel)` — Pydantic schema used for request validation
- `create_message(msg: MessageCreate, db: Session = Depends(get_db))` — POST endpoint: creates a SQLAlchemy `Message`, commits, and returns it
- `read_messages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db))` — GET endpoint: lists messages

How it uses DB session:
- `db: Session = Depends(get_db)` injects a SQLAlchemy session from `session.py` for the request scope
- The handler uses `db.add(...)`, `db.commit()` and `db.refresh(...)` to persist the object

Test the endpoints (after server is running):

```bash
# Create a message
curl -X POST http://localhost:8000/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"role": "user", "content": "Hello world"}' | jq

# List messages
curl http://localhost:8000/api/messages/ | jq
```

Note: For this router to be reachable you must include it in `main.py` (see "Next steps" below).

---

## `db/base_class.py`

Path: `backend/app/db/base_class.py`

Purpose:
- Provides a small convenience base class for SQLAlchemy models using `@as_declarative()`
- Automatically generates `__tablename__` from the model class name

Why this is useful:
- Avoids repeating table-name boilerplate in every model
- Provides a single place to add common model behavior in the future

Important lines:
- `@as_declarative()` marks the class as SQLAlchemy declarative base
- `@declared_attr def __tablename__` returns `cls.__name__.lower()`, so `Message` → `messages` by default

---

## `db/base.py`

Path: `backend/app/db/base.py`

Purpose:
- Imports the `Base` from `base_class.py` and imports models so that tools like Alembic can "see" the models when autogenerating migrations

Why import models here?
- Alembic autogeneration compares the model metadata (Base.metadata) to the actual DB. If models are not imported anywhere, Alembic won't detect them.

Note: Add future model imports here (e.g. `from app.models.user import User`) so Alembic can detect them.

---

## `db/session.py`

Path: `backend/app/db/session.py`

Purpose:
- Reads the `DATABASE_URL` environment variable and creates a SQLAlchemy engine and a `SessionLocal` factory
- Exposes `get_db()` which yields a DB session and ensures it is closed after the request

Key lines:
- `SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")` — you must set this env var (see next section)
- `engine = create_engine(SQLALCHEMY_DATABASE_URL)` — creates DB engine
- `SessionLocal = sessionmaker(..., bind=engine)` — creates a session factory
- `def get_db(): db = SessionLocal(); try: yield db finally: db.close()` — FastAPI dependency that yields a per-request session

Important deployment notes:
- For production or serverless, prefer connection pooling or a managed DB service; `create_engine` handles pooling for typical long-running processes
- In serverless environments (e.g., many short-lived functions), use a connection pooler (PgBouncer) or specialized async setups

Environment variable example (in `.env`):
```
DATABASE_URL="postgresql://doadmin:password@host:5432/defaultdb?sslmode=require"
```

---

## `models/message.py`

Path: `backend/app/models/message.py`

Purpose:
- SQLAlchemy `Message` model representing the `messages` table

Columns:
- `id`: Integer primary key
- `role`: `String` (e.g. `user` or `assistant`)
- `content`: `Text` — the message content
- `created_at`: `DateTime` defaulted to `datetime.utcnow`

Notes:
- `__tablename__` is explicitly set to `messages` (this is optional because `base_class` auto-generates tablenames, but explicit naming is okay)

---

## How a request flows (high-level)

1. Browser → Frontend JavaScript makes an HTTP request to the backend (e.g., POST `/api/messages`)
2. FastAPI receives the request and selects the matching route
3. FastAPI resolves dependencies: `get_db()` is called to provide a SQLAlchemy session
4. Handler code uses session (`db`) to create/query models and commits changes
5. Handler returns a response; FastAPI serializes it to JSON and sends back to the client
6. `get_db()` finally closes the DB session

---

## Missing wiring to enable API paths

Currently the `messages.py` router is defined but not yet mounted in `main.py`. To expose the messages endpoints add these lines to `main.py`:

```python
from app.api.endpoints import messages as messages_router
app.include_router(messages_router.router, prefix="/api/messages", tags=["messages"])
```

After this, POST and GET `/api/messages/` will be reachable.

---

## Migrations (Alembic)

This project prepares for migrations by:
- Keeping `Base` and importing models in `db/base.py`

To add migrations:
1. Install alembic (already in `requirements.txt`) and initialize if not already:

```bash
alembic init alembic
```

2. Edit `alembic/env.py` to import `app.db.base` so `Base.metadata` is available.
3. Set `sqlalchemy.url` in `alembic.ini` or configure env var injection.
4. Generate a revision:

```bash
alembic revision --autogenerate -m "create messages table"
alembic upgrade head
```

---

## Run & Test (summary)

1. Start backend (local development):

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Create a message:

```bash
curl -X POST http://localhost:8000/api/messages/ \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Hello"}'
```

3. List messages:

```bash
curl http://localhost:8000/api/messages/
```

If you are using Docker Compose (the repository includes a `docker-compose.yml`) you can build and run the stack:

```bash
# Build images
sudo docker-compose build
# Start services in background
sudo docker-compose up -d
# Tail backend logs
sudo docker-compose logs -f backend
```

---

## Common pitfalls & tips

- `DATABASE_URL` must be set in environment or `.env`. `db/session.py` calls `load_dotenv()` so a `.env` at repo root works during local dev.
- Alembic autogeneration will only detect models that are imported somewhere (that's why `db/base.py` imports `Message`).
- The provided `session` is synchronous. If you switch to an async DB stack (e.g. `asyncpg` + `sqlalchemy` 2.0 async engine), you'll need to refactor endpoints to async and use `AsyncSession`.
- For serverless deployment, consider connection pooling solutions like PgBouncer to avoid exhausting DB connections.

---

## Suggested next steps (practical roadmap)

1. Mount `messages` router in `main.py` so endpoints are reachable.
2. Add basic Alembic migrations and apply them to your database.
3. Add a small seed script to create required reference rows (routes, phases) if needed.
4. Implement authentication (JWT or OAuth) and protect endpoints before storing user stories.
5. Add tests for the endpoints (use `pytest` + `testclient` from FastAPI).

---

If you want, I can now:
- Add the `app.include_router(...)` line to `main.py` and restart the server, or
- Create an Alembic `env.py` template that imports `app.db.base`, or
- Add a small `README` snippet with the exact `.env` example and `docker-compose` commands.

Which would you like next?
