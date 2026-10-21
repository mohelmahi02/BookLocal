import emails
import public_bookings
from test_guest import SLOT, guest_book, setup_business


def capture(monkeypatch):
    sent = []
    monkeypatch.setattr(
        public_bookings, "send_email",
        lambda to, subject, body: sent.append((to, subject, body)),
    )
    return sent


def test_booking_sends_customer_and_owner_emails(client, monkeypatch):
    sent = capture(monkeypatch)
    owner, service = setup_business(client)
    r = guest_book(client, "test-cuts", service["id"])
    assert r.status_code == 201
    recipients = {to for to, _, _ in sent}
    assert recipients == {"gary@example.com", "owner1@test.com"}
    customer = next(m for m in sent if m[0] == "gary@example.com")
    assert "Test Cuts" in customer[1]
    assert "Haircut" in customer[2]
    assert "2026-11-07 at 10:00" in customer[2]
    owner_mail = next(m for m in sent if m[0] == "owner1@test.com")
    assert "Gary Guest" in owner_mail[2]
    assert "0871234567" in owner_mail[2]


def test_no_email_when_slot_is_taken(client, monkeypatch):
    sent = capture(monkeypatch)
    owner, service = setup_business(client)
    guest_book(client, "test-cuts", service["id"])
    sent.clear()
    r = guest_book(client, "test-cuts", service["id"], email="other@example.com")
    assert r.status_code == 409
    assert sent == []


def test_email_failure_does_not_break_booking(client, monkeypatch):
    monkeypatch.setenv("EMAIL_SENDER", "sender@example.com")

    def boom(*args, **kwargs):
        raise RuntimeError("SES is down")

    monkeypatch.setattr(emails.boto3, "client", boom)
    owner, service = setup_business(client)
    r = guest_book(client, "test-cuts", service["id"])
    assert r.status_code == 201


def test_send_email_without_sender_is_a_noop(monkeypatch):
    monkeypatch.delenv("EMAIL_SENDER", raising=False)
    assert emails.send_email("a@b.c", "subject", "body") is False
