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
