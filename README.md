# Task Management API

[![CI](https://github.com/Gilberthoughton/fastapi-task-api/actions/workflows/ci.yml/badge.svg)](https://github.com/Gilberthoughton/fastapi-task-api/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A production-structured REST API for managing personal tasks, built with
**FastAPI**, **SQLAlchemy 2.0**, and **JWT authentication**. Each user can
register, log in, and manage a private list of tasks — full CRUD with
per-user ownership, input validation, and consistent error handling.

This repository is a portfolio project intended to demonstrate backend
engineering fundamentals: clean layered architecture, REST API design,
database modelling, stateless authentication, automated tests, and
containerization with Docker.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
  - [Run Locally](#run-locally)
  - [Run with Docker](#run-with-docker)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Example Usage (cURL)](#example-usage-curl)
- [Running Tests](#running-tests)
- [Design Decisions](#design-decisions)

---

## Features

- **User registration** with email + password, validated and uniqueness-checked
- **User login** issuing a signed **JWT** access token
- **JWT-protected** endpoints via the OAuth2 bearer scheme
- **Task CRUD** — create, list (paginated), read, partial-update, delete
- **Per-user ownership** — users can only ever see or modify their own tasks
- **Input validation** with Pydantic v2 (typed, constrained fields)
- **Consistent error handling** with appropriate HTTP status codes
- **Interactive API docs** auto-generated at `/docs` and `/redoc`
- **Automated test suite** (pytest) covering auth, CRUD, and ownership isolation
- **Dockerized** with a non-root image, health check, and Compose file

---

## Tech Stack

| Concern            | Choice                                   |
| ------------------ | ---------------------------------------- |
| Language           | Python 3.12                              |
| Web framework      | FastAPI                                  |
| ORM                | SQLAlchemy 2.0 (typed `Mapped` columns)  |
| Validation         | Pydantic v2 + pydantic-settings          |
| Database           | SQLite (swappable for PostgreSQL)        |
| Auth               | JWT (PyJWT) + bcrypt password hashing    |
| Server             | Uvicorn (ASGI)                           |
| Tests              | pytest + httpx TestClient                |
| Lint / format      | Ruff                                     |
| CI                 | GitHub Actions (lint, tests, Docker build) |
| Packaging / deploy | Docker + Docker Compose                  |

---

## Architecture

The application follows a **layered (clean) architecture**. Each layer has a
single responsibility and depends only on the layers beneath it, which keeps
business logic testable and the HTTP surface thin.

```mermaid
flowchart TD
    Client([HTTP Client])

    subgraph App["FastAPI Application"]
        direction TB
        API["API layer<br/><code>api/routes/*</code> · <code>api/deps.py</code><br/><i>routing · auth gate · status codes</i>"]
        Schemas["Schema layer<br/><code>schemas/*</code><br/><i>request / response contracts (Pydantic)</i>"]
        CRUD["CRUD layer<br/><code>crud/*</code><br/><i>owner-scoped queries</i>"]
        Models["Model layer<br/><code>models/*</code><br/><i>SQLAlchemy ORM tables</i>"]
        Core["Core<br/><code>core/config · database · security</code><br/><i>settings · engine · hashing + JWT</i>"]
    end

    DB[(SQLite / PostgreSQL)]

    Client -->|JSON over HTTP| API
    API --> Schemas
    API --> CRUD
    CRUD --> Models
    Models --> Core
    Core --> DB
```

**Request lifecycle — `POST /api/v1/tasks`:**

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant R as Route handler
    participant D as get_current_user (deps)
    participant V as Pydantic (TaskCreate)
    participant CR as CRUD layer
    participant DB as Database

    C->>R: POST /tasks + Bearer token + JSON body
    R->>D: resolve current user
    alt token missing / invalid
        D-->>C: 401 Unauthorized
    end
    D-->>R: authenticated User
    R->>V: validate request body
    alt body invalid
        V-->>C: 422 Unprocessable Entity
    end
    V-->>R: validated payload
    R->>CR: create_task(owner_id, payload)
    CR->>DB: INSERT (scoped to owner_id)
    DB-->>CR: row
    CR-->>R: Task
    R-->>C: 201 Created (TaskRead)
```

This separation means the database can be swapped (SQLite → PostgreSQL) by
changing one environment variable, and the query logic can be unit-tested
without spinning up HTTP.

---

## Project Structure

```
fastapi-task-api/
├── app/
│   ├── main.py                 # App factory: routers, CORS, lifespan, error handlers
│   ├── core/
│   │   ├── config.py           # Env-driven settings (pydantic-settings)
│   │   ├── database.py         # Engine, session factory, Base, get_db dependency
│   │   └── security.py         # Password hashing + JWT encode/decode
│   ├── models/
│   │   ├── user.py             # User ORM model
│   │   └── task.py             # Task ORM model
│   ├── schemas/
│   │   ├── user.py             # UserCreate / UserRead
│   │   ├── task.py             # TaskCreate / TaskUpdate / TaskRead
│   │   └── token.py            # Token / TokenPayload
│   ├── crud/
│   │   ├── user.py             # User queries + authentication
│   │   └── task.py             # Owner-scoped task queries
│   └── api/
│       ├── deps.py             # Shared dependencies (DB session, current user)
│       └── routes/
│           ├── auth.py         # /auth/register, /auth/login, /auth/me
│           └── tasks.py        # /tasks CRUD
├── tests/
│   ├── conftest.py             # In-memory DB + auth fixtures
│   ├── test_auth.py
│   └── test_tasks.py
├── .github/workflows/ci.yml    # Lint + tests + Docker build on push/PR
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml              # Ruff + pytest configuration
├── .env.example
├── .dockerignore
├── .gitignore
├── LICENSE
└── README.md
```

---

## Database Schema

Two tables with a one-to-many relationship: a **User** owns many **Tasks**.

```mermaid
erDiagram
    USERS ||--o{ TASKS : owns

    USERS {
        int      id PK
        string   email UK "unique, indexed"
        string   hashed_password "bcrypt hash"
        datetime created_at
    }

    TASKS {
        int      id PK
        string   title
        text     description "nullable"
        bool     completed "default false"
        int      owner_id FK "indexed, ON DELETE CASCADE"
        datetime created_at
        datetime updated_at "auto-updates"
    }
```

### `users`

| Column            | Type        | Constraints                       |
| ----------------- | ----------- | --------------------------------- |
| `id`              | INTEGER     | Primary key                       |
| `email`           | VARCHAR(320)| Unique, indexed, not null         |
| `hashed_password` | VARCHAR(255)| Not null (bcrypt hash)            |
| `created_at`      | DATETIME    | Not null, defaults to now (UTC)   |

### `tasks`

| Column        | Type        | Constraints                                  |
| ------------- | ----------- | -------------------------------------------- |
| `id`          | INTEGER     | Primary key                                  |
| `title`       | VARCHAR(255)| Not null                                     |
| `description` | TEXT        | Nullable                                     |
| `completed`   | BOOLEAN     | Not null, default `false`                    |
| `owner_id`    | INTEGER     | Foreign key → `users.id`, indexed, not null  |
| `created_at`  | DATETIME    | Not null, defaults to now (UTC)              |
| `updated_at`  | DATETIME    | Not null, auto-updates on modify             |

**Relationship & integrity**

```
users (1) ──────< (many) tasks
        owner_id  FK ON DELETE CASCADE
```

- `tasks.owner_id` references `users.id` with **`ON DELETE CASCADE`**, so
  deleting a user removes their tasks and never leaves orphaned rows.
- `email` is **unique and indexed** to enforce one account per address and to
  keep login lookups fast.
- `owner_id` is **indexed** because every task query filters on it.

> Schema is created automatically on startup via `Base.metadata.create_all`.
> A production deployment would replace this with **Alembic** migrations for
> versioned, reversible schema changes.

---

## Getting Started

### Prerequisites

- Python **3.12+** (for local runs), or
- Docker + Docker Compose (for containerized runs)

### Run Locally

```bash
# 1. Clone and enter the project
cd fastapi-task-api

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your environment file and set a real SECRET_KEY
cp .env.example .env
# Generate a strong secret:
#   openssl rand -hex 32
# then paste it into .env as SECRET_KEY

# 5. Start the development server (auto-reload)
uvicorn app.main:app --reload
```

The API is now running at **http://localhost:8000**.
Open **http://localhost:8000/docs** for interactive Swagger documentation.

### Run with Docker

```bash
# Build and start in the background
docker compose up --build -d

# Tail logs
docker compose logs -f

# Stop
docker compose down
```

The service listens on **http://localhost:8000** and persists its SQLite
database in a named Docker volume (`api-data`).

> **Note:** Set a strong `SECRET_KEY` in `docker-compose.yml` (or via a `.env`
> file) before any non-local use.

---

## Configuration

All configuration is supplied through environment variables (loaded from `.env`
in development). See [`.env.example`](.env.example).

| Variable                      | Default                  | Description                                  |
| ----------------------------- | ------------------------ | -------------------------------------------- |
| `PROJECT_NAME`                | `Task Management API`    | Shown in the OpenAPI docs                     |
| `API_V1_PREFIX`               | `/api/v1`                | Base path for all versioned routes            |
| `ENVIRONMENT`                 | `development`            | Free-form environment label                   |
| `SECRET_KEY`                  | *(required)*             | Key used to sign JWTs — keep secret           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                     | Access-token lifetime in minutes              |
| `ALGORITHM`                   | `HS256`                  | JWT signing algorithm                         |
| `BACKEND_CORS_ORIGINS`        | `http://localhost:3000,http://localhost:8000` | Comma-separated allow-list of browser origins |
| `DATABASE_URL`                | `sqlite:///./tasks.db`   | SQLAlchemy connection string                  |

To use PostgreSQL instead of SQLite, set e.g.
`DATABASE_URL="postgresql+psycopg://user:pass@host:5432/tasks"` — no code
changes required.

---

## API Documentation

Base URL: `http://localhost:8000/api/v1`
Interactive docs: `GET /docs` (Swagger UI) · `GET /redoc` (ReDoc)

| Method   | Path               | Auth | Description                       | Success |
| -------- | ------------------ | :--: | --------------------------------- | :-----: |
| `GET`    | `/health`          |  —   | Liveness/readiness probe          |  200    |
| `POST`   | `/auth/register`   |  —   | Register a new user               |  201    |
| `POST`   | `/auth/login`      |  —   | Obtain a JWT access token         |  200    |
| `GET`    | `/auth/me`         |  ✅  | Get the current user              |  200    |
| `POST`   | `/tasks`           |  ✅  | Create a task                     |  201    |
| `GET`    | `/tasks`           |  ✅  | List your tasks (paginated)       |  200    |
| `GET`    | `/tasks/{id}`      |  ✅  | Get one of your tasks             |  200    |
| `PATCH`  | `/tasks/{id}`      |  ✅  | Partially update a task           |  200    |
| `DELETE` | `/tasks/{id}`      |  ✅  | Delete a task                     |  204    |

**Authentication:** call `/auth/login` with form fields `username` (your email)
and `password`. The response contains an `access_token`; send it on protected
requests as `Authorization: Bearer <token>`.

**Error responses**

| Status | When                                                |
| ------ | --------------------------------------------------- |
| `401`  | Missing/invalid/expired token, or bad credentials   |
| `404`  | Task not found (or owned by another user)           |
| `409`  | Email already registered                            |
| `422`  | Request body fails validation                       |

---

## Example Usage (cURL)

```bash
BASE=http://localhost:8000/api/v1

# 1. Register
curl -s -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"password123"}'

# 2. Log in and capture the token
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -d "username=jane@example.com&password=password123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Create a task
curl -s -X POST $BASE/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Ship portfolio","description":"Polish the README"}'

# 4. List tasks
curl -s $BASE/tasks -H "Authorization: Bearer $TOKEN"

# 5. Update a task (mark complete)
curl -s -X PATCH $BASE/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"completed":true}'

# 6. Delete a task
curl -s -X DELETE $BASE/tasks/1 -H "Authorization: Bearer $TOKEN"
```

---

## Running Tests

```bash
pip install -r requirements.txt

# Lint & format check (same as CI)
ruff check .
ruff format --check .

# Test suite
SECRET_KEY=test-secret pytest
```

The suite runs against an isolated in-memory SQLite database (no setup needed)
and covers:

- Registration: success, duplicate email, invalid email, weak password
- Login: success and wrong-password rejection
- Task CRUD: create, list, read, update, delete
- **Ownership isolation**: one user cannot read or delete another user's task
- Auth enforcement: protected routes reject unauthenticated requests

> **Continuous Integration:** every push and pull request to `main` runs the
> linter, the full test suite (Python 3.12), and a Docker image build via
> [GitHub Actions](.github/workflows/ci.yml).

---

## Design Decisions

- **Layered architecture** keeps HTTP, validation, and persistence concerns
  separate, so each can be reasoned about and tested in isolation.
- **Owner-scoped queries** enforce authorization at the data layer rather than
  trusting the route — a task lookup *cannot* return another user's row.
- **404 instead of 403** for tasks owned by others avoids leaking the existence
  of resources a user isn't allowed to see.
- **Stateless JWT auth** means no server-side session store; tokens are signed
  and self-validating, which scales horizontally without shared state.
- **Bcrypt password hashing** — plaintext passwords are never stored.
- **Pydantic response models** act as an allow-list on output, so internal
  fields like `hashed_password` can never accidentally be serialized.
- **Environment-driven config** (twelve-factor) keeps secrets out of code and
  makes the same image deployable across environments.
- **Explicit CORS allow-list** rather than a wildcard, so the API never echoes
  arbitrary origins on credentialed requests.
- **Linting + CI as a quality gate** — Ruff and the test suite run on every
  push, so regressions are caught before merge.

---

### Possible Next Steps

Ideas that would extend this into a larger system: Alembic migrations,
refresh tokens + token revocation, role-based access control, rate limiting,
structured logging/observability, and a CI pipeline running the test suite on
every push.
