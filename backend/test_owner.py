def make_user(client, email, name="Test User"):
    client.post("/register", json={"name": name, "email": email, "password": "testpass123"})
    r = client.post("/login", json={"email": email, "password": "testpass123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def create_business(client, headers, name="Test Cuts"):
    return client.post(
        "/owner/business",
        headers=headers,
        json={"name": name, "category": "barber", "location": "Castlebar"},
    )


FULL_WEEK = [
    {"day_of_week": d, "opening_time": "09:00", "closing_time": "17:00"} for d in range(7)
]


def test_create_business(client):
    h = make_user(client, "owner1@test.com")
    r = create_business(client, h)
    assert r.status_code == 201
    assert r.json()["slug"] == "test-cuts"
    assert r.json()["category"] == "barber"


def test_cannot_create_second_business(client):
    h = make_user(client, "owner1@test.com")
    assert create_business(client, h).status_code == 201
    assert create_business(client, h, name="Another").status_code == 409


def test_slugs_are_unique(client):
    h1 = make_user(client, "owner1@test.com")
    h2 = make_user(client, "owner2@test.com")
    assert create_business(client, h1).json()["slug"] == "test-cuts"
    assert create_business(client, h2).json()["slug"] == "test-cuts-2"


def test_no_business_yet_returns_404(client):
    h = make_user(client, "owner1@test.com")
    assert client.get("/owner/business", headers=h).status_code == 404


def test_add_and_list_services(client):
    h = make_user(client, "owner1@test.com")
    create_business(client, h)
    r = client.post("/owner/services", headers=h,
                    json={"name": "Haircut", "price": 20, "duration_minutes": 30})
    assert r.status_code == 201
    listed = client.get("/owner/services", headers=h).json()
    assert len(listed) == 1
    assert listed[0]["name"] == "Haircut"


def test_set_hours_and_public_page(client):
    h = make_user(client, "owner1@test.com")
    create_business(client, h)
    client.post("/owner/services", headers=h,
                json={"name": "Haircut", "price": 20, "duration_minutes": 30})
    r = client.put("/owner/hours", headers=h, json=FULL_WEEK)
    assert r.status_code == 200
    assert len(r.json()) == 7

    public = client.get("/public/businesses/test-cuts")
    assert public.status_code == 200
    data = public.json()
    assert data["name"] == "Test Cuts"
    assert len(data["services"]) == 1
    assert len(data["hours"]) == 7


def test_hours_validation(client):
    h = make_user(client, "owner1@test.com")
    create_business(client, h)
    bad_order = [{"day_of_week": 0, "opening_time": "17:00", "closing_time": "09:00"}]
    assert client.put("/owner/hours", headers=h, json=bad_order).status_code == 400
    bad_format = [{"day_of_week": 0, "opening_time": "9am", "closing_time": "5pm"}]
    assert client.put("/owner/hours", headers=h, json=bad_format).status_code == 400
    dup_day = [
        {"day_of_week": 1, "opening_time": "09:00", "closing_time": "12:00"},
        {"day_of_week": 1, "opening_time": "13:00", "closing_time": "17:00"},
    ]
    assert client.put("/owner/hours", headers=h, json=dup_day).status_code == 400


def test_public_unknown_slug_404(client):
    assert client.get("/public/businesses/does-not-exist").status_code == 404


def test_owner_sees_customer_bookings(client):
    owner = make_user(client, "owner1@test.com")
    biz = create_business(client, owner).json()
    svc = client.post("/owner/services", headers=owner,
                      json={"name": "Haircut", "price": 20, "duration_minutes": 30}).json()
    client.put("/owner/hours", headers=owner, json=FULL_WEEK)

    customer = make_user(client, "cust1@test.com", name="Cara Customer")
    booked = client.post("/bookings", headers=customer, json={
        "business_id": biz["id"], "service_id": svc["id"],
        "start_time": "2026-11-07T10:00:00",
    })
    assert booked.status_code == 200

    rows = client.get("/owner/bookings", headers=owner).json()
    assert len(rows) == 1
    assert rows[0]["customer_name"] == "Cara Customer"
    assert rows[0]["service"] == "Haircut"


def test_delete_service_blocked_when_it_has_bookings(client):
    owner = make_user(client, "owner1@test.com")
    biz = create_business(client, owner).json()
    used = client.post("/owner/services", headers=owner,
                       json={"name": "Haircut", "price": 20, "duration_minutes": 30}).json()
    unused = client.post("/owner/services", headers=owner,
                         json={"name": "Beard trim", "price": 10, "duration_minutes": 15}).json()
    client.put("/owner/hours", headers=owner, json=FULL_WEEK)

    customer = make_user(client, "cust1@test.com")
    client.post("/bookings", headers=customer, json={
        "business_id": biz["id"], "service_id": used["id"],
        "start_time": "2026-11-07T10:00:00",
    })

    assert client.delete(f"/owner/services/{used['id']}", headers=owner).status_code == 409
    assert client.delete(f"/owner/services/{unused['id']}", headers=owner).status_code == 200


def test_cannot_delete_another_owners_service(client):
    owner1 = make_user(client, "owner1@test.com")
    create_business(client, owner1)
    svc = client.post("/owner/services", headers=owner1,
                      json={"name": "Haircut", "price": 20, "duration_minutes": 30}).json()

    owner2 = make_user(client, "owner2@test.com")
    create_business(client, owner2, name="Other Place")
    assert client.delete(f"/owner/services/{svc['id']}", headers=owner2).status_code == 404


def test_owner_endpoints_require_auth(client):
    assert client.get("/owner/business").status_code == 401
    assert client.post("/owner/business", json={"name": "X Cuts"}).status_code == 401
    assert client.get("/owner/bookings").status_code == 401
