FULL_WEEK = [
    {"day_of_week": d, "opening_time": "09:00", "closing_time": "17:00"} for d in range(7)
]
SLOT = "2026-11-07T10:00:00"


def make_user(client, email, name="Test User"):
    client.post("/register", json={"name": name, "email": email, "password": "testpass123"})
    r = client.post("/login", json={"email": email, "password": "testpass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def setup_business(client, email="owner1@test.com", name="Test Cuts"):
    owner = make_user(client, email)
    client.post("/owner/business", headers=owner, json={"name": name, "category": "barber"})
    service = client.post("/owner/services", headers=owner,
                          json={"name": "Haircut", "price": 20, "duration_minutes": 30}).json()
    client.put("/owner/hours", headers=owner, json=FULL_WEEK)
    return owner, service


def guest_book(client, slug, service_id, start_time=SLOT, name="Gary Guest",
               email="gary@example.com", phone="0871234567"):
    return client.post(f"/public/businesses/{slug}/bookings", json={
        "service_id": service_id,
        "start_time": start_time,
        "name": name,
        "email": email,
        "phone": phone,
    })


def test_guest_can_book_without_account(client):
    owner, service = setup_business(client)
    r = guest_book(client, "test-cuts", service["id"])
    assert r.status_code == 201
    data = r.json()
    assert data["status"] == "confirmed"
    assert len(data["cancel_token"]) >= 16


def test_owner_sees_guest_booking_with_phone(client):
    owner, service = setup_business(client)
    guest_book(client, "test-cuts", service["id"])
    rows = client.get("/owner/bookings", headers=owner).json()
    assert len(rows) == 1
    assert rows[0]["customer_name"] == "Gary Guest"
    assert rows[0]["customer_email"] == "gary@example.com"
    assert rows[0]["customer_phone"] == "0871234567"


def test_guest_double_booking_rejected(client):
    owner, service = setup_business(client)
    assert guest_book(client, "test-cuts", service["id"]).status_code == 201
    second = guest_book(client, "test-cuts", service["id"], name="Other", email="o@example.com")
    assert second.status_code == 409


def test_guest_booking_outside_hours_rejected(client):
    owner, service = setup_business(client)
    r = guest_book(client, "test-cuts", service["id"], start_time="2026-11-07T20:00:00")
    assert r.status_code == 400


def test_guest_booking_validation(client):
    owner, service = setup_business(client)
    assert guest_book(client, "test-cuts", service["id"], email="not-an-email").status_code == 400
    assert guest_book(client, "no-such-business", service["id"]).status_code == 404
    assert guest_book(client, "test-cuts", 99999).status_code == 404


def test_guest_cannot_use_another_businesses_service(client):
    owner1, service1 = setup_business(client, "owner1@test.com", "Test Cuts")
    owner2, service2 = setup_business(client, "owner2@test.com", "Other Place")
    r = guest_book(client, "other-place", service1["id"])
    assert r.status_code == 404


def test_guest_cancel_with_token_frees_the_slot(client):
    owner, service = setup_business(client)
    token = guest_book(client, "test-cuts", service["id"]).json()["cancel_token"]

    assert client.delete(f"/public/bookings/{token}").status_code == 200

    again = guest_book(client, "test-cuts", service["id"], name="Next", email="n@example.com")
    assert again.status_code == 201


def test_guest_cancel_unknown_token_404(client):
    assert client.delete("/public/bookings/not-a-real-token").status_code == 404


def test_owner_can_edit_service(client):
    owner, service = setup_business(client)
    r = client.put(f"/owner/services/{service['id']}", headers=owner,
                   json={"name": "Skin fade", "price": 25, "duration_minutes": 45})
    assert r.status_code == 200
    assert r.json()["name"] == "Skin fade"
    assert r.json()["price"] == 25
    listed = client.get("/owner/services", headers=owner).json()
    assert listed[0]["duration_minutes"] == 45


def test_owner_cannot_edit_another_owners_service(client):
    owner1, service1 = setup_business(client, "owner1@test.com", "Test Cuts")
    owner2, service2 = setup_business(client, "owner2@test.com", "Other Place")
    r = client.put(f"/owner/services/{service1['id']}", headers=owner2,
                   json={"name": "Hacked", "price": 1, "duration_minutes": 30})
    assert r.status_code == 404
