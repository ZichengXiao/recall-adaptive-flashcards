from datetime import date
import unittest

from scheduler import calculate_review


class SchedulerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.today = date(2026, 10, 8)

    def test_first_successful_review_uses_one_day_interval(self) -> None:
        result = calculate_review(0, 0, 2.5, 4, self.today)
        self.assertEqual(result.repetitions, 1)
        self.assertEqual(result.interval_days, 1)
        self.assertEqual(result.due_date, "2026-10-09")

    def test_second_successful_review_uses_six_day_interval(self) -> None:
        result = calculate_review(1, 1, 2.5, 4, self.today)
        self.assertEqual(result.repetitions, 2)
        self.assertEqual(result.interval_days, 6)
        self.assertEqual(result.due_date, "2026-10-14")

    def test_failed_review_resets_repetitions(self) -> None:
        result = calculate_review(5, 24, 2.4, 1, self.today)
        self.assertEqual(result.repetitions, 0)
        self.assertEqual(result.interval_days, 1)

    def test_ease_factor_never_drops_below_minimum(self) -> None:
        result = calculate_review(4, 12, 1.3, 0, self.today)
        self.assertEqual(result.ease_factor, 1.3)

    def test_invalid_quality_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            calculate_review(0, 0, 2.5, 7, self.today)


if __name__ == "__main__":
    unittest.main()
