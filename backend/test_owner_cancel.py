from test_guest import setup_business, guest_book


def test_owner_can_cancel_a_booking_and_slot_frees_up(client):
    owner, service = setup_business(client)
    booking = guest_book(client, "test-cuts", service["id"]).json()

    r = client.delete(f"/owner/bookings/{booking['id']}", headers=owner)
    assert r.status_code == 200

    rows = client.get("/owner/bookings", headers=owner).json()
    assert rows[0]["status"] == "cancelled"

    again = guest_book(client, "test-cuts", service["id"], name="Next", email="n@example.com")
    assert again.status_code == 201


def test_owner_cannot_cancel_another_businesses_booking(client):
    owner1, service1 = setup_business(client, "owner1@test.com", "Test Cuts")
    owner2, service2 = setup_business(client, "owner2@test.com", "Other Place")
    booking = guest_book(client, "test-cuts", service1["id"]).json()

    r = client.delete(f"/owner/bookings/{booking['id']}", headers=owner2)
    assert r.status_code == 404


def test_owner_cancel_requires_auth(client):
    assert client.delete("/owner/bookings/1").status_code == 401
