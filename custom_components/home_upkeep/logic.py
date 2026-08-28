"""
Pure rescheduling and seasonal-constraint calculations.

Ported from the add-on backend (`backend/app/main.py`), which computed these
inline and had no unit tests for them.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta


def find_first_non_prohibited_month(
    start_date: date, prohibited_months: list[int]
) -> date:
    """
    Find the first day of the next month that is not prohibited.

    If the start_date month is not prohibited, return the first day of that
    month. Otherwise, roll forward to the first day of the next
    non-prohibited month.
    """
    if not prohibited_months:
        return start_date

    current_year = start_date.year
    current_month = start_date.month

    if current_month not in prohibited_months:
        return start_date.replace(day=1)

    max_months = 12
    for _ in range(max_months):
        current_month += 1
        if current_month > max_months:
            current_month = 1
            current_year += 1

        if current_month not in prohibited_months:
            return date(current_year, current_month, 1)

    # Fallback: if all months are prohibited, return the original date.
    return start_date


def calculate_next_due_date(
    base_date: date,
    reschedule_period: str,
    prohibited_months: list[int] | None = None,
) -> date:
    """
    Calculate the next due date for a rescheduled task.

    Args:
        base_date: The base date to calculate from.
        reschedule_period: The reschedule period (e.g., "5d", "1w", "1m").
        prohibited_months: List of prohibited months.

    Returns:
        The calculated next due date.

    """
    amount = int(reschedule_period[:-1])
    unit = reschedule_period[-1]

    next_due = base_date

    if unit == "d":
        next_due = base_date + timedelta(days=amount)
    elif unit == "w":
        next_due = base_date + timedelta(weeks=amount)
    elif unit == "m":
        # Month addition: add months keeping day if possible,
        # fallback to last day of next month.
        year = base_date.year
        month = base_date.month + amount
        day = base_date.day
        year += (month - 1) // 12
        month = ((month - 1) % 12) + 1
        last_day = monthrange(year, month)[1]
        day = min(day, last_day)
        next_due = base_date.replace(year=year, month=month, day=day)

    if prohibited_months and next_due.month in prohibited_months:
        next_due = find_first_non_prohibited_month(next_due, prohibited_months)

    return next_due
