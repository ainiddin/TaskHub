"""Recurrence rules for repeating tasks.

Extracted from TaskDetailAPIView.update so the rule can be unit-tested without HTTP.
It is a table-driven strategy: each repeat_type maps to a small function returning the interval.
Behaviour is intentionally identical to the previous if/elif chain (monthly = 30 days).
"""
from datetime import date, timedelta

# repeat_type -> function(repeat_every_days) -> timedelta (or None when no interval can be derived)
INTERVAL_BY_REPEAT_TYPE = {
    'daily': lambda every_days: timedelta(days=1),
    'weekly': lambda every_days: timedelta(weeks=1),
    'monthly': lambda every_days: timedelta(days=30),
    'custom': lambda every_days: timedelta(days=every_days) if every_days else None,
}


def calculate_next_occurrence(repeat_type, repeat_every_days, today=None):
    """Return the next occurrence date, or None when the task has no derivable schedule."""
    interval_for = INTERVAL_BY_REPEAT_TYPE.get(repeat_type)
    if interval_for is None:
        return None
    interval = interval_for(repeat_every_days)
    if interval is None:
        return None
    return (today or date.today()) + interval
