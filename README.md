# Fitness Club API

## Project Overview

REST API for fitness club management built with FastAPI, PostgreSQL, and SQLAlchemy. Supports client management, memberships, class scheduling, and bookings with capacity validation.

## Features

- Manage clients with case-insensitive email uniqueness through the API.
- Create memberships and update their dates or status.
- Register trainers and manage a class schedule.
- Filter classes by UTC date and trainer. Paginate every collection.
- Book and cancel classes with transaction-safe capacity checks.

## Tech Stack

Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.0 async ORM, asyncpg, PostgreSQL 17, Alembic, pytest, pytest-asyncio, HTTPX, Ruff, Docker Compose, and GitHub Actions.

## Architecture

FastAPI routers expose the HTTP API and obtain an `AsyncSession` per request through dependency injection. Pydantic validates input and serializes responses. Services implement business rules and open transactions for writes. SQLAlchemy models describe the tables and database constraints. Alembic manages schema changes.

## Getting Started

### Docker Compose

```bash
docker compose up --build
```

Compose starts PostgreSQL, waits for its health check, and starts the API after applying migrations. Open [Swagger UI](http://localhost:8000/docs). The API is bound to localhost, and the database port is available inside the Compose network.

### Local Python

Create an empty PostgreSQL database and grant a local role permission to connect and create tables in it. Run the following from the repository root and edit `.env` for your local connection.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Application and migration connection string in `postgresql+asyncpg://` format. For Compose, the API service supplies its own URL. |
| `POSTGRES_USER` | Optional Compose database role. Defaults to `fitness`. |
| `POSTGRES_DB` | Optional Compose database name. Defaults to `fitness_club`. |
| `TEST_DATABASE_URL` | Exported connection string for a disposable test database whose name ends in `_test`. |

The Compose configuration uses PostgreSQL trust authentication for local development. A standalone database can use its own credentials in `.env`.

## Database Migrations

Run these commands with an active virtual environment and `DATABASE_URL` available in the environment or in `.env`.

```bash
alembic upgrade head
alembic current
alembic check
```

After editing the ORM models, create a revision with `alembic revision --autogenerate -m "Describe the change"`, review the generated operations, and apply the revision.

## API Endpoints

All routes use the `/api/v1` prefix.

| Path | Methods |
| --- | --- |
| `/clients` | `POST`, `GET` |
| `/clients/{id}` | `GET`, `PATCH`, `DELETE` |
| `/memberships` | `POST`, `GET` |
| `/memberships/{id}` | `GET`, `PATCH` |
| `/trainers` | `POST`, `GET` |
| `/trainers/{id}` | `GET` |
| `/classes` | `POST`, `GET` |
| `/classes/{id}` | `GET`, `PATCH`, `DELETE` |
| `/bookings` | `POST`, `GET` |
| `/bookings/{id}` | `DELETE` |

Collections return arrays and accept `limit` (1–100, default 20) and `offset` (default 0). The classes collection also accepts an ISO date and a `trainer_id`. For partial updates, omit fields to keep their current values.

Requests return `200` for reads and updates, `201` for creation, and `204` for deletion. Errors use `404` for missing resources, `409` for conflicts, and `422` for invalid inputs.

```bash
api=http://localhost:8000/api/v1

curl -i "$api/clients" -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","phone":"+35712345678"}'

curl -i "$api/trainers" -H 'Content-Type: application/json' \
  -d '{"name":"Alex Morgan","specialization":"Mobility"}'

# Use the IDs returned by the preceding requests and choose a future date.
curl -i "$api/memberships" -H 'Content-Type: application/json' \
  -d '{"client_id":1,"start_date":"2030-05-01","end_date":"2030-05-31"}'

curl -i "$api/classes" -H 'Content-Type: application/json' \
  -d '{"title":"Mobility","trainer_id":1,"starts_at":"2030-05-10T18:00:00+03:00","duration_minutes":45,"capacity":10}'

curl "$api/classes?date=2030-05-10&trainer_id=1&limit=10&offset=0"

# Use the returned class ID, then use the booking ID to cancel.
curl -i "$api/bookings" -H 'Content-Type: application/json' \
  -d '{"client_id":1,"class_id":1}'

curl -i -X DELETE "$api/bookings/1"
```

## Running Tests

Install the development dependencies, then point the suite at an empty PostgreSQL database dedicated to testing. To start one with Docker, run:

```bash
docker run --rm -d --name fitness-club-test \
  -e POSTGRES_USER=fitness -e POSTGRES_DB=fitness_club_test \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  -p 127.0.0.1:55433:5432 postgres:17
docker logs fitness-club-test
```

Once the server is ready to accept TCP connections, export the URL and run:

```bash
export TEST_DATABASE_URL=postgresql+asyncpg://fitness@127.0.0.1:55433/fitness_club_test
pytest -q
ruff check .
ruff format --check .
```

The suite applies Alembic migrations and truncates the application tables before each test. It exercises the FastAPI app through HTTPX and uses PostgreSQL for every request. When finished with the disposable container, run `docker stop fitness-club-test`.

## Business Rules

- Client emails are normalized to lowercase, with a PostgreSQL unique constraint on the stored value.
- An eligible membership has status `active` and covers the UTC calendar date of the class, including both endpoints. The status can be changed explicitly and booking always checks the date range.
- Class start times require a UTC offset and are stored as PostgreSQL `timestamptz`. Responses and class date filters use UTC.
- Booking checks the client, class, start time, membership, duplicate status, and capacity in one transaction. Creation locks the class row with `SELECT FOR UPDATE` before counting bookings. PostgreSQL `READ COMMITTED` lets the next transaction see a committed booking after it acquires the lock.
- Cancellation deletes the booking and frees a seat. Capacity changes share the class lock and cannot reduce capacity below the booking count. Membership edits and rescheduling affect eligibility checks for subsequent bookings.
- Deleting a client removes that client's memberships and bookings. Deleting a class removes its bookings.

## Project Structure

```text
fitness-club-api/
├── app/
│   ├── main.py           # App factory, lifespan, error handlers
│   ├── api/              # HTTP routers
│   ├── core/             # Settings and async database sessions
│   ├── models/           # ORM tables and constraints
│   ├── schemas/          # Request and response models
│   └── services/         # Business rules and transactions
├── alembic/
│   └── versions/         # Database migrations
├── tests/                # API integration tests
├── .github/workflows/    # CI on push and pull request
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── compose.yaml
├── Dockerfile
├── pyproject.toml
└── README.md
```
