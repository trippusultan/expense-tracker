"""
main.py — FastAPI Expense Tracker: auth + CRUD + date-range filters
"""
import hashlib
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field

from auth import create_access_token, decode_token
from config import settings
from database import (
    count_expenses,
    create_expense,
    create_user,
    delete_expense,
    get_expense,
    get_user_by_username,
    init_db,
    list_expenses,
    update_expense,
)

# ── app setup ────────────────────────────────────────────────────────────────

app = FastAPI(title="Expense Tracker API", version="1.0.0")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)

VALID_CATEGORIES = {
    "Groceries", "Leisure", "Electronics",
    "Utilities", "Clothing", "Health", "Others",
}


@app.on_event("startup")
async def startup() -> None:
    await init_db()


# ── helpers ──────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


async def current_user(token: str | None = Depends(oauth2_scheme)) -> dict:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = await get_user_by_username(payload.get("sub", ""))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _today_iso() -> str:
    return date.today().isoformat()


def _week_ago_iso() -> str:
    return (date.today() - timedelta(days=7)).isoformat()


def _month_ago_iso() -> str:
    return (date.today() - timedelta(days=30)).isoformat()


def _three_months_ago_iso() -> str:
    return (date.today() - timedelta(days=90)).isoformat()


# ── schemas ──────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=120)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ExpenseIn(BaseModel):
    amount: float = Field(..., gt=0)
    category: Literal[
        "Groceries", "Leisure", "Electronics",
        "Utilities", "Clothing", "Health", "Others",
    ]
    description: str = Field(default="", max_length=500)
    date: str = Field(default_factory=_today_iso)  # YYYY-MM-DD


class ExpenseOut(ExpenseIn):
    id: int
    user_id: int
    created_at: str
    updated_at: str


class ExpenseListOut(BaseModel):
    total: int
    expenses: list[ExpenseOut]


# ── auth routes ──────────────────────────────────────────────────────────────

@app.post(
    "/auth/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(body: UserRegister):
    existing = await get_user_by_username(body.username)
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already taken")
    hashed = _hash_password(body.password)
    await create_user(body.username, body.email, hashed)
    return {"ok": True, "message": f"User '{body.username}' registered successfully"}


@app.post("/auth/login", response_model=TokenOut, summary="Log in and get a JWT")
async def login(body: UserLogin):
    user = await get_user_by_username(body.username)
    if not user or user["hashed_password"] != _hash_password(body.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"]})
    return TokenOut(access_token=token)


# ── expense CRUD ─────────────────────────────────────────────────────────────

@app.get(
    "/expenses",
    response_model=ExpenseListOut,
    summary="List expenses (filterable by date range & category)",
)
async def get_expenses(
    category: str | None = Query(None),
    start_date: str | None = Query(None, description="YYYY-MM-DD filter (inclusive)"),
    end_date: str | None = Query(None, description="YYYY-MM-DD filter (inclusive)"),
    period: Literal["week", "month", "3months"] | None = Query(
        None, description="Shortcut: week / month / 3months"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user: dict = Depends(current_user),
):
    if period:
        if period == "week":
            start_date = _week_ago_iso()
        elif period == "month":
            start_date = _month_ago_iso()
        elif period == "3months":
            start_date = _three_months_ago_iso()
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}",
        )
    rows = await list_expenses(
        user["id"], category=category, start_date=start_date, end_date=end_date,
        skip=skip, limit=limit,
    )
    total = await count_expenses(
        user["id"], category=category, start_date=start_date, end_date=end_date,
    )
    return ExpenseListOut(total=total, expenses=rows)


@app.post(
    "/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
)
async def post_expense(body: ExpenseIn, user: dict = Depends(current_user)):
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}",
        )
    expense_id = await create_expense(
        user_id=user["id"],
        amount=body.amount,
        category=body.category,
        description=body.description,
        date=body.date,
    )
    return await get_expense(user["id"], expense_id)


@app.put(
    "/expenses/{expense_id}",
    response_model=ExpenseOut,
    summary="Update an existing expense",
)
async def put_expense(
    expense_id: int,
    body: ExpenseIn,
    user: dict = Depends(current_user),
):
    existing = await get_expense(user["id"], expense_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Expense not found")
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Choose from: {', '.join(VALID_CATEGORIES)}",
        )
    updated = await update_expense(
        user["id"], expense_id,
        amount=body.amount,
        category=body.category,
        description=body.description,
        date=body.date,
    )
    return updated


@app.delete(
    "/expenses/{expense_id}",
    summary="Delete an expense",
)
async def del_expense(expense_id: int, user: dict = Depends(current_user)):
    existing = await get_expense(user["id"], expense_id)
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Expense not found")
    await delete_expense(user["id"], expense_id)
    return {"ok": True, "message": f"Expense {expense_id} deleted"}


@app.get("/health", summary="Health check")
async def health():
    return {"ok": True, "service": "expense-tracker", "version": "1.0.0"}
