from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import (
    create_user,
    get_user_by_email,
    init_db,
    seed_db,
    get_user_details,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    add_expense as db_add_expense,
    VALID_CATEGORIES
)
from datetime import datetime, timedelta

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
@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile():
    user_id = session["user_id"]

    # --- DATE FILTERING LOGIC ---
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    
    # Validate dates
    try:
        if date_from:
            datetime.strptime(date_from, "%Y-%m-%d")
        if date_to:
            datetime.strptime(date_to, "%Y-%m-%d")
            
        if date_from and date_to and date_from > date_to:
            flash("Start date must be before end date", "error")
            return redirect(url_for("profile"))

    except ValueError:
        date_from, date_to = None, None

    # User Info
    user_raw = get_user_details(user_id)
    if not user_raw:
        session.clear()
        flash("Your session has expired or the account was removed.", "error")
        return redirect(url_for("login"))

    user_data = {
        "name": user_raw["name"],
        "email": user_raw["email"],
        "member_since": user_raw["member_since"],
        "initials": "".join([n[0].upper() for n in user_raw["name"].split()])
    }

    # --- START SUMMARY STATS ---
    stats_raw = get_summary_stats(user_id, date_from, date_to)
    stats_data = {
        "total_spent": f"₹{stats_raw['total_spent']:,.2f}",
        "transaction_count": stats_raw["transaction_count"],
        "top_category": stats_raw["top_category"]
    }
    # --- END SUMMARY STATS ---

    # --- START TRANSACTIONS ---
    tx_raw = get_recent_transactions(user_id, date_from=date_from, date_to=date_to)
    transactions_data = [
        {
            "date": tx["date"],
            "description": tx["description"],
            "category": tx["category"],
            "amount": f"₹{tx['amount']:,.2f}"
        }
        for tx in tx_raw
    ]
    # --- END TRANSACTIONS ---

    # --- START CATEGORIES ---
    cat_raw = get_category_breakdown(user_id, date_from, date_to)
    categories_data = [
        {
            "category": cat["category"],
            "amount": f"₹{cat['amount']:,.2f}",
            "percentage": cat["percentage"]
        }
        for cat in cat_raw
    ]
    # --- END CATEGORIES ---

    # --- PRESET CALCULATION ---
    today = datetime.now().date()
    
    # This Month
    first_of_month = today.replace(day=1)
    this_month_url = url_for("profile", date_from=first_of_month.strftime("%Y-%m-%d"), date_to=today.strftime("%Y-%m-%d"))
    
    # Last 3 Months
    three_months_ago = today - timedelta(days=90)
    three_months_url = url_for("profile", date_from=three_months_ago.strftime("%Y-%m-%d"), date_to=today.strftime("%Y-%m-%d"))
    
    # Last 6 Months
    six_months_ago = today - timedelta(days=180)
    six_months_url = url_for("profile", date_from=six_months_ago.strftime("%Y-%m-%d"), date_to=today.strftime("%Y-%m-%d"))
    
    # All Time
    all_time_url = url_for("profile")
    
    presets = [
        {"label": "This Month", "url": this_month_url, "active": (date_from == first_of_month.strftime("%Y-%m-%d") and date_to == today.strftime("%Y-%m-%d"))},
        {"label": "Last 3 Months", "url": three_months_url, "active": (date_from == three_months_ago.strftime("%Y-%m-%d") and date_to == today.strftime("%Y-%m-%d"))},
        {"label": "Last 6 Months", "url": six_months_url, "active": (date_from == six_months_ago.strftime("%Y-%m-%d") and date_to == today.strftime("%Y-%m-%d"))},
        {"label": "All Time", "url": all_time_url, "active": (not date_from and not date_to)},
    ]

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats_data,
        transactions=transactions_data,
        categories=categories_data,
        presets=presets,
        date_from=date_from,
        date_to=date_to
    )

@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount_str = request.form.get("amount")
        category = request.form.get("category")
        description = request.form.get("description", "").strip()
        date = request.form.get("date")

        # Validation
        errors = []

        # Amount validation
        try:
            amount = float(amount_str)
            if amount <= 0:
                errors.append("Amount must be greater than 0")
        except (TypeError, ValueError):
            errors.append("Amount must be a valid number")

        # Category validation
        if not category or category not in VALID_CATEGORIES:
            errors.append("Please select a valid category")

        # Date validation
        try:
            if not date:
                raise ValueError
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            errors.append("Please provide a valid date")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_expense.html",
                                    amount=amount_str,
                                    category=category,
                                    description=description,
                                    date=date,
                                    categories=VALID_CATEGORIES)

        try:
            # Store NULL for blank description
            final_desc = description if description else None
            db_add_expense(session["user_id"], amount, category, final_desc, date)
            flash("Expense added successfully!", "success")
            return redirect(url_for("profile"))
        except sqlite3.Error as e:
            flash(f"Database error: {str(e)}", "error")
            return render_template("add_expense.html",
                                    amount=amount_str,
                                    category=category,
                                    description=description,
                                    date=date,
                                    categories=VALID_CATEGORIES)

    return render_template("add_expense.html", categories=VALID_CATEGORIES)


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
