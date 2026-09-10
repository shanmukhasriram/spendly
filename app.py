from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import create_user, get_user_by_email, init_db, seed_db

from functools import wraps

app = Flask(__name__)
app.secret_key = "spendly-super-secret-key"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not all([name, email, password, confirm_password]):
            flash("All fields are required", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must be at least 8 characters long", "error")
            return redirect(url_for("register"))

        try:
            create_user(name, email, password)
            flash("Account created successfully! Please sign in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered", "error")
            return redirect(url_for("register"))
        except Exception as e:
            flash(f"An unexpected error occurred: {str(e)}", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = get_user_by_email(email)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("profile"))

        flash("Invalid email or password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    # Hardcoded data for Step 04 Design
    user_data = {
        "name": "Shanmukha Sriram",
        "email": "shanmukha@example.com",
        "member_since": "January 2026",
        "initials": "SS"
    }

    stats_data = {
        "total_spent": "₹12,450.00",
        "transaction_count": 42,
        "top_category": "Food"
    }

    transactions_data = [
        {"date": "2026-09-10", "description": "Organic Grocery Store", "category": "Food", "amount": "₹1,200.00"},
        {"date": "2026-09-09", "description": "Monthly Internet Bill", "category": "Bills", "amount": "₹999.00"},
        {"date": "2026-09-08", "description": "Fuel Refill", "category": "Transport", "amount": "₹2,500.00"},
        {"date": "2026-09-07", "description": "Movie Ticket", "category": "Entertainment", "amount": "₹450.00"},
        {"date": "2026-09-06", "description": "Pharmacy Store", "category": "Health", "amount": "₹800.00"},
    ]

    categories_data = [
        {"category": "Food", "amount": "₹4,500", "percentage": 36},
        {"category": "Transport", "amount": "₹3,200", "percentage": 26},
        {"category": "Bills", "amount": "₹2,100", "percentage": 17},
        {"category": "Entertainment", "amount": "₹1,250", "percentage": 10},
        {"category": "Health", "amount": "₹1,400", "percentage": 11},
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats_data,
        transactions=transactions_data,
        categories=categories_data
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    with app.app_context():
        init_db()
        seed_db()
    app.run(debug=True, port=5001)
