import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = "spendly.db"

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
    # Only seed if the database is empty
    with get_db() as conn:
        cursor = conn.execute("SELECT count(*) FROM users")
        if cursor.fetchone()[0] == 0:
            # Demo User
            user = ("Demo User", "demo@spendly.com", generate_password_hash("demo123"))
            conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", user)

            user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()[0]

            # Sample Expenses (8 total)
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

def create_user(name, email, password_hash):
    """Inserts a new user into the database."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
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
