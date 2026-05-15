#!/usr/bin/env python3
"""
Expense Tracker CLI
Track add / delete / update / list / summary and monthly budget.
Usage: expense-tracker <command> [options]
"""

import sys
import json
import csv
import os
from datetime import datetime, timezone
from argparse import ArgumentParser, Namespace

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.json")

MONTHS = [
    None, "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


# ── data layer ────────────────────────────────────────────────────────────────

def load_data() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(expenses: list[dict]) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2, default=str)


def next_id(expenses: list[dict]) -> int:
    return max((e["id"] for e in expenses), default=0) + 1


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_add(args: Namespace, expenses: list[dict]) -> None:
    desc = args.description
    if not desc or not desc.strip():
        print("Error: description is required.")
        sys.exit(1)
    amount = args.amount
    if amount <= 0:
        print("Error: amount must be a positive number.")
        sys.exit(1)
    now = datetime.now(timezone.utc)
    expense = {
        "id": next_id(expenses),
        "date": now.strftime("%Y-%m-%d"),
        "description": desc.strip(),
        "amount": round(amount, 2),
        "category": args.category or "general",
    }
    expenses.append(expense)
    save_data(expenses)
    print(f"Expense added successfully (ID: {expense['id']})")


def cmd_delete(args: Namespace, expenses: list[dict]) -> None:
    before = len(expenses)
    expenses[:] = [e for e in expenses if e["id"] != args.id]
    if len(expenses) == before:
        print(f"Error: expense with ID {args.id} does not exist.")
        sys.exit(1)
    save_data(expenses)
    print("Expense deleted successfully")


def cmd_update(args: Namespace, expenses: list[dict]) -> None:
    for e in expenses:
        if e["id"] == args.id:
            if args.description:
                e["description"] = args.description
            if args.amount is not None:
                if args.amount <= 0:
                    print("Error: amount must be a positive number.")
                    sys.exit(1)
                e["amount"] = round(args.amount, 2)
            if args.category is not None:
                e["category"] = args.category
            # refresh date on update
            e["date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            save_data(expenses)
            print(f"Expense {args.id} updated successfully")
            return
    print(f"Error: expense with ID {args.id} does not exist.")
    sys.exit(1)


def cmd_list(args: Namespace, expenses: list[dict]) -> None:
    rows = expenses
    if args.category:
        rows = [e for e in rows if e.get("category", "general") == args.category]
    if not rows:
        print("No expenses found.")
        return
    # table
    print(f"{'ID':>4}  {'Date':<12}  {'Category':<12}  {'Description':<30}  {'Amount'}")
    print("-" * 76)
    for e in sorted(rows, key=lambda x: x["id"]):
        print(
            f"{e['id']:>4}  {e['date']:<12}  {e.get('category','general'):<12}  "
            f"{e['description']:<30}  ${e['amount']:.2f}"
        )


def cmd_summary(args: Namespace, expenses: list[dict]) -> None:
    now = datetime.now()
    target_year = args.year or now.year

    if args.month:
        month_num = args.month
        month_name = MONTHS[month_num]
        filtered = [
            e for e in expenses
            if datetime.strptime(e["date"], "%Y-%m-%d").year == target_year
            and datetime.strptime(e["date"], "%Y-%m-%d").month == month_num
        ]
        total = sum(e["amount"] for e in filtered)
        print(f"Total expenses for {month_name} {target_year}: ${total:.2f}")

        # per-category breakdown
        cats: dict[str, float] = {}
        for e in filtered:
            cats[e.get("category", "general")] = cats.get(e.get("category", "general"), 0) + e["amount"]
        for cat, amt in sorted(cats.items()):
            print(f"  {cat:<15} ${amt:.2f}")

        # budget check
        budget = _get_budget(month_num, target_year)
        if budget > 0:
            pct = (total / budget) * 100
            remaining = budget - total
            print(f"\nBudget: ${budget:.2f}  |  Spent: ${total:.2f}  |  Remaining: ${remaining:.2f}  ({pct:.1f}%)")
            if total >= budget:
                print("⚠️  Budget exceeded!")
            elif pct >= 90:
                print("⚠️  Warning: you have reached 90% of your budget!")

    else:
        total = sum(e["amount"] for e in expenses)
        print(f"Total expenses: ${total:.2f}")

        # per-category breakdown
        cats: dict[str, float] = {}
        for e in expenses:
            cats[e.get("category", "general")] = cats.get(e.get("category", "general"), 0) + e["amount"]
        for cat, amt in sorted(cats.items()):
            print(f"  {cat:<15} ${amt:.2f}")


def cmd_export(args: Namespace, expenses: list[dict]) -> None:
    path = args.output or "expenses.csv"
    rows = expenses
    if args.category:
        rows = [e for e in rows if e.get("category", "general") == args.category]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "date", "description", "amount", "category"])
        writer.writeheader()
        for e in sorted(rows, key=lambda x: x["id"]):
            writer.writerow({
                "id": e["id"],
                "date": e["date"],
                "description": e["description"],
                "amount": e["amount"],
                "category": e.get("category", "general"),
            })
    print(f"Exported {len(rows)} expenses to {path}")


