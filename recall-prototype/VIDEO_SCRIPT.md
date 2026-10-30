# Recall Explainer Video Script

Hello, this is Recall, a beginner-friendly adaptive flashcard application that I built with Python. The interface uses Tkinter, the cards are stored in an SQLite database, and a simplified SM-2-style algorithm decides when each card should be reviewed again. The goal is to help a learner focus on difficult cards while reviewing easier cards less often.

I will first demonstrate the main workflow. I can add a new card by entering a question and an answer. I can also load three sample cards. The home screen shows the total number of cards, how many are due today, and the number of completed reviews. During a review, the question appears first. After I click “Reveal answer,” I can rate the card as Again, Hard, Good, or Easy. The card is then removed from today’s queue and given a new due date. The Manage Cards window also lets me view, edit, or delete saved cards.

The program is divided into three files so that each part has one clear responsibility. In `recall_app.py`, the `RecallApp` class builds the interface and connects buttons to functions. The `refresh` function asks the database for the next due card and updates the statistics. The `reveal_answer` function displays the hidden answer, while `review_current_card` sends the selected rating to the database.

In `database.py`, the `RecallDatabase` class creates the cards and reviews tables. The `add_card`, `update_card`, and `delete_card` functions use parameterised SQL queries, which keep data handling simple and safe. The `record_review` function reads the current scheduling values, calls the scheduling algorithm, updates the card, and saves a review-history record in one transaction.

Finally, `scheduler.py` contains the independent `calculate_review` function. A failed review resets the interval to one day. Successful reviews begin with one day, then six days, and later multiply the previous interval by the ease factor. Keeping this calculation separate makes it easier to understand and test. The included unit tests confirm that card storage, editing, deletion, review history, intervals, and error handling work correctly.
