#!/usr/bin/env python3

import os.path
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import feedparser  # type: ignore


FEED_FILE = os.path.expanduser("~/.plaintextfeeds")
DATA_FILE = os.path.expanduser("~/.plaintextfeeds.data")
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


@dataclass
class Entry:
    url: str
    title: str
    pub_date: datetime

    def get_info(self) -> str:
        return (
            f"  Entry: {self.title}\n"
            f"   Link: {self.url}\n"
            f"   Date: {self.pub_date.strftime('%d %B %Y at %H:%M:%S')}"
        )


@dataclass
class Feed:
    url: str
    title: Optional[str] = None
    entries: list[Entry] = field(default_factory=list)
    retrieval_failed: bool = False
    newest_retrieved_date: Optional[
        datetime
    ] = None  # Published date of the newest retrieved entry
    is_enabled: bool = False

    def get_info(self) -> str:
        retrieval_failed_msg = " (retrieval failed)" if self.retrieval_failed else ""

        if self.title:
            return f"Feed: {self.title}{retrieval_failed_msg}\n" f" URL: {self.url}"

        return f"Feed: {self.url}"


Url = str


def get_url_list(feed_file: str) -> list[Url]:
    feed_file_path = Path(feed_file)

    try:
        with open(feed_file_path, encoding="utf-8") as file:
            lines = file.read().split("\n")
    except FileNotFoundError:
        feed_file_path.touch()
        return []

    lines = [line.strip() for line in lines]

    urls = list(filter(lambda line: len(line) > 0 and line[0] != "#", lines))

    return urls


def get_feed_data(data_file: str, date_format: str, urls: list[Url]) -> dict[Url, Feed]:
    feed_data: dict[Url, Feed] = {}

    for url in urls:
        feed_data[url] = Feed(url, is_enabled=True)

    try:
        with open(data_file, encoding="utf-8") as file:
            lines = file.read().split("\n")

            for line in lines:
                parts = line.split("last updated", maxsplit=2)

                if len(parts) > 0:
                    url = parts[0].strip()

                    if len(url) == 0:
                        continue

                    newest_retrieved_date = None

                    if len(parts) > 1:
                        try:
                            newest_retrieved_date = datetime.strptime(
                                parts[1].strip(), date_format
                            )
                        except ValueError:
                            pass

                    if not url in feed_data:
                        feed_data[url] = Feed(url)

                    feed_data[url].newest_retrieved_date = newest_retrieved_date
    except FileNotFoundError:
        pass

    return feed_data


def update_feed(feed: Feed) -> None:
    data = feedparser.parse(feed.url)

    if "bozo" in data and data["bozo"]:
        feed.retrieval_failed = True
        return

    if "title" in data["feed"]:
        feed.title = data["feed"]["title"]

    newest_pub_date = feed.newest_retrieved_date

    for entry in data.entries:
        if "published_parsed" not in entry:
            continue

        year, month, day, hour, minute, second, _, _, _ = entry["published_parsed"]
        pub_date = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)

        if feed.newest_retrieved_date is None or pub_date > feed.newest_retrieved_date:
            url = entry.get("link", "(URL missing)")
            title = entry.get("title", "(Title missing)")

            feed.entries.append(Entry(url, title, pub_date))

            if newest_pub_date is None or pub_date > newest_pub_date:
                newest_pub_date = pub_date

    feed.entries.sort(key=lambda article: article.pub_date, reverse=True)
    feed.newest_retrieved_date = newest_pub_date


def save_feed_data(
    data_file: str, date_format: str, feed_data: dict[str, Feed]
) -> None:
    with open(data_file, "w", encoding="utf-8") as file:
        for feed in feed_data.values():
            if feed.newest_retrieved_date:
                data = f"{feed.url} last updated {feed.newest_retrieved_date.strftime(date_format)}"
            else:
                data = feed.url
            file.write(f"{data}\n")


def main() -> None:
    feed_file = FEED_FILE
    data_file = DATA_FILE
    date_format = DATE_FORMAT

    feeds = get_url_list(feed_file)

    if len(feeds) == 0:
        print(f"No URLs listed in {feed_file}; exiting.", file=sys.stderr)
        sys.exit(0)

    feed_data = get_feed_data(data_file, date_format, feeds)

    for feed in feed_data.values():
        if feed.is_enabled:
            update_feed(feed)

    save_feed_data(data_file, date_format, feed_data)

    feeds_without_new_articles = []

    for feed in feed_data.values():
        if not feed.is_enabled:
            continue

        if len(feed.entries) == 0:
            feeds_without_new_articles.append(feed)
            continue

        print(feed.get_info())

        for entry in feed.entries:
            print(entry.get_info())

        print()

    if len(feeds_without_new_articles) > 0:
        print("Feeds without new articles:")

        for feed in feeds_without_new_articles:
            if not feed.is_enabled:
                continue

            print(feed.get_info())


if __name__ == "__main__":
    main()
