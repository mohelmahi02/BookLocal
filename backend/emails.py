"""Sends emails through AWS SES.

Never raises: a failed email must not break a booking. If EMAIL_SENDER is not
set (local dev, tests), emails are only logged.
"""
import logging
import os

import boto3

logger = logging.getLogger("booklocal.email")


def send_email(to: str, subject: str, body: str) -> bool:
    sender = os.getenv("EMAIL_SENDER")
    if not sender or not to:
        logger.info("Email not sent (no sender configured): to=%s subject=%s", to, subject)
        return False
    try:
        client = boto3.client("ses", region_name=os.getenv("SES_REGION", "eu-west-1"))
        client.send_email(
            Source=sender,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
            },
        )
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def _when(start_time) -> str:
    s = str(start_time)
    return f"{s[:10]} at {s[11:16]}"


def customer_confirmation(business_name, service_name, start_time, location=None) -> tuple[str, str]:
    subject = f"Booking confirmed: {business_name}"
    lines = [
        "Hi,",
        "",
        f"Your booking is confirmed.",
        "",
        f"Business: {business_name}",
        f"Service: {service_name}",
        f"When: {_when(start_time)}",
    ]
    if location:
        lines.append(f"Where: {location}")
    lines += ["", "If you need to cancel, please contact the business directly."]
    return subject, "\n".join(lines)


def owner_notification(business_name, service_name, start_time, guest_name, guest_email, guest_phone=None) -> tuple[str, str]:
    subject = f"New booking: {service_name} on {_when(start_time)}"
    lines = [
        f"You have a new booking at {business_name}.",
        "",
        f"Service: {service_name}",
        f"When: {_when(start_time)}",
        f"Customer: {guest_name}",
        f"Email: {guest_email}",
    ]
    if guest_phone:
        lines.append(f"Phone: {guest_phone}")
    return subject, "\n".join(lines)
