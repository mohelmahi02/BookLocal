from datetime import datetime, date
from booking_logic import get_available_slots

target_date = date(2026, 9, 26)  # a Saturday

existing = [
    (datetime(2026, 9, 26, 10, 0), datetime(2026, 9, 26, 10, 30)),
    (datetime(2026, 9, 26, 11, 30), datetime(2026, 9, 26, 12, 15)),
]

slots = get_available_slots(
    opening_time="09:00",
    closing_time="17:00",
    duration_minutes=45,
    existing_bookings=existing,
    target_date=target_date,
)

for s in slots:
    print(s.strftime("%H:%M"))
