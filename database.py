"""
database.py — async aiosqlite layer: users + expenses tables
All schemas, migrations, and query helpers live here.
"""
import aiosqlite
from datetime import datetime
from pathlib import Path
from config import settings

DB_PATH = Path(__file__).parent / "data" / "expense.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ── schema ──────────────────────────────────────────────────────────────────

CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT    NOT NULL UNIQUE,
    email        TEXT    NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL,
    created_at   TEXT    NOT NULL
)
"""

CREATE_EXPENSES = """
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount      REAL    NOT NULL,
    category    TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    date        TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
)
"""


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_USERS)
        await db.execute(CREATE_EXPENSES)
        await db.commit()


# ── raw helpers ──────────────────────────────────────────────────────────────

async def _fetchone(query: str, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await (await db.execute(query, params)).fetchone()
        return dict(row) if row else None


async def _fetchall(query: str, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        return [dict(r) for r in await (await db.execute(query, params)).fetchall()]


async def _execute(query: str, params=()) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor.lastrowid or 0


# ── users ────────────────────────────────────────────────────────────────────

async def create_user(username: str, email: str, hashed_password: str) -> int:
    now = datetime.utcnow().isoformat()
    return await _execute(
        "INSERT INTO users (username, email, hashed_password, created_at) VALUES (?,?,?,?)",
        (username, email, hashed_password, now),
    )


async def get_user_by_username(username: str) -> dict | None:
    return await _fetchone(
        "SELECT * FROM users WHERE username = ?", (username,)
    )


async def get_user_by_id(user_id: int) -> dict | None:
    return await _fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


# ── expenses ─────────────────────────────────────────────────────────────────

async def create_expense(
    user_id: int, amount: float, category: str, description: str, date: str
) -> int:
    now = datetime.utcnow().isoformat()
    return await _execute(
        """INSERT INTO expenses (user_id, amount, category, description, date, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?)""",
        (user_id, amount, category, description, date, now, now),
    )


async def get_expense(user_id: int, expense_id: int) -> dict | None:
    return await _fetchone(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )


async def list_expenses(
    user_id: int,
    category: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params: list = [user_id]

    if category:
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    return await _fetchall(query, tuple(params))


async def count_expenses(user_id: int, category=None, start_date=None, end_date=None) -> int:
    q = "SELECT COUNT(*) AS c FROM expenses WHERE user_id = ?"
    p: list = [user_id]
    if category:
        q += " AND category = ?"; p.append(category)
    if start_date:
        q += " AND date >= ?"; p.append(start_date)
    if end_date:
        q += " AND date <= ?"; p.append(end_date)
    row = await _fetchone(q, tuple(p))
    return row["c"] if row else 0


async def update_expense(
    user_id: int,
    expense_id: int,
    amount: float | None = None,
    category: str | None = None,
    description: str | None = None,
    date: str | None = None,
) -> dict | None:
    fields, params = [], [expense_id, user_id]
    if amount is not None:
        fields.append("amount = ?"); params.append(amount)
    if category is not None:
        fields.append("category = ?"); params.append(category)
    if description is not None:
        fields.append("description = ?"); params.append(description)
    if date is not None:
        fields.append("date = ?"); params.append(date)
    if not fields:
        return await get_expense(user_id, expense_id)
    params.append(datetime.utcnow().isoformat())
    await _execute(
        f"UPDATE expenses SET {', '.join(fields)}, updated_at = ? WHERE id = ? AND user_id = ?",
        tuple(params),
    )
    return await get_expense(user_id, expense_id)


async def delete_expense(user_id: int, expense_id: int) -> bool:
    await _execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, user_id),
    )
    return True
