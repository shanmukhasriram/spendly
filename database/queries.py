import sqlite3
from datetime import datetime
from database.db import get_db

def get_user_by_id(user_id):
    """Fetches user details and formats the member since date."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not row:
            return None

        # Format created_at (YYYY-MM-DD HH:MM:SS) to "Month YYYY"
        try:
            dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            # Fallback if date is just YYYY-MM-DD or None
            try:
                dt = datetime.strptime(row["created_at"][:10], "%Y-%m-%d")
            except (ValueError, TypeError):
                return {
                    "name": row["name"],
                    "email": row["email"],
                    "member_since": "Unknown"
                }

        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": dt.strftime("%B %Y")
        }

def get_summary_stats(user_id):
    """Calculates total spent, transaction count, and top category."""
    with get_db() as conn:
        # Totals
        totals = conn.execute(
            "SELECT SUM(amount) as total, COUNT(id) as count FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        total_spent = totals["total"] if totals["total"] is not None else 0.0
        transaction_count = totals["count"] if totals["count"] is not None else 0

        # Top Category
        top_cat_row = conn.execute(
            "SELECT category FROM expenses WHERE user_id = ? GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
            (user_id,)
        ).fetchone()

        top_category = top_cat_row["category"] if top_cat_row else "—"

        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        }

def get_recent_transactions(user_id, limit=10):
    """Fetches the most recent transactions for a user."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT ?",
            (user_id, limit)
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

def get_category_breakdown(user_id):
    """Calculates spending breakdown by category with rounded percentages."""
    with get_db() as conn:
        # Get total spending first
        total_row = conn.execute(
            "SELECT SUM(amount) as total FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        grand_total = total_row["total"] if total_row["total"] is not None else 0.0
        if grand_total == 0:
            return []

        # Get totals per category
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,)
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

        # Adjust the largest category to ensure the sum is exactly 100%
        if breakdown:
            diff = 100 - sum_pct
            breakdown[0]["percentage"] += diff

        return breakdown
