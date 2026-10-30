"""Scheduling logic for the Recall flashcard prototype.

The function in this module is deliberately independent from the user interface
and database.  Keeping it pure makes the algorithm easy to explain and test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class ScheduleResult:
    """The scheduling state produced after one card review."""

    repetitions: int
    interval_days: int
    ease_factor: float
    due_date: str


def calculate_review(
    repetitions: int,
    interval_days: int,
    ease_factor: float,
    quality: int,
    review_date: date | None = None,
) -> ScheduleResult:
    """Calculate the next review using a small SM-2-style algorithm.

    ``quality`` uses the original 0-5 scale.  The interface maps its four
    buttons to 1 (Again), 3 (Hard), 4 (Good), and 5 (Easy).
    """

    if quality not in range(6):
        raise ValueError("quality must be an integer from 0 to 5")
    if repetitions < 0 or interval_days < 0:
        raise ValueError("repetitions and interval_days cannot be negative")

    day = review_date or date.today()
    difference = 5 - quality
    new_ease = ease_factor + (0.1 - difference * (0.08 + difference * 0.02))
    new_ease = max(1.3, round(new_ease, 2))

    if quality < 3:
        new_repetitions = 0
        new_interval = 1
    elif repetitions == 0:
        new_repetitions = 1
        new_interval = 1
    elif repetitions == 1:
        new_repetitions = 2
        new_interval = 6
    else:
        new_repetitions = repetitions + 1
        new_interval = max(1, round(interval_days * new_ease))

    next_due = day + timedelta(days=new_interval)
    return ScheduleResult(
        repetitions=new_repetitions,
        interval_days=new_interval,
        ease_factor=new_ease,
        due_date=next_due.isoformat(),
    )
