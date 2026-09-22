import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

# --- Constants ---
VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        conn.commit()

def seed_db():
    """Inserts sample data for development."""
    with get_db() as conn:
        cursor = conn.execute("SELECT count(*) FROM users")
        if cursor.fetchone()[0] == 0:
            user = ("Demo User", "demo@spendly.com", generate_password_hash("demo123"))
            conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", user)
            user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]

            expenses = [
                (user_id, 15.50, "Food", "Lunch", "2026-09-01"),
                (user_id, 10.00, "Transport", "Bus fare", "2026-09-02"),
                (user_id, 100.00, "Bills", "Internet bill", "2026-09-03"),
                (user_id, 45.00, "Health", "Pharmacy", "2026-09-04"),
                (user_id, 20.00, "Entertainment", "Cinema", "2026-09-05"),
                (user_id, 60.00, "Shopping", "New shirt", "2026-09-06"),
                (user_id, 12.00, "Other", "Gift wrap", "2026-09-07"),
                (user_id, 25.00, "Food", "Dinner", "2026-09-08"),
            ]
            conn.executemany("INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)", expenses)
            conn.commit()

def create_user(name, email, password):
    """Hashes password and inserts a new user into the database."""
    password_hash = generate_password_hash(password)
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        conn.commit()
        return cursor.lastrowid

def add_expense(user_id, amount, category, description, date):
    """Inserts a new expense for a specific user."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, description, date)
        )
        conn.commit()
        return cursor.lastrowid

def get_user_by_email(email):
    """Fetches a user by their email address."""
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

def get_user_by_id(user_id):
    """Fetches a user by their ID."""
    with get_db() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

# --- Internal Helpers ---

def _apply_date_filter(user_id, date_from=None, date_to=None):
    """Returns a WHERE clause and parameter list for date filtering."""
    where_clause = "WHERE user_id = ?"
    params = [user_id]
    if date_from:
        where_clause += " AND date >= ?"
        params.append(date_from)
    if date_to:
        where_clause += " AND date <= ?"
        params.append(date_to)
    return where_clause, params

# --- Query Helpers ---

def get_user_details(user_id):
    """Fetches user details and formats the member since date."""
    user = get_user_by_id(user_id)
    if not user:
        return None

    try:
        dt = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        try:
            dt = datetime.strptime(user["created_at"][:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            return {
                "name": user["name"],
                "email": user["email"],
                "member_since": "Unknown"
            }

    return {
        "name": user["name"],
        "email": user["email"],
        "member_since": dt.strftime("%B %Y")
    }

def get_summary_stats(user_id, date_from=None, date_to=None):
    """Calculates total spent, transaction count, and top category."""
    where_clause, params = _apply_date_filter(user_id, date_from, date_to)
    with get_db() as conn:
        totals = conn.execute(
            f"SELECT SUM(amount) as total, COUNT(id) as count FROM expenses {where_clause}",
            params
        ).fetchone()

        total_spent = totals["total"] if totals["total"] is not None else 0.0
        transaction_count = totals["count"] if totals["count"] is not None else 0

        top_cat_row = conn.execute(
            f"SELECT category FROM expenses {where_clause} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            params
        ).fetchone()

        top_category = top_cat_row["category"] if top_cat_row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        }

def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    """Fetches the most recent transactions for a user within a date range."""
    where_clause, params = _apply_date_filter(user_id, date_from, date_to)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT date, description, category, amount FROM expenses {where_clause} ORDER BY date DESC LIMIT ?",
            params + [limit]
        ).fetchall()

        return [
            {
                "date": row["date"],
                "description": row["description"],
                "category": row["category"],
                "amount": row["amount"]
            }
            for row in rows
        ]

def get_category_breakdown(user_id, date_from=None, date_to=None):
    """Calculates spending breakdown by category within a date range."""
    where_clause, params = _apply_date_filter(user_id, date_from, date_to)
    with get_db() as conn:
        total_row = conn.execute(
            f"SELECT SUM(amount) as total FROM expenses {where_clause}",
            params
        ).fetchone()

        grand_total = total_row["total"] if total_row["total"] is not None else 0.0
        if grand_total == 0:
            return []

        rows = conn.execute(
            f"SELECT category, SUM(amount) as total FROM expenses {where_clause} GROUP BY category ORDER BY total DESC",
            params
        ).fetchall()

        breakdown = []
        sum_pct = 0

        for row in rows:
            amount = row["total"]
            pct = round((amount / grand_total) * 100)
            breakdown.append({
                "category": row["category"],
                "amount": amount,
                "percentage": pct
            })
            sum_pct += pct

        if breakdown:
            diff = 100 - sum_pct
            breakdown[0]["percentage"] += diff

        return breakdown
