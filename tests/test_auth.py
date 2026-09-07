import pytest
from app import app
from database.db import init_db, get_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-key'
    with app.test_client() as client:
        with app.app_context():
            init_db()
            with get_db() as conn:
                conn.execute("DELETE FROM expenses")
                conn.execute("DELETE FROM users")
                conn.commit()
        yield client

def test_register(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login
    assert b"Sign in" in response.data

def test_login(client):
    # Register first
    reg_response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert b"Account created successfully" in reg_response.data

    # Login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    })

    assert response.status_code == 302
    assert response.headers['Location'] == '/profile'

    # Now follow to profile
    response = client.get('/profile', follow_redirects=True)
    assert response.status_code == 200
    assert b"Profile page" in response.data

def test_login_invalid(client):
    # Register first
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    # Login with wrong password
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)

    assert b"Invalid email or password" in response.data

def test_profile_protected(client):
    response = client.get('/profile', follow_redirects=True)
    # Should redirect to login
    assert b"Sign in" in response.data

def test_logout(client):
    # Register and login
    client.post('/register', data={
        'name': 'Test User',
        'email': 'logout@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.post('/login', data={
        'email': 'logout@example.com',
        'password': 'password123'
    })

    # Logout
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"You have been logged out successfully" in response.data

    # Verify profile is now protected again
    response = client.get('/profile', follow_redirects=True)
    assert b"Sign in" in response.data

def test_logout_unauthorized(client):
    # Attempt to logout without being logged in
    response = client.get('/logout', follow_redirects=True)
    assert b"Sign in" in response.data
