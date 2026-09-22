import pytest
import os
from app import app as flask_app
from database.db import init_db, get_db
import database.db

@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
        'WTF_CSRF_ENABLED': False,
    })

    # Use a dedicated test database file to avoid polluting dev data
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = "test_add_expense.db"

    with flask_app.app_context():
        init_db()
        yield flask_app

    # Cleanup test database and restore original path
    try:
        if os.path.exists("test_add_expense.db"):
            os.remove("test_add_expense.db")
    except PermissionError:
        pass
    database.db.DB_PATH = original_db_path

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """A test client that is already logged in."""
    # Register and login using the correct fields from the implementation
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass',
        'confirm_password': 'testpass'
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass'
    })
    return client

class TestAddExpense:

    # --- Auth Guards ---

    def test_get_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.get('/expenses/add')
        assert response.status_code == 302
        assert response.location.endswith('/login')

    def test_post_add_expense_unauthenticated_redirects_to_login(self, client):
        response = client.post('/expenses/add', data={'amount': '10.0', 'category': 'Food', 'date': '2026-01-01'})
        assert response.status_code == 302
        assert response.location.endswith('/login')

    # --- UI / GET Requests ---

    def test_get_add_expense_authenticated_renders_form(self, auth_client):
        response = auth_client.get('/expenses/add')
        assert response.status_code == 200
        assert b'<form' in response.data
        assert b'method="POST"' in response.data

        # Verify the 7 fixed categories
        categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
        for cat in categories:
            assert cat.encode() in response.data

        # Ensure it is a select dropdown
        assert b'<select' in response.data

    # --- Happy Path ---

    def test_post_add_expense_valid_data_success(self, auth_client, app):
        data = {
            'amount': '50.0',
            'category': 'Food',
            'date': '2026-03-20',
            'description': 'Lunch'
        }
        response = auth_client.post('/expenses/add', data=data, follow_redirects=False)

        # Check redirect to profile
        assert response.status_code == 302
        assert response.location.endswith('/profile')

        # Verify DB insertion
        with app.app_context():
            db = get_db()
            row = db.execute('SELECT amount, category, date, description FROM expenses').fetchone()
            assert row is not None
            assert float(row['amount']) == 50.0
            assert row['category'] == 'Food'
            assert row['date'] == '2026-03-20'
            assert row['description'] == 'Lunch'

    def test_post_add_expense_no_description_saves_as_null(self, auth_client, app):
        data = {
            'amount': '20.0',
            'category': 'Transport',
            'date': '2026-03-21',
            'description': '' # Optional field
        }
        response = auth_client.post('/expenses/add', data=data, follow_redirects=False)

        assert response.status_code == 302

        with app.app_context():
            db = get_db()
            # Order by id DESC to get the most recently inserted record
            row = db.execute('SELECT description FROM expenses ORDER BY id DESC LIMIT 1').fetchone()
            assert row['description'] is None  # Should be stored as NULL in SQLite

    # --- Validation Errors ---

    @pytest.mark.parametrize("amount, category, date, description", [
        # Missing amount
        ('', 'Food', '2026-01-01', 'Test'),
        # Zero amount
        ('0', 'Food', '2026-01-01', 'Test'),
        # Negative amount
        ('-10', 'Food', '2026-01-01', 'Test'),
        # Non-numeric amount
        ('abc', 'Food', '2026-01-01', 'Test'),
        # Missing category
        ('10', '', '2026-01-01', 'Test'),
        # Invalid category
        ('10', 'Luxury', '2026-01-01', 'Test'),
        # Missing date
        ('10', 'Food', '', 'Test'),
        # Invalid date format
        ('10', 'Food', '01-01-2026', 'Test'),
        ('10', 'Food', 'not-a-date', 'Test'),
    ])
    def test_post_add_expense_validation_errors(self, auth_client, amount, category, date, description):
        data = {
            'amount': amount,
            'category': category,
            'date': date,
            'description': description
        }
        response = auth_client.post('/expenses/add', data=data)

        # Should re-render the form (200 OK), not redirect (302)
        assert response.status_code == 200
        # Response should contain an error message (usually flashed or in a div)
        assert b'error' in response.data.lower() or b'invalid' in response.data.lower()

        # Check that previously submitted values are retained in the form inputs
        if amount and amount != 'Luxury': # Category is handled separately
            assert amount.encode() in response.data
        if category and category in ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]:
            assert category.encode() in response.data
        if date:
            assert date.encode() in response.data
