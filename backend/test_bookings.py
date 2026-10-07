def test_create_booking_success(client, seeded_business, auth_token):
    service = seeded_business["service"]
    business = seeded_business["business"]

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": "2026-09-26T13:00:00",  # Saturday, within 09:00-17:00
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"
    assert data["start_time"].startswith("2026-09-26T13:00:00")


def test_create_booking_outside_business_hours(client, seeded_business, auth_token):
    service = seeded_business["service"]
    business = seeded_business["business"]

    response = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": "2026-09-26T18:00:00",  # after 17:00 close
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Requested time is outside business hours"


def test_create_booking_conflict_rejected(client, seeded_business, auth_token):
    service = seeded_business["service"]
    business = seeded_business["business"]

    first = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": "2026-09-26T10:00:00",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": "2026-09-26T10:00:00",  # same slot again
        },
    )
    assert second.status_code == 409
    assert second.json()["detail"] == "This slot is no longer available"


def test_create_booking_requires_auth(client, seeded_business):
    service = seeded_business["service"]
    business = seeded_business["business"]

    response = client.post(
        "/bookings",
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": "2026-09-26T14:00:00",
        },
    )
    assert response.status_code == 401


def _book(client, token, business, service, start_time):
    return client.post(
        "/bookings",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "business_id": business.id,
            "service_id": service.id,
            "start_time": start_time,
        },
    )


def _second_user_token(client):
    client.post("/register", json={
        "name": "Other Customer",
        "email": "othercustomer@test.com",
        "password": "otherpass123",
    })
    r = client.post("/login", json={
        "email": "othercustomer@test.com",
        "password": "otherpass123",
    })
    return r.json()["access_token"]


def test_list_my_bookings(client, seeded_business, auth_token):
    b, s = seeded_business["business"], seeded_business["service"]
    assert _book(client, auth_token, b, s, "2026-09-26T11:00:00").status_code == 200

    r = client.get("/bookings", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_list_bookings_only_returns_own(client, seeded_business, auth_token):
    b, s = seeded_business["business"], seeded_business["service"]
    assert _book(client, auth_token, b, s, "2026-09-26T11:00:00").status_code == 200

    other = _second_user_token(client)
    r = client.get("/bookings", headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 200
    assert r.json() == []


def test_cancel_booking(client, seeded_business, auth_token):
    b, s = seeded_business["business"], seeded_business["service"]
    created = _book(client, auth_token, b, s, "2026-09-26T12:00:00")
    booking_id = created.json()["id"]

    r = client.delete(f"/bookings/{booking_id}",
                      headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200

    # the same slot can now be booked again
    again = _book(client, auth_token, b, s, "2026-09-26T12:00:00")
    assert again.status_code == 200


def test_cannot_cancel_someone_elses_booking(client, seeded_business, auth_token):
    b, s = seeded_business["business"], seeded_business["service"]
    booking_id = _book(client, auth_token, b, s, "2026-09-26T12:00:00").json()["id"]

    other = _second_user_token(client)
    r = client.delete(f"/bookings/{booking_id}",
                      headers={"Authorization": f"Bearer {other}"})
    assert r.status_code == 404


def test_bookings_endpoints_require_auth(client):
    assert client.get("/bookings").status_code == 401
    assert client.delete("/bookings/1").status_code == 401
