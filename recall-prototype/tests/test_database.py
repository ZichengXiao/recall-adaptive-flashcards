from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from database import RecallDatabase


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        path = Path(self.temporary_directory.name) / "test.db"
        self.database = RecallDatabase(path)

    def tearDown(self) -> None:
        self.database.close()
        self.temporary_directory.cleanup()

    def test_added_card_is_due_immediately(self) -> None:
        card_id = self.database.add_card("Question", "Answer")
        card = self.database.get_due_card(date.today())
        self.assertIsNotNone(card)
        self.assertEqual(card["id"], card_id)

    def test_review_updates_card_and_writes_history(self) -> None:
        card_id = self.database.add_card("Question", "Answer")
        result = self.database.record_review(card_id, 4, date(2026, 10, 8))
        total, due, reviews = self.database.get_counts(date(2026, 10, 8))
        self.assertEqual((total, due, reviews), (1, 0, 1))
        self.assertEqual(result.due_date, "2026-10-09")

    def test_blank_card_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.database.add_card("", "Answer")

    def test_card_can_be_updated(self) -> None:
        card_id = self.database.add_card("Old question", "Old answer")
        self.database.update_card(card_id, "New question", "New answer")
        card = self.database.get_card(card_id)
        self.assertEqual(card["front"], "New question")
        self.assertEqual(card["back"], "New answer")

    def test_deleting_card_also_deletes_review_history(self) -> None:
        card_id = self.database.add_card("Question", "Answer")
        self.database.record_review(card_id, 4, date(2026, 10, 8))
        self.database.delete_card(card_id)
        total, due, reviews = self.database.get_counts(date(2026, 10, 8))
        self.assertEqual((total, due, reviews), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
