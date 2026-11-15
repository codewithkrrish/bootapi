# bootapi

A FastAPI starter template with JWT auth, settings, and tests — clone it and
have a working API skeleton in minutes instead of an afternoon.

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Why I built this

Every time I started a new API I did the same boring setup first: FastAPI
scaffold, settings from env vars, register/login, a database, a health
endpoint, and tests I kept meaning to write. So I built the version of that
setup I actually wanted to clone — small enough to read in one sitting, with
nothing I didn't need.

## What's inside

- **JWT auth** — register, login, and a `/auth/me` endpoint. Passwords are
  hashed with stdlib pbkdf2 (no extra auth framework to learn).
- **Settings from the environment** — pydantic-settings, `BOOTAPI_` prefix,
  `.env` file support.
- **SQLite store, no ORM** — plain `sqlite3`, one file, easy to swap for
  Postgres later. The routers never touch SQL directly.
- **Health + readiness endpoints** — `/health` for liveness, `/health/ready`
  pings the database and returns 503 while it can't answer.
- **A working CRUD example** — `/items` shows the pattern for your own
  resources, including owner scoping (another user's item is a 404, not a
  leak).
- **Tests that actually run** — 19 tests covering auth, ownership, and the
  edge cases. Docker + compose files included.

## Quickstart

```bash
git clone https://github.com/codewithkrrish/bootapi.git
cd bootapi
python -m venv .venv && source .venv/bin/activate
pip install .
cp .env.example .env   # then set a real BOOTAPI_SECRET_KEY
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the interactive Swagger UI.

Or with Docker:

```bash
docker compose up --build
```

## A first request

```bash
# register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "correct-horse-123"}'
# {"id":1,"email":"you@example.com"}

# log in
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=you@example.com&password=correct-horse-123"
# {"access_token":"eyJ...","token_type":"bearer"}

# create an item (use the token from above)
curl -X POST http://127.0.0.1:8000/items \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Ship the API"}'
# {"id":1,"title":"Ship the API","done":false}
```

## Endpoints

| Method | Path | Auth | What it does |
| ------ | ---- | ---- | ------------ |
| GET | `/health` | — | Liveness check |
| GET | `/health/ready` | — | Readiness check (pings the DB) |
| POST | `/auth/register` | — | Create a user (409 if the email is taken) |
| POST | `/auth/login` | — | Trade email + password for a JWT |
| GET | `/auth/me` | Yes | Who the token belongs to |
| POST | `/items` | Yes | Create an item |
| GET | `/items` | Yes | List your items |
| GET | `/items/{id}` | Yes | Fetch one item |
| DELETE | `/items/{id}` | Yes | Delete one item |

## Configuration

All settings come from the environment (prefix `BOOTAPI_`) or a `.env` file:

| Variable | Default | What it does |
| -------- | ------- | ------------ |
| `BOOTAPI_SECRET_KEY` | `change-me-in-production` | Signs the JWTs — change this before deploying |
| `BOOTAPI_DATABASE_PATH` | `bootapi.db` | Where the SQLite file lives |
| `BOOTAPI_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | How long a login token lasts |
| `BOOTAPI_DEBUG` | `false` | Extra debug output |

## Project structure

```
bootapi/
├── app/
│   ├── main.py          # app factory + entry point
│   ├── config.py        # settings from the environment
│   ├── security.py      # password hashing + JWT helpers
│   ├── store.py         # SQLite data layer (no ORM)
│   ├── models.py        # request/response shapes
│   ├── deps.py          # shared dependencies (current user, store)
│   └── routers/
│       ├── health.py
│       ├── auth.py
│       └── items.py     # CRUD example — copy it for your own resources
├── tests/
│   ├── test_health.py
│   ├── test_auth.py
│   └── test_items.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Running the tests

```bash
pip install ".[dev]"
python -m pytest -q
```

Tests run against a throwaway database in a temp dir — your real
`bootapi.db` is never touched.

## How auth works

1. `POST /auth/register` stores the email and a pbkdf2 hash (200,000
   iterations, random salt per user). The hash never leaves the server.
2. `POST /auth/login` checks the password and returns a signed JWT
   (HS256, 30 minutes by default).
3. Protected endpoints take `Authorization: Bearer <token>` and load the
   user from the token's subject. A bad token is a 401 with the same
   message as a missing one.

## Limitations

Honest notes, so you know what you're getting:

- **SQLite, single file.** Fine for a starter and for small services; move
  to Postgres when you need concurrent writers or a second server.
- **No refresh tokens.** Tokens last 30 minutes and clients log in again.
  Add refresh tokens when long sessions actually matter, not before.
- **No email verification or password reset.** Registering doesn't confirm
  the email belongs to anyone. That's a feature to add, not one I faked.
- **HS256 symmetric signing.** One shared secret signs and verifies. If
  you split into multiple services, switch to RS256.
- **The `/items` resource is a demo.** It's there to show the pattern —
  delete it when you add your own.

## License

MIT — see [LICENSE](LICENSE).

## Author

Built by [Krrish](https://github.com/codewithkrrish) — I make Python tools,
Discord bots, and small web apps. If this saved you an afternoon, a star
helps more than you'd think.
