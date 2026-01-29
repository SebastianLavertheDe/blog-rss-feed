#!/usr/bin/env python3
"""Fetch external RSS feed from Reddit r/OpenAI and reformat with feedgen."""

import requests
import os
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import xml.etree.ElementTree as ET


class ExternalRSSImporter:
    def __init__(self, rss_url, output_file, feed_title, feed_link, feed_description):
        self.rss_url = rss_url
        self.output_file = output_file
        self.feed_title = feed_title
        self.feed_link = feed_link
        self.feed_description = feed_description

    def parse_date(self, date_str):
        """Parse various date formats"""
        from dateutil import parser as date_parser

        try:
            parsed_date = date_parser.parse(date_str)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except:
            return datetime.now(timezone.utc)

    def fetch_and_reformat(self):
        """Fetch RSS/Atom feed from URL and reformat with feedgen"""
        print(f"Fetching RSS from: {self.rss_url}")

        try:
            response = requests.get(
                self.rss_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                timeout=30,
            )
            response.raise_for_status()

            # Parse external feed
            root = ET.fromstring(response.content)

            # Create feedgen instance
            feed = FeedGenerator()
            feed.title(self.feed_title)
            feed.link(href=self.feed_link, rel="alternate")
            feed.description(self.feed_description)
            feed.language("en")

            # Detect feed type and parse accordingly
            items = []

            if root.tag == "{http://www.w3.org/2005/Atom}feed":
                # Atom feed format (Reddit)
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for entry in entries:
                    item = {}
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    link_elem = entry.find(
                        ".//{http://www.w3.org/2005/Atom}link[@href]"
                    )
                    content_elem = entry.find(".//{http://www.w3.org/2005/Atom}content")
                    updated_elem = entry.find("{http://www.w3.org/2005/Atom}updated")
                    id_elem = entry.find("{http://www.w3.org/2005/Atom}id")

                    item["title"] = title_elem.text if title_elem is not None else ""
                    item["link"] = (
                        link_elem.get("href") if link_elem is not None else ""
                    )
                    item["description"] = (
                        content_elem.text if content_elem is not None else item["title"]
                    )
                    item["pubDate"] = (
                        updated_elem.text if updated_elem is not None else None
                    )
                    item["guid"] = id_elem.text if id_elem is not None else item["link"]

                    if item["title"] and item["link"]:
                        items.append(item)

            else:
                # RSS format
                channel = root.find(".//channel")
                if channel is None:
                    channel = root

                rss_items = channel.findall(".//item")
                for item in rss_items:
                    item_dict = {}
                    title = item.find("title")
                    link = item.find("link")
                    description = item.find("description")
                    pub_date = item.find("pubDate")
                    guid = item.find("guid")

                    if title is None or link is None:
                        continue

                    item_dict["title"] = title.text if title is not None else ""
                    item_dict["link"] = link.text if link is not None else ""
                    item_dict["description"] = (
                        description.text
                        if description is not None
                        else item_dict["title"]
                    )
                    item_dict["pubDate"] = (
                        pub_date.text if pub_date is not None else None
                    )
                    item_dict["guid"] = (
                        guid.text if guid is not None else item_dict["link"]
                    )

                    items.append(item_dict)

            # Add entries to feed
            for item in items:
                try:
                    entry = feed.add_entry()
                    entry.title(item["title"])
                    entry.link(href=item["link"])
                    entry.description(item["description"])
                    entry.guid(item["guid"], permalink=True)

                    if item.get("pubDate"):
                        parsed_date = self.parse_date(item["pubDate"])
                        entry.pubDate(parsed_date)

                except Exception as e:
                    print(f"Warning: Error processing item: {e}")
                    continue

            # Create rss directory if it doesn't exist
            os.makedirs("rss", exist_ok=True)

            # Save to file with pretty print
            output_path = os.path.join("rss", self.output_file)
            rss_content = feed.rss_str(pretty=True)
            with open(output_path, "wb") as f:
                f.write(rss_content)

            print(f"✓ RSS saved to: {output_path}")
            print(f"  Processed {len(items)} items")
            return True

        except Exception as e:
            print(f"✗ Error fetching RSS: {e}")
            return False


def main():
    importer = ExternalRSSImporter(
        rss_url="https://www.reddit.com/r/OpenAI/hot/.rss?limit=50",
        output_file="openai_reddit_rss.xml",
        feed_title="Reddit r/OpenAI",
        feed_link="https://www.reddit.com/r/OpenAI",
        feed_description="Reddit posts from r/OpenAI subreddit",
    )
    success = importer.fetch_and_reformat()

    if success:
        print("Reddit r/OpenAI RSS imported successfully!")
    else:
        print("Failed to import Reddit r/OpenAI RSS")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
