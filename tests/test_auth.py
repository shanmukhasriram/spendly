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
        yield client

def test_register(client):
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login
    assert b"Sign in" in response.data

def test_login(client):
    # Register first
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Login
    response = client.post('/login', data={
        'email': 'test@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Profile page" in response.data

def test_login_invalid(client):
    # Register first
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123'
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
