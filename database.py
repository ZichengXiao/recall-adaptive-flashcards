"""SQLite persistence for Recall."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import sqlite3

from scheduler import ScheduleResult, calculate_review


class RecallDatabase:
    """Store cards and review history in one local SQLite database."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                front TEXT NOT NULL,
                back TEXT NOT NULL,
                repetitions INTEGER NOT NULL DEFAULT 0,
                interval_days INTEGER NOT NULL DEFAULT 0,
                ease_factor REAL NOT NULL DEFAULT 2.5,
                due_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id INTEGER NOT NULL,
                reviewed_at TEXT NOT NULL,
                quality INTEGER NOT NULL CHECK (quality BETWEEN 0 AND 5),
                previous_interval INTEGER NOT NULL,
                next_interval INTEGER NOT NULL,
                FOREIGN KEY (card_id) REFERENCES cards(id) ON DELETE CASCADE
            );
            """
        )
        self.connection.commit()

    def add_card(self, front: str, back: str) -> int:
        front = front.strip()
        back = back.strip()
        if not front or not back:
            raise ValueError("Both the front and back of a card are required")

        now = datetime.now().isoformat(timespec="seconds")
        cursor = self.connection.execute(
            """
            INSERT INTO cards (front, back, due_date, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (front, back, date.today().isoformat(), now),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def get_due_card(self, on_date: date | None = None) -> sqlite3.Row | None:
        target = (on_date or date.today()).isoformat()
        return self.connection.execute(
            """
            SELECT * FROM cards
            WHERE due_date <= ?
            ORDER BY due_date ASC, id ASC
            LIMIT 1
            """,
            (target,),
        ).fetchone()

    def record_review(
        self,
        card_id: int,
        quality: int,
        review_date: date | None = None,
    ) -> ScheduleResult:
        card = self.connection.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()
        if card is None:
            raise KeyError(f"Card {card_id} does not exist")

        result = calculate_review(
            repetitions=card["repetitions"],
            interval_days=card["interval_days"],
            ease_factor=card["ease_factor"],
            quality=quality,
            review_date=review_date,
        )
        reviewed_at = datetime.now().isoformat(timespec="seconds")

        with self.connection:
            self.connection.execute(
                """
                UPDATE cards
                SET repetitions = ?, interval_days = ?, ease_factor = ?, due_date = ?
                WHERE id = ?
                """,
                (
                    result.repetitions,
                    result.interval_days,
                    result.ease_factor,
                    result.due_date,
                    card_id,
                ),
            )
            self.connection.execute(
                """
                INSERT INTO reviews (
                    card_id, reviewed_at, quality, previous_interval, next_interval
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    card_id,
                    reviewed_at,
                    quality,
                    card["interval_days"],
                    result.interval_days,
                ),
            )
        return result

    def get_counts(self, on_date: date | None = None) -> tuple[int, int, int]:
        target = (on_date or date.today()).isoformat()
        total = self.connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        due = self.connection.execute(
            "SELECT COUNT(*) FROM cards WHERE due_date <= ?", (target,)
        ).fetchone()[0]
        reviews = self.connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        return int(total), int(due), int(reviews)

    def list_cards(self) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                """
                SELECT id, front, back, repetitions, due_date,
                       interval_days, ease_factor
                FROM cards
                ORDER BY due_date ASC, id ASC
                """
            ).fetchall()
        )

    def get_card(self, card_id: int) -> sqlite3.Row | None:
        """Return one card so the interface can display it for editing."""

        return self.connection.execute(
            "SELECT * FROM cards WHERE id = ?", (card_id,)
        ).fetchone()

    def update_card(self, card_id: int, front: str, back: str) -> None:
        """Change the question and answer without resetting review progress."""

        front = front.strip()
        back = back.strip()
        if not front or not back:
            raise ValueError("Both the front and back of a card are required")

        cursor = self.connection.execute(
            """
            UPDATE cards
            SET front = ?, back = ?
            WHERE id = ?
            """,
            (front, back, card_id),
        )
        self.connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(f"Card {card_id} does not exist")

    def delete_card(self, card_id: int) -> None:
        """Delete a card and its review history."""

        cursor = self.connection.execute(
            "DELETE FROM cards WHERE id = ?", (card_id,)
        )
        self.connection.commit()
        if cursor.rowcount == 0:
            raise KeyError(f"Card {card_id} does not exist")

    def seed_examples(self) -> bool:
        """Add a small demo deck only when the database has no cards."""

        total, _, _ = self.get_counts()
        if total:
            return False
        examples = [
            ("What does a variable store?", "A value that a program can reuse or change."),
            ("What is a function?", "A named, reusable block of code that performs a task."),
            ("What does a database persist?", "Data that should remain after the program closes."),
        ]
        for front, back in examples:
            self.add_card(front, back)
        return True

    def close(self) -> None:
        self.connection.close()
