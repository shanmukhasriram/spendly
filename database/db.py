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
                password TEXT NOT NULL
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
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
            # Sample Users
            users = [
                ("Alice Smith", "alice@example.com", generate_password_hash("password123")),
                ("Bob Jones", "bob@example.com", generate_password_hash("secure456")),
            ]
            conn.executemany("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", users)

            # Get IDs of seeded users
            alice_id = conn.execute("SELECT id FROM users WHERE email = ?", ("alice@example.com",)).fetchone()[0]
            bob_id = conn.execute("SELECT id FROM users WHERE email = ?", ("bob@example.com",)).fetchone()[0]

            # Sample Expenses
            expenses = [
                (alice_id, 50.0, "Food", "Grocery shopping", "2026-09-01"),
                (alice_id, 20.0, "Transport", "Uber to office", "2026-09-02"),
                (bob_id, 1200.0, "Rent", "Monthly rent", "2026-09-01"),
                (bob_id, 15.0, "Entertainment", "Movie ticket", "2026-09-02"),
                (bob_id, 45.0, "Food", "Dinner at restaurant", "2026-09-02"),
            ]
            conn.executemany("INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)", expenses)
            conn.commit()

def create_user(name, email, password_hash):
    """Inserts a new user into the database."""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
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

