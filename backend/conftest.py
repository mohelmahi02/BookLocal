import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "postgresql://booklocal:booklocal_dev@localhost:5432/booklocal_test"

from database import Base, get_db
from main import app
from fastapi.testclient import TestClient

TEST_DATABASE_URL = "postgresql://booklocal:booklocal_dev@localhost:5432/booklocal_test"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_business(db_session):
    from models import User, Business, Service, BusinessHours
    from auth import hash_password

    owner = User(name="Business Owner", email="owner@test.com",
                 hashed_password=hash_password("ownerpass123"), role="business")
    db_session.add(owner)
    db_session.commit()
    db_session.refresh(owner)

    business = Business(owner_id=owner.id, name="Test Barbershop",
                         description="Test", location="Castlebar")
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)

    service = Service(business_id=business.id, name="Haircut",
                       price=20.00, duration_minutes=30)
    db_session.add(service)
    db_session.commit()
    db_session.refresh(service)

    hours = BusinessHours(business_id=business.id, day_of_week=5,
                           opening_time="09:00", closing_time="17:00")
    db_session.add(hours)
    db_session.commit()

    return {"business": business, "service": service}


@pytest.fixture
def auth_token(client):
    client.post("/register", json={
        "name": "Booking Customer",
        "email": "bookingcustomer@test.com",
        "password": "custpass123",
    })
    response = client.post("/login", json={
        "email": "bookingcustomer@test.com",
        "password": "custpass123",
    })
    return response.json()["access_token"]
