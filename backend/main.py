from datetime import datetime, time, timedelta
from fastapi import FastAPI

app = FastAPI(title="BookLocal API")

@app.get("/")
def root():
    return {"status": "BookLocal API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

from datetime import date as date_type
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import get_db
from models import BusinessHours, Booking, Service
from booking_logic import get_available_slots


@app.get("/businesses/{business_id}/available-slots")
def available_slots(
    business_id: int,
    service_id: int,
    target_date: date_type = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    service = db.query(Service).filter(Service.id == service_id, Service.business_id == business_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found for this business")

    day_of_week = target_date.weekday()  # 0 = Monday
    hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == business_id,
        BusinessHours.day_of_week == day_of_week,
    ).first()
    if not hours:
        return {"date": str(target_date), "slots": [], "message": "Business closed this day"}

    bookings = db.query(Booking).filter(
        Booking.business_id == business_id,
        Booking.status == "confirmed",
        and_(Booking.start_time >= datetime.combine(target_date, time.min),
             Booking.start_time <= datetime.combine(target_date, time.max)),
    ).all()

    existing = [(b.start_time.replace(tzinfo=None), b.end_time.replace(tzinfo=None)) for b in bookings]

    slots = get_available_slots(
        opening_time=hours.opening_time,
        closing_time=hours.closing_time,
        duration_minutes=service.duration_minutes,
        existing_bookings=existing,
        target_date=target_date,
    )

    return {"date": str(target_date), "slots": [s.strftime("%H:%M") for s in slots]}

from pydantic import BaseModel


class BookingCreate(BaseModel):
    user_id: int
    business_id: int
    service_id: int
    start_time: datetime


@app.post("/bookings")
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    service = db.query(Service).filter(
        Service.id == payload.service_id,
        Service.business_id == payload.business_id,
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found for this business")

    start_time = payload.start_time
    end_time = start_time + timedelta(minutes=service.duration_minutes)

    # Check business is open at this time
    day_of_week = start_time.weekday()
    hours = db.query(BusinessHours).filter(
        BusinessHours.business_id == payload.business_id,
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

    # Lock existing bookings for this business to prevent a race condition
    # where two requests both pass the overlap check at the same time
    conflicting = db.query(Booking).filter(
        Booking.business_id == payload.business_id,
        Booking.status == "confirmed",
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    ).with_for_update().first()

    if conflicting:
        raise HTTPException(status_code=409, detail="This slot is no longer available")

    new_booking = Booking(
        user_id=payload.user_id,
        business_id=payload.business_id,
        service_id=payload.service_id,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
    )
    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)

    return {
        "id": new_booking.id,
        "start_time": new_booking.start_time.isoformat(),
        "end_time": new_booking.end_time.isoformat(),
        "status": new_booking.status,
    }
