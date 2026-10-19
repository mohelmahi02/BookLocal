import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from bookings_core import create_booking_record
from database import get_db
from models import Booking, Business

router = APIRouter(prefix="/public", tags=["public"])

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class GuestBookingIn(BaseModel):
    service_id: int
    start_time: datetime
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(max_length=200)
    phone: Optional[str] = Field(default=None, max_length=30)


@router.post("/businesses/{slug}/bookings", status_code=201)
def guest_book(slug: str, data: GuestBookingIn, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.slug == slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not EMAIL.match(data.email.strip()):
        raise HTTPException(status_code=400, detail="Please enter a valid email address")

    booking = create_booking_record(
        db,
        business_id=business.id,
        service_id=data.service_id,
        start_time=data.start_time,
        guest_name=data.name.strip(),
        guest_email=data.email.strip().lower(),
        guest_phone=data.phone.strip() if data.phone else None,
    )
    return {
        "id": booking.id,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "status": booking.status,
        "cancel_token": booking.cancel_token,
    }


@router.delete("/bookings/{token}")
def guest_cancel(token: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.cancel_token == token).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking.status = "cancelled"
    db.commit()
    return {"status": "cancelled"}
