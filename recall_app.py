"""Tkinter interface for the Recall adaptive flashcard prototype."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from database import RecallDatabase


APP_DIR = Path(__file__).resolve().parent
DATABASE_PATH = APP_DIR / "recall.db"


class RecallApp(tk.Tk):
    def __init__(self, database_path: str | Path = DATABASE_PATH) -> None:
        super().__init__()
        self.title("Recall - Adaptive Flashcards")
        self.geometry("820x610")
        self.minsize(700, 520)
        self.configure(bg="#f4f6fb")

        self.database = RecallDatabase(database_path)
        self.current_card = None
        self.answer_revealed = False

        self._configure_styles()
        self._build_interface()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.refresh()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f4f6fb")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure(
            "Title.TLabel",
            background="#f4f6fb",
            foreground="#1f2a63",
            font=("Arial", 26, "bold"),
        )
        style.configure(
            "Sub.TLabel",
            background="#f4f6fb",
            foreground="#59627d",
            font=("Arial", 11),
        )
        style.configure(
            "Card.TLabel",
            background="#ffffff",
            foreground="#1d2748",
            font=("Arial", 18),
            wraplength=650,
            justify="center",
        )
        style.configure(
            "Answer.TLabel",
            background="#ffffff",
            foreground="#314ba0",
            font=("Arial", 16, "bold"),
            wraplength=650,
            justify="center",
        )
        style.configure(
            "Stats.TLabel",
            background="#e7edff",
            foreground="#263879",
            font=("Arial", 11, "bold"),
            padding=10,
        )
        style.configure("TButton", font=("Arial", 11), padding=(12, 8))
        style.configure("Primary.TButton", font=("Arial", 11, "bold"))

    def _build_interface(self) -> None:
        header = ttk.Frame(self, padding=(28, 22, 28, 8))
        header.pack(fill="x")
        ttk.Label(header, text="Recall", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="A simple adaptive flashcard trainer using Python, SQLite and an SM-2-style scheduler",
            style="Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        toolbar = ttk.Frame(self, padding=(28, 8))
        toolbar.pack(fill="x")
        ttk.Button(
            toolbar,
            text="Add card",
            style="Primary.TButton",
            command=self.open_add_card,
        ).pack(side="left")
        ttk.Button(toolbar, text="Manage cards", command=self.open_card_list).pack(
            side="left", padx=8
        )
        ttk.Button(toolbar, text="Load demo cards", command=self.load_examples).pack(side="left")
        self.stats_label = ttk.Label(toolbar, style="Stats.TLabel")
        self.stats_label.pack(side="right")

        card = ttk.Frame(self, style="Card.TFrame", padding=32)
        card.pack(fill="both", expand=True, padx=28, pady=(6, 18))

        self.prompt_label = ttk.Label(card, text="", style="Card.TLabel")
        self.prompt_label.pack(fill="x", pady=(30, 22))

        self.answer_label = ttk.Label(card, text="", style="Answer.TLabel")
        self.answer_label.pack(fill="x", pady=(8, 28))

        self.reveal_button = ttk.Button(
            card,
            text="Reveal answer",
            style="Primary.TButton",
            command=self.reveal_answer,
        )
        self.reveal_button.pack(pady=8)

        self.rating_frame = ttk.Frame(card, style="Card.TFrame")
        self.rating_frame.pack(pady=(20, 10))
        ratings = [
            ("Again", 1),
            ("Hard", 3),
            ("Good", 4),
            ("Easy", 5),
        ]
        self.rating_buttons = []
        for label, quality in ratings:
            button = ttk.Button(
                self.rating_frame,
                text=label,
                command=lambda value=quality: self.review_current_card(value),
                state="disabled",
            )
            button.pack(side="left", padx=6)
            self.rating_buttons.append(button)

        self.feedback_label = ttk.Label(card, text="", style="Sub.TLabel")
        self.feedback_label.pack(pady=(18, 0))

    def refresh(self) -> None:
        total, due, reviews = self.database.get_counts()
        self.stats_label.configure(text=f"Cards: {total}   Due: {due}   Reviews: {reviews}")
        self.current_card = self.database.get_due_card()
        self.answer_revealed = False
        self.answer_label.configure(text="")
        for button in self.rating_buttons:
            button.configure(state="disabled")

        if self.current_card is None:
            self.prompt_label.configure(
                text="No cards are due today. Add a card or load the demo deck to continue."
            )
            self.reveal_button.configure(state="disabled")
        else:
            self.prompt_label.configure(text=self.current_card["front"])
            self.reveal_button.configure(state="normal")

    def reveal_answer(self) -> None:
        if self.current_card is None:
            return
        self.answer_revealed = True
        self.answer_label.configure(text=self.current_card["back"])
        self.reveal_button.configure(state="disabled")
        for button in self.rating_buttons:
            button.configure(state="normal")

    def review_current_card(self, quality: int) -> None:
        if self.current_card is None or not self.answer_revealed:
            return
        result = self.database.record_review(self.current_card["id"], quality)
        self.feedback_label.configure(
            text=f"Saved. Next review in {result.interval_days} day(s), on {result.due_date}."
        )
        self.refresh()

    def open_add_card(self) -> None:
        window = tk.Toplevel(self)
        window.title("Add a flashcard")
        window.geometry("520x350")
        window.transient(self)
        window.grab_set()

        frame = ttk.Frame(window, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Front / question").pack(anchor="w")
        front = tk.Text(frame, height=4, wrap="word", font=("Arial", 11))
        front.pack(fill="x", pady=(4, 14))
        ttk.Label(frame, text="Back / answer").pack(anchor="w")
        back = tk.Text(frame, height=4, wrap="word", font=("Arial", 11))
        back.pack(fill="x", pady=(4, 16))

        def save() -> None:
            try:
                self.database.add_card(front.get("1.0", "end"), back.get("1.0", "end"))
            except ValueError as error:
                messagebox.showerror("Cannot add card", str(error), parent=window)
                return
            window.destroy()
            self.feedback_label.configure(text="Card added and ready for review.")
            self.refresh()

        ttk.Button(frame, text="Save card", style="Primary.TButton", command=save).pack(anchor="e")
        front.focus_set()

    def open_card_list(self) -> None:
        window = tk.Toplevel(self)
        window.title("Manage cards")
        window.geometry("980x480")
        window.minsize(820, 400)

        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text="Select a card, then choose Edit or Delete.",
            font=("Arial", 11),
        ).pack(anchor="w", pady=(0, 10))

        columns = ("id", "front", "back", "due", "interval", "ease")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading("id", text="ID")
        tree.heading("front", text="Front")
        tree.heading("back", text="Back")
        tree.heading("due", text="Due date")
        tree.heading("interval", text="Interval")
        tree.heading("ease", text="Ease")
        tree.column("id", width=45, anchor="center")
        tree.column("front", width=270)
        tree.column("back", width=300)
        tree.column("due", width=100, anchor="center")
        tree.column("interval", width=75, anchor="center")
        tree.column("ease", width=65, anchor="center")
        tree.pack(fill="both", expand=True)

        def refresh_tree() -> None:
            """Reload the table after a card is edited or deleted."""

            for item in tree.get_children():
                tree.delete(item)
            for card in self.database.list_cards():
                tree.insert(
                    "",
                    "end",
                    values=(
                        card["id"],
                        card["front"],
                        card["back"],
                        card["due_date"],
                        card["interval_days"],
                        f"{card['ease_factor']:.2f}",
                    ),
                )

        def selected_card_id() -> int | None:
            selected = tree.selection()
            if not selected:
                messagebox.showinfo(
                    "Select a card",
                    "Please select a card first.",
                    parent=window,
                )
                return None
            values = tree.item(selected[0], "values")
            return int(values[0])

        def edit_selected() -> None:
            card_id = selected_card_id()
            if card_id is not None:
                self.open_edit_card(card_id, window, refresh_tree)

        def delete_selected() -> None:
            card_id = selected_card_id()
            if card_id is None:
                return
            if not messagebox.askyesno(
                "Delete card",
                "Delete this card and its review history?",
                parent=window,
            ):
                return
            self.database.delete_card(card_id)
            refresh_tree()
            self.feedback_label.configure(text="Card deleted.")
            self.refresh()

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=(12, 0))
        ttk.Button(buttons, text="Edit selected", command=edit_selected).pack(
            side="left"
        )
        ttk.Button(buttons, text="Delete selected", command=delete_selected).pack(
            side="left", padx=8
        )
        ttk.Button(buttons, text="Close", command=window.destroy).pack(side="right")

        tree.bind("<Double-1>", lambda _event: edit_selected())
        refresh_tree()

    def open_edit_card(
        self,
        card_id: int,
        parent: tk.Misc,
        after_save,
    ) -> None:
        """Open a small window that edits one existing card."""

        card = self.database.get_card(card_id)
        if card is None:
            messagebox.showerror("Card not found", "This card no longer exists.", parent=parent)
            return

        window = tk.Toplevel(self)
        window.title("Edit flashcard")
        window.geometry("520x350")
        window.transient(parent)
        window.grab_set()

        frame = ttk.Frame(window, padding=22)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Front / question").pack(anchor="w")
        front = tk.Text(frame, height=4, wrap="word", font=("Arial", 11))
        front.pack(fill="x", pady=(4, 14))
        front.insert("1.0", card["front"])

        ttk.Label(frame, text="Back / answer").pack(anchor="w")
        back = tk.Text(frame, height=4, wrap="word", font=("Arial", 11))
        back.pack(fill="x", pady=(4, 16))
        back.insert("1.0", card["back"])

        def save() -> None:
            try:
                self.database.update_card(
                    card_id,
                    front.get("1.0", "end"),
                    back.get("1.0", "end"),
                )
            except ValueError as error:
                messagebox.showerror("Cannot save card", str(error), parent=window)
                return
            window.destroy()
            after_save()
            self.feedback_label.configure(text="Card updated.")
            self.refresh()

        ttk.Button(
            frame,
            text="Save changes",
            style="Primary.TButton",
            command=save,
        ).pack(anchor="e")
        front.focus_set()

    def load_examples(self) -> None:
        if self.database.seed_examples():
            self.feedback_label.configure(text="Three demo cards were added.")
        else:
            messagebox.showinfo(
                "Demo deck not loaded",
                "The database already contains cards, so no examples were added.",
                parent=self,
            )
        self.refresh()

    def _close(self) -> None:
        self.database.close()
        self.destroy()


if __name__ == "__main__":
    try:
        RecallApp().mainloop()
    except tk.TclError as error:
        raise SystemExit(f"Recall could not open its window: {error}") from error
