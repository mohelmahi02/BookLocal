def test_register_new_user(client):
    response = client.post("/register", json={
        "name": "Test User",
        "email": "newuser@test.com",
        "password": "securepass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email_rejected(client):
    client.post("/register", json={
        "name": "First User",
        "email": "dupe@test.com",
        "password": "securepass123",
    })
    response = client.post("/register", json={
        "name": "Second User",
        "email": "dupe@test.com",
        "password": "differentpass456",
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_correct_credentials(client):
    client.post("/register", json={
        "name": "Login Test",
        "email": "logintest@test.com",
        "password": "correctpass123",
    })
    response = client.post("/login", json={
        "email": "logintest@test.com",
        "password": "correctpass123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_rejected(client):
    client.post("/register", json={
        "name": "Login Test 2",
        "email": "logintest2@test.com",
        "password": "correctpass123",
    })
    response = client.post("/login", json={
        "email": "logintest2@test.com",
        "password": "wrongpass",
    })
    assert response.status_code == 401


def test_login_nonexistent_user_rejected(client):
    response = client.post("/login", json={
        "email": "doesnotexist@test.com",
        "password": "whatever123",
    })
    assert response.status_code == 401
