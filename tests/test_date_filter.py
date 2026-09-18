import pytest
from app import app
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    # Use a separate test database to avoid messing with dev data
    import database.db
    original_db_path = database.db.DB_PATH
    database.db.DB_PATH = "test_date_filter.db"

    with app.test_client() as client:
        with app.app_context():
            database.db.init_db()
            database.db.seed_db()
        yield client

    # Cleanup test database and restore original path
    try:
        if os.path.exists("test_date_filter.db"):
            os.remove("test_date_filter.db")
    except PermissionError:
        pass
    database.db.DB_PATH = original_db_path

def test_profile_date_filter(client):
    # Login
    client.post('/login', data={'email': 'demo@spendly.com', 'password': 'demo123'}, follow_redirects=True)
    
    # Test All Time
    resp = client.get('/profile')
    assert resp.status_code == 200
    
    # Test Custom Range (Valid)
    resp = client.get('/profile?date_from=2026-09-01&date_to=2026-09-05')
    assert resp.status_code == 200
    
    # Test Invalid Range (Start > End)
    resp = client.get('/profile?date_from=2026-09-10&date_to=2026-09-01', follow_redirects=True)
    assert b"Start date must be before end date" in resp.data
    
    # Test Malformed Date
    resp = client.get('/profile?date_from=not-a-date')
    assert resp.status_code == 200

