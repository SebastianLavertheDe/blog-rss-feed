#!/usr/bin/env python3
"""Fetch external Atom feed from hey.com and reformat with feedgen."""

import requests
import os
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import xml.etree.ElementTree as ET


class AtomRSSImporter:
    def __init__(self, atom_url, output_file, feed_title, feed_link, feed_description):
        self.atom_url = atom_url
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
        """Fetch Atom feed from URL and reformat with feedgen"""
        print(f"Fetching Atom feed from: {self.atom_url}")

        try:
            response = requests.get(
                self.atom_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                timeout=30,
            )
            response.raise_for_status()

            # Parse the Atom feed
            root = ET.fromstring(response.content)

            # Create feedgen instance
            feed = FeedGenerator()
            feed.title(self.feed_title)
            feed.link(href=self.feed_link, rel="alternate")
            feed.description(self.feed_description)
            feed.language("en")

            # Find all entries in Atom format
            entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

            for entry in entries:
                try:
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    link_elem = entry.find(
                        ".//{http://www.w3.org/2005/Atom}link[@rel='alternate']"
                    )
                    content_elem = entry.find("{http://www.w3.org/2005/Atom}content")
                    published_elem = entry.find(
                        "{http://www.w3.org/2005/Atom}published"
                    )
                    updated_elem = entry.find("{http://www.w3.org/2005/Atom}updated")
                    id_elem = entry.find("{http://www.w3.org/2005/Atom}id")

                    if title_elem is None or link_elem is None:
                        continue

                    title_text = title_elem.text if title_elem is not None else ""
                    link_text = link_elem.get("href") if link_elem is not None else ""
                    content_text = (
                        content_elem.text if content_elem is not None else title_text
                    )

                    # Try to parse date, prefer published over updated
                    pub_date_text = None
                    if published_elem is not None:
                        pub_date_text = published_elem.text
                    elif updated_elem is not None:
                        pub_date_text = updated_elem.text

                    guid_text = id_elem.text if id_elem is not None else link_text

                    # Add entry
                    feed_entry = feed.add_entry()
                    feed_entry.title(title_text)
                    feed_entry.link(href=link_text)
                    feed_entry.description(content_text)
                    feed_entry.guid(guid_text, permalink=True)

                    if pub_date_text:
                        parsed_date = self.parse_date(pub_date_text)
                        feed_entry.pubDate(parsed_date)

                except Exception as e:
                    print(f"Warning: Error processing entry: {e}")
                    continue

            # Create rss directory if it doesn't exist
            os.makedirs("rss", exist_ok=True)

            # Save to file with pretty print
            output_path = os.path.join("rss", self.output_file)
            rss_content = feed.rss_str(pretty=True)
            with open(output_path, "wb") as f:
                f.write(rss_content)

            print(f"✓ RSS saved to: {output_path}")
            print(f"  Processed {len(entries)} entries")
            return True

        except Exception as e:
            print(f"✗ Error fetching Atom feed: {e}")
            return False


def main():
    importer = AtomRSSImporter(
        atom_url="https://world.hey.com/dhh/feed.atom",
        output_file="david_heinemeier_hansson_rss.xml",
        feed_title="David Heinemeier Hansson",
        feed_link="https://world.hey.com/dhh",
        feed_description="Blog posts from David Heinemeier Hansson",
    )
    success = importer.fetch_and_reformat()

    if success:
        print("David Heinemeier Hansson RSS imported successfully!")
    else:
        print("Failed to import David Heinemeier Hansson RSS")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
