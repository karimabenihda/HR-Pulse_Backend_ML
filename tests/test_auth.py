from fastapi.testclient import TestClient
from app.main import app

# Create the fake client
client = TestClient(app)
def test_signup(setup_database):
    """Test signup endpoint"""
    response = client.post("/signup", json={
        "firstname": "John",
        "lastname": "Doe",
        "email": "john@example.com",
        "password": "test123"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["user"]["email"] == "john@example.com"
    
def test_login(setup_database):
    """Test login endpoint"""
    # Create user
    client.post("/signup", json={
        "firstname": "John",
        "lastname": "Doe",
        "email": "john@example.com",
        "password": "test123"
    })
    
    # Login
    response = client.post("/login", json={
        "email": "john@example.com",
        "password": "test123"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["user"]["email"] == "john@example.com"
