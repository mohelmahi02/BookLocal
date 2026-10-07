import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Booking, Business, BusinessHours, Service, User

router = APIRouter(prefix="/owner", tags=["owner"])
public_router = APIRouter(prefix="/public", tags=["public"])

HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class BusinessIn(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    category: str = Field(default="other", max_length=50)
    description: Optional[str] = None
    location: Optional[str] = None


class ServiceIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(ge=0)
    duration_minutes: int = Field(ge=5, le=480)


class HoursIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    opening_time: str
    closing_time: str


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "business"


def unique_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug, n = base, 2
    while db.query(Business).filter(Business.slug == slug).first():
        slug = f"{base}-{n}"
        n += 1
    return slug


def business_dict(b: Business) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "category": b.category,
        "description": b.description,
        "location": b.location,
        "slug": b.slug,
    }


def service_dict(s: Service) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "price": s.price,
        "duration_minutes": s.duration_minutes,
    }


def hours_list(db: Session, business_id: int) -> list:
    rows = (
        db.query(BusinessHours)
        .filter(BusinessHours.business_id == business_id)
        .order_by(BusinessHours.day_of_week)
        .all()
    )
    return [
        {"day_of_week": h.day_of_week, "opening_time": h.opening_time, "closing_time": h.closing_time}
        for h in rows
    ]


def my_business(db: Session, user: User) -> Business:
    business = db.query(Business).filter(Business.owner_id == user.id).first()
    if not business:
        raise HTTPException(status_code=404, detail="You have not created a business yet")
    return business


@router.post("/business", status_code=201)
def create_business(
    data: BusinessIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Business).filter(Business.owner_id == current_user.id).first():
        raise HTTPException(status_code=409, detail="You already have a business")
    business = Business(
        owner_id=current_user.id,
        name=data.name,
        category=data.category,
        description=data.description,
        location=data.location,
        slug=unique_slug(db, data.name),
    )
    db.add(business)
    current_user.role = "business"
    db.commit()
    db.refresh(business)
    return business_dict(business)


@router.get("/business")
def get_business(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return business_dict(my_business(db, current_user))


@router.post("/services", status_code=201)
def add_service(
    data: ServiceIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = my_business(db, current_user)
    service = Service(
        business_id=business.id,
        name=data.name,
        price=data.price,
        duration_minutes=data.duration_minutes,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service_dict(service)


@router.get("/services")
def list_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    business = my_business(db, current_user)
    services = db.query(Service).filter(Service.business_id == business.id).order_by(Service.id).all()
    return [service_dict(s) for s in services]


@router.delete("/services/{service_id}")
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = my_business(db, current_user)
    service = (
        db.query(Service)
        .filter(Service.id == service_id, Service.business_id == business.id)
        .first()
    )
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if db.query(Booking).filter(Booking.service_id == service.id).first():
        raise HTTPException(status_code=409, detail="This service has bookings and cannot be deleted")
    db.delete(service)
    db.commit()
    return {"status": "deleted"}


@router.put("/hours")
def set_hours(
    hours: List[HoursIn],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    business = my_business(db, current_user)
    days = [h.day_of_week for h in hours]
    if len(days) != len(set(days)):
        raise HTTPException(status_code=400, detail="Each day can only appear once")
    for h in hours:
        if not (HHMM.match(h.opening_time) and HHMM.match(h.closing_time)):
            raise HTTPException(status_code=400, detail="Times must be in HH:MM format")
        if h.opening_time >= h.closing_time:
            raise HTTPException(status_code=400, detail="Opening time must be before closing time")
    db.query(BusinessHours).filter(BusinessHours.business_id == business.id).delete()
    for h in hours:
        db.add(
            BusinessHours(
                business_id=business.id,
                day_of_week=h.day_of_week,
                opening_time=h.opening_time,
                closing_time=h.closing_time,
            )
        )
    db.commit()
    return hours_list(db, business.id)


@router.get("/hours")
def get_hours(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    business = my_business(db, current_user)
    return hours_list(db, business.id)


@router.get("/bookings")
def owner_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    business = my_business(db, current_user)
    rows = (
        db.query(Booking, User, Service)
        .join(User, Booking.user_id == User.id)
        .join(Service, Booking.service_id == Service.id)
        .filter(Booking.business_id == business.id)
        .order_by(Booking.start_time)
        .all()
    )
    return [
        {
            "id": b.id,
            "start_time": b.start_time,
            "end_time": b.end_time,
            "status": b.status,
            "service": s.name,
            "customer_name": u.name,
            "customer_email": u.email,
        }
        for b, u, s in rows
    ]


@public_router.get("/businesses/{slug}")
def public_business(slug: str, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.slug == slug).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    services = db.query(Service).filter(Service.business_id == business.id).order_by(Service.id).all()
    return {
        **business_dict(business),
        "services": [service_dict(s) for s in services],
        "hours": hours_list(db, business.id),
    }
