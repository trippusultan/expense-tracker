# Expense Tracker API

A FastAPI + JWT-backed REST API for tracking personal expenses.
Each authenticated user owns their own expense records; JWT tokens protect every write endpoint.

**Tech Stack:** Python · FastAPI · aiosqlite · PyJWT · Pydantic

**Project URL:** https://github.com/trippusultan/expense-tracker

---

## How to run

```bash
# install dependencies
pip install -r requirements.txt

# dev server (auto-reload)
python run.py

# production
uvicorn main:app --host 0.0.0.0 --port 8001
```

The SQLite database is created automatically at `data/expense.db` on first launch.

---

## Authentication

JWT tokens are issued at `POST /auth/register` and `POST /auth/login`.
Pass the token as an `Authorization: Bearer <token>` header on every
expense endpoint.

### Register

```http
POST /auth/register
Content-Type: application/json

{ "username": "alice", "email": "alice@example.com", "password": "secret123" }
```

### Login

```http
POST /auth/login
Content-Type: application/json

{ "username": "alice", "password": "secret123" }
```

Response:

```json
{ "access_token": "<JWT>", "token_type": "bearer" }
```

---

## Expense endpoints

All paths below require `Authorization: Bearer <token>`.

### List expenses

```http
GET /expenses
GET /expenses?period=week
GET /expenses?period=month
GET /expenses?period=3months
GET /expenses?start_date=2026-01-01&end_date=2026-05-17
GET /expenses?category=Groceries&period=month
```

| Query param | Description |
|---|---|
| `period` | Shortcut: `week` (last 7 d), `month` (last 30 d), `3months` (last 90 d) |
| `start_date` | Inclusive lower bound `YYYY-MM-DD` |
| `end_date` | Inclusive upper bound `YYYY-MM-DD` |
| `category` | One of the 7 categories (see below) |
| `skip` | Offset for pagination |
| `limit` | Page size (1–500) |

```json
{
  "total": 5,
  "expenses": [
    {
      "id": 1,
      "amount": 12.50,
      "category": "Groceries",
      "description": "Apples and bread",
      "date": "2026-05-15",
      "user_id": 1,
      "created_at": "2026-05-15T10:30:00",
      "updated_at": "2026-05-15T10:30:00"
    }
  ]
}
```

### Create expense

```http
POST /expenses
Content-Type: application/json

{
  "amount": 12.50,
  "category": "Groceries",
  "description": "Apples and bread",
  "date": "2026-05-17"
}
```

Returns the created record with `201` status.

### Update expense

```http
PUT /expenses/1
Content-Type: application/json

{ "amount": 15.00, "category": "Groceries", "description": "Apples, bread & milk", "date": "2026-05-17" }
```

### Delete expense

```http
DELETE /expenses/1
```

---

## Expense categories

`Groceries` · `Leisure` · `Electronics` · `Utilities` · `Clothing` · `Health` · `Others`

---

## Verify with curl

```bash
# 1 — register
curl -s -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"t@e.com","password":"secret123"}'

# 2 — login (save the token)
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"secret123"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 3 — create expense
curl -s -X POST http://localhost:8001/expenses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":99.99,"category":"Electronics","description":"Headphones"}'

# 4 — list (week)
curl -s "http://localhost:8001/expenses?period=week" -H "Authorization: Bearer $TOKEN"

# 5 — update
curl -s -X PUT http://localhost:8001/expenses/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":79.99,"category":"Electronics","description":"Headphones (discounted)","date":"2026-05-17"}'

# 6 — total list
curl -s "http://localhost:8001/expenses" -H "Authorization: Bearer $TOKEN"

# 7 — delete
curl -s -X DELETE http://localhost:8001/expenses/1 -H "Authorization: Bearer $TOKEN"

# 8 — health
curl -s http://localhost:8001/health
```

---

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | `dev-secret-change-in-production` | JWT signing secret |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/expense.db` | aiosqlite connection URL |
| `HOST` | `0.0.0.0` | uvicorn bind address |
| `PORT` | `8001` | uvicorn listen port |

Generate a strong `SECRET_KEY` before deploying to production.

---

## License

MIT
