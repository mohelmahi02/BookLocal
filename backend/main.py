from datetime import datetime, time
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
