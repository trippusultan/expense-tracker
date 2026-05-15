# Expense Tracker CLI

Track your finances directly from the terminal — add, delete, update, list, and summarize expenses with monthly budgets and CSV export.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📋 Project

Part of the [Expense Tracker](https://roadmap.sh/projects/expense-tracker) project challenge on **roadmap.sh**.

---

## ✨ Features

| Feature | Status |
|---|---|
| Add expense (description + amount + category) | ✅ |
| Delete expense by ID | ✅ |
| Update expense by ID | ✅ |
| List all expenses (table view) | ✅ |
| Filter list by category | ✅ |
| Total summary | ✅ |
| Monthly summary with per-category breakdown | ✅ |
| Monthly budget (set + warning at 90% / exceeded) | ✅ |
| Export to CSV | ✅ |
| Zero external dependencies | ✅ |

---

## 🚀 Installation

Just Python 3.8+. No `pip install` needed.

```bash
git clone https://github.com/trippusultan/expense-tracker.git
cd expense-tracker
```

---

## 🛠 Usage

```bash
python3 expense-tracker.py <command> [options]
```

| Command | Flags |
|---|---|
| `add` | `--description`, `--amount`, `--category` |
| `delete` | `--id` |
| `update` | `--id`, `--description`, `--amount`, `--category` |
| `list` | `--category` |
| `summary` | `--month` (1–12), `--year` |
| `export` | `--output <file.csv>`, `--category` |
| `budget` | `--month`, `--year`, `--set-budget <amount>` |

---

## 📖 Examples

```bash
# Add expenses
python3 expense-tracker.py add --description "Lunch" --amount 20
python3 expense-tracker.py add --description "Dinner" --amount 10 --category food
python3 expense-tracker.py add --description "Uber" --amount 15 --category transport

# List all
python3 expense-tracker.py list

# List filtered by category
python3 expense-tracker.py list --category food

# Total summary
python3 expense-tracker.py summary

# Monthly summary
python3 expense-tracker.py summary --month 5

# Delete
python3 expense-tracker.py delete --id 2

# Update
python3 expense-tracker.py update --id 1 --amount 25 --description "Lunch"

# Export to CSV
python3 expense-tracker.py export
python3 expense-tracker.py export --output my-expenses.csv --category food

# Set a monthly budget
python3 expense-tracker.py budget --month 5 --set-budget 100
# Shows warnings when you exceed 90% or overspend in monthly summary
```

---

## 📊 Output

### `list`

```
  ID  Date          Category      Description                     Amount
----------------------------------------------------------------------------
   1  2026-05-15    general       Lunch                           $20.00
   2  2026-05-15    food          Coffee                          $5.50
```

### `summary`

```
Total expenses: $100.00
  general         $20.00
  housing         $80.00

Budget: $100.00  |  Spent: $100.00  |  Remaining: $0.00  (100.0%)
⚠️  Budget exceeded!
```

### `summary --month 5`

```
Total expenses for May 2026: $100.00
  general         $20.00
  housing         $80.00

Budget: $100.00  |  Spent: $100.00  |  Remaining: $0.00  (100.0%)
⚠️  Budget exceeded!
```

---

## 📁 Data Storage

- **Expenses:** `expenses.json` (same directory as the script)
- **Budgets:** `budgets.json` (same directory as the script)

Both track data by default within the script folder — just commit or back up the whole project directory.

---

## ⚠️ Error Handling

| Scenario | Response |
|---|---|
| Invalid / missing description | `Error: description is required.` |
| Negative / zero amount | `Error: amount must be a positive number.` |
| Non-existent expense ID | `Error: expense with ID X does not exist.` |
| Invalid month number | argparse built-in error |
| No expenses found | `No expenses found.` |

---

## 🔗 Links

- [roadmap.sh Project](https://roadmap.sh/projects/expense-tracker)
- [GitHub Repo](https://github.com/trippusultan/expense-tracker)

---

## 📄 License

MIT