def cmd_budget(args: Namespace) -> None:
    """Set budget for a month: --month N --amount N | show all budgets."""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "budgets.json")
    budgets: dict[str, float] = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            budgets = json.load(f)

    if args.set_budget:
        key = f"{args.year or datetime.now().year}-{str(args.month).zfill(2)}"
        budgets[key] = args.set_budget
        with open(config_path, "w") as f:
            json.dump(budgets, f, indent=2)
        month_name = MONTHS[args.month]
        print(f"Budget set for {month_name} {args.year or datetime.now().year}: ${args.set_budget:.2f}")
        return

    # show all
    if not budgets:
        print("No budgets set. Use --set-budget to add one.")
        return
    print(f"{'Month':<20}  {'Budget'}")
    print("-" * 30)
    now = datetime.now()
    for key in sorted(budgets):
        y, m = key.split("-")
        month_name = MONTHS[int(m)]
        print(f"{month_name} {y:<14}  ${budgets[key]:.2f}")


def _get_budget(month: int, year: int) -> float:
    key = f"{year}-{str(month).zfill(2)}"
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "budgets.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return json.load(f).get(key, 0)
    return 0


# ── parser ───────────────────────────────────────────────────────────────────

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="expense-tracker", description="Simple CLI expense tracker")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # add
    p_add = sub.add_parser("add", help="Add an expense")
    p_add.add_argument("--description", "-d", required=True, help="Expense description")
    p_add.add_argument("--amount", "-a", type=float, required=True, help="Expense amount")
    p_add.add_argument("--category", "-c", default="general", help="Category (default: general)")

    # delete
    p_del = sub.add_parser("delete", help="Delete an expense")
    p_del.add_argument("--id", type=int, required=True, help="Expense ID to delete")

    # update
    p_upd = sub.add_parser("update", help="Update an expense")
    p_upd.add_argument("--id", type=int, required=True, help="Expense ID to update")
    p_upd.add_argument("--description", "-d", default=None)
    p_upd.add_argument("--amount", "-a", type=float, default=None)
    p_upd.add_argument("--category", "-c", default=None)

    # list
    p_list = sub.add_parser("list", help="List all expenses")
    p_list.add_argument("--category", "-c", default=None, help="Filter by category")

    # summary
    p_sum = sub.add_parser("summary", help="Show expense summary")
    p_sum.add_argument("--month", type=int, choices=range(1, 13), default=None,
                       help="Month number (1-12)")
    p_sum.add_argument("--year", type=int, default=None, help="Year (default: current)")

    # export
    p_exp = sub.add_parser("export", help="Export expenses to CSV")
    p_exp.add_argument("--output", "-o", default="expenses.csv",
                       help="Output file path (default: expenses.csv)")
    p_exp.add_argument("--category", "-c", default=None, help="Filter by category")

    # budget
    p_bud = sub.add_parser("budget", help="Set or view monthly budgets")
    p_bud.add_argument("--month", type=int, choices=range(1, 13), required=True)
    p_bud.add_argument("--year", type=int, default=datetime.now().year)
    p_bud.add_argument("--set-budget", type=float, default=None,
                       help="Set budget amount for the given month")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    expenses = load_data()

    dispatch = {
        "add": cmd_add,
        "delete": cmd_delete,
        "update": cmd_update,
        "list": cmd_list,
        "summary": cmd_summary,
        "export": cmd_export,
    }
    cmd = dispatch.get(args.command)
    if cmd:
        cmd(args, expenses)
    elif args.command == "budget":
        cmd_budget(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
