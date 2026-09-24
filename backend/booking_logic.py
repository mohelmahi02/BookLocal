from datetime import datetime, timedelta, time
from typing import List


def get_available_slots(
    opening_time: str,
    closing_time: str,
    duration_minutes: int,
    existing_bookings: List[tuple],
    target_date: datetime.date,
) -> List[datetime]:
    open_h, open_m = map(int, opening_time.split(":"))
    close_h, close_m = map(int, closing_time.split(":"))

    day_start = datetime.combine(target_date, time(open_h, open_m))
    day_end = datetime.combine(target_date, time(close_h, close_m))

    bookings_sorted = sorted(existing_bookings, key=lambda b: b[0])

    slots = []
    cursor = day_start
    duration = timedelta(minutes=duration_minutes)

    for booking_start, booking_end in bookings_sorted:
        while cursor + duration <= booking_start:
            slots.append(cursor)
            cursor += duration
        if booking_end > cursor:
            cursor = booking_end

    while cursor + duration <= day_end:
        slots.append(cursor)
        cursor += duration

    return slots
