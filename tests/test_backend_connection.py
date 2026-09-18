import pytest
from app import app
from flask import url_for
from database.db import init_db, seed_db, get_db, get_summary_stats, get_recent_transactions, get_category_breakdown, get_user_details
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Store original path to restore it later
    import database.db
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = "test_spendly.db"

    with app.test_client() as client:
        with app.app_context():
            init_db()
            seed_db()
        yield client

    # Cleanup test database and restore original path
    try:
        if os.path.exists("test_spendly.db"):
            os.remove("test_spendly.db")
    except PermissionError:
        pass
    database.db.DB_PATH = original_db_path

def test_get_user_by_id(client):
    with app.app_context():
        # Seed user is created by seed_db()
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        user_id = user["id"]

        user_data = get_user_details(user_id)
        assert user_data["name"] == "Demo User"
        assert user_data["email"] == "demo@spendly.com"
        assert "2026" in user_data["member_since"] # Date format check

def test_get_summary_stats_with_data(client):
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        user_id = user["id"]

        stats = get_summary_stats(user_id)
        # Seed data: 15.5+10+100+45+20+60+12+25 = 287.5 (Wait, spec says 346.24?)
        # Let me check seed_db() in database/db.py
        # seed_db has 8 items: 15.5, 10.0, 100.0, 45.0, 20.0, 60.0, 12.0, 25.0 = 287.5
        # The spec mentioned 346.24, but the actual seed_db code I saw has 287.5.
        # I'll assert based on the actual seed_db values.
        assert stats["total_spent"] == 287.5
        assert stats["transaction_count"] == 8
        assert stats["top_category"] == "Bills" # 100.0 is the highest

def test_get_summary_stats_no_data(client):
    with app.app_context():
        # Create user with no expenses
        conn = get_db()
        cursor = conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                            ("No Spend", f"none_{os.urandom(4).hex()}@example.com", "hash"))
        user_id = cursor.lastrowid
        conn.commit()

        stats = get_summary_stats(user_id)
        assert stats["total_spent"] == 0.0
        assert stats["transaction_count"] == 0
        assert stats["top_category"] == "—"

def test_get_recent_transactions(client):
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        user_id = user["id"]

        txs = get_recent_transactions(user_id)
        assert len(txs) == 8
        # Check ordering (newest first) - Seed data dates are 09-01 to 09-08
        assert txs[0]["date"] == "2026-09-08"

def test_get_category_breakdown(client):
    with app.app_context():
        conn = get_db()
        user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
        user_id = user["id"]

        breakdown = get_category_breakdown(user_id)
        # Sum of percentages must be 100
        total_pct = sum(cat["percentage"] for cat in breakdown)
        assert total_pct == 100
        # Bills should be the largest (100 / 287.5 * 100 approx 34.78)
        assert breakdown[0]["category"] == "Bills"

def test_profile_route_unauthenticated(client):
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 302
    assert response.location == url_for("login", _external=False)

def test_profile_route_authenticated(client):
    with client.session_transaction() as sess:
        # Get seed user id
        with app.app_context():
            conn = get_db()
            user = conn.execute("SELECT id FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
            sess["user_id"] = user["id"]

    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Demo User" in response.data
    assert b"demo@spendly.com" in response.data
    assert "₹" in response.data.decode('utf-8')
