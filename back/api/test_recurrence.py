"""Pure unit tests for api.recurrence (no database, no HTTP)."""
from datetime import date

from django.test import SimpleTestCase

from .recurrence import calculate_next_occurrence

TODAY = date(2026, 1, 31)


class CalculateNextOccurrenceTests(SimpleTestCase):
    def test_daily(self):
        self.assertEqual(calculate_next_occurrence('daily', None, TODAY), date(2026, 2, 1))

    def test_weekly(self):
        self.assertEqual(calculate_next_occurrence('weekly', None, TODAY), date(2026, 2, 7))

    def test_monthly_is_thirty_days_not_calendar_month(self):
        # documents the current rule: Jan 31 + 30 days = Mar 2 (a known limitation, see risk register)
        self.assertEqual(calculate_next_occurrence('monthly', None, TODAY), date(2026, 3, 2))

    def test_custom_uses_interval(self):
        self.assertEqual(calculate_next_occurrence('custom', 10, TODAY), date(2026, 2, 10))

    def test_custom_without_interval_returns_none(self):
        self.assertIsNone(calculate_next_occurrence('custom', None, TODAY))
        self.assertIsNone(calculate_next_occurrence('custom', 0, TODAY))

    def test_unknown_or_missing_type_returns_none(self):
        self.assertIsNone(calculate_next_occurrence(None, None, TODAY))
        self.assertIsNone(calculate_next_occurrence('yearly', None, TODAY))
