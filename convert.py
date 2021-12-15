import json
import csv
from datetime import date

from constants import STORE_PATH, CSV_PATH, COLLECTED, BOOK

READING = "currently-reading"
TO_READ = "to-read"
READ = "read"
HEADER = "Title", "Author", "Date Read", "Date Added", "Shelves"
MIN_READ = 95
MIN_READING = 10


def read() -> COLLECTED:
    with open(STORE_PATH) as f:
        return json.load(f)


def clean_title(title: str) -> str:
    no_edition = title.rsplit("(", 1)[0]
    return no_edition.split(":")[0].strip()


def clean_author(author: str) -> str:
    if not author:
        return ""
    single_author = author.split(";")[0]
    split = single_author.split(",")
    if len(split) < 2:
        return split[0]
    return f"{split[1]} {split[0]}".strip()


def convert(book: BOOK):
    title = clean_title(book.get("title", ""))
    author = clean_author(book.get("authors", ""))
    date_added = date.today().strftime(r"%Y-%m-%d")
    progress = book.get("progress", 0)
    if progress == "":
        progress = 0
    date_read = None
    shelf = TO_READ
    if progress > MIN_READ:
        date_read = date.today().strftime(r"%Y-%m-%d")
        shelf = READ
    elif progress > MIN_READING:
        shelf = READING

    return {
        "Title": title,
        "Author": author,
        "Date Read": date_read,
        "Date Added": date_added,
        "Shelves": shelf
    }


def to_csv(collected: COLLECTED):
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(
            csvfile,
            HEADER,
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        for _, book in collected.items():
            converted = convert(book)
            writer.writerow(converted)


def main():
    stored_collected = read()
    collected = stored_collected.get("collected", {})
    to_csv(collected)


main()
