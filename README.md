# Recall Adaptive Flashcards

Recall is a beginner-friendly Python flashcard program. It uses a Tkinter interface, an SQLite database, and a simplified SM-2-style scheduling algorithm.

## Features

-   Add flashcards with a question and answer
-   Load three example cards
-   Review cards that are due today
-   Reveal an answer before choosing Again, Hard, Good, or Easy
-   Automatically calculate the next review date
-   View, edit, and delete saved cards
-   Keep cards and review history after the program closes
-   Display totals for cards, due cards, and completed reviews

## Files

-   `recall_app.py` builds the Tkinter interface and handles button events.
-   `database.py` stores cards and review history in SQLite.
-   `scheduler.py` calculates the next review interval.
-   `tests/` contains unit tests for the database and scheduler.
-   `recall.db` is created automatically and stores local data.

## Run the program

Python 3 with Tkinter is required. No external packages are needed.

``` bash
python3 recall_app.py
```

If you want a fresh database, close the program and rename or remove `recall.db`. A new empty database will be created the next time the program starts.

## Run the tests

``` bash
python3 -m unittest discover -s tests -v
```

## How the scheduler works

The program stores three values for each card: repetitions, interval, and ease factor. A low rating resets the card to a one-day interval. Successful reviews first use one day, then six days, and later multiply the previous interval by the ease factor. The ease factor never falls below 1.3.

This is a simplified learning project inspired by the SM-2 approach. It is designed to be easy to explain rather than to reproduce every part of the original algorithm.
