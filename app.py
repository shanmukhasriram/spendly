from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import create_user, get_user_by_email, init_db, seed_db
from database import queries


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
    user_id = session["user_id"]

    # User Info
    user_raw = queries.get_user_by_id(user_id)
    user_data = {
        "name": user_raw["name"],
        "email": user_raw["email"],
        "member_since": user_raw["member_since"],
        "initials": "".join([n[0].upper() for n in user_raw["name"].split()])
    }

    # --- START SUMMARY STATS ---
    stats_raw = queries.get_summary_stats(user_id)
    stats_data = {
        "total_spent": f"₹{stats_raw['total_spent']:,.2f}",
        "transaction_count": stats_raw["transaction_count"],
        "top_category": stats_raw["top_category"]
    }
    # --- END SUMMARY STATS ---

    # --- START TRANSACTIONS ---
    tx_raw = queries.get_recent_transactions(user_id)
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
    cat_raw = queries.get_category_breakdown(user_id)
    categories_data = [
        {
            "category": cat["category"],
            "amount": f"₹{cat['amount']:,.2f}",
            "percentage": cat["percentage"]
        }
        for cat in cat_raw
    ]
    # --- END CATEGORIES ---

    return render_template(
        "profile.html",
        user=user_data,
        stats=stats_data,
        transactions=transactions_data,
        categories=categories_data
    )


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        amount = request.form.get("amount")
        category = request.form.get("category")
        description = request.form.get("description")
        date = request.form.get("date")

        if not all([amount, category, description, date]):
            flash("All fields are required", "error")
            return redirect(url_for("add_expense"))

        try:
            from database.db import add_expense as db_add_expense
            db_add_expense(session["user_id"], float(amount), category, description, date)
            flash("Expense added successfully!", "success")
            return redirect(url_for("profile"))
        except ValueError:
            flash("Invalid amount entered", "error")
            return redirect(url_for("add_expense"))
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("add_expense"))

    return render_template("add_expense.html")


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
