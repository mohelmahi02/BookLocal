import secrets
from datetime import timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Booking, BusinessHours, Service


def create_booking_record(
    db: Session,
    business_id: int,
    service_id: int,
    start_time,
    user_id: Optional[int] = None,
    guest_name: Optional[str] = None,
    guest_email: Optional[str] = None,
    guest_phone: Optional[str] = None,
) -> Booking:
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.business_id == business_id,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found for this business")

    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Check business is open at this time
    day_of_week = start_time.weekday()
    hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id,
        BusinessHours.day_of_week == day_of_week,
    ).first()
    if not hours:
        raise HTTPException(status_code=400, detail="Business closed on this day")

    open_h, open_m = map(int, hours.opening_time.split(":"))
    close_h, close_m = map(int, hours.closing_time.split(":"))
    day_start = start_time.replace(hour=open_h, minute=open_m, second=0, microsecond=0)
    day_end = start_time.replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    if start_time < day_start or end_time > day_end:
        raise HTTPException(status_code=400, detail="Requested time is outside business hours")

    # Lock overlapping bookings so two simultaneous requests cannot both succeed
    conflicting = db.query(Booking).filter(
        Booking.business_id == business_id,
        Booking.status == "confirmed",
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    ).with_for_update().first()
    if conflicting:
        raise HTTPException(status_code=409, detail="This slot is no longer available")

    booking = Booking(
        user_id=user_id,
        business_id=business_id,
        service_id=service_id,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone,
        cancel_token=secrets.token_urlsafe(16),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking
