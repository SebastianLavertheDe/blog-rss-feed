#!/usr/bin/env python3
"""Fetch external RSS/Atom feed and reformat with feedgen."""

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
            response = requests.get(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            # Parse the external feed
            root = ET.fromstring(response.content)

            # Create feedgen instance
            feed = FeedGenerator()
            feed.title(self.feed_title)
            feed.link(href=self.feed_link, rel='alternate')
            feed.description(self.feed_description)
            feed.language('en')

            # Detect feed type and parse accordingly
            items = []

            if root.tag == "{http://www.w3.org/2005/Atom}feed":
                # Atom feed format
                entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                for entry in entries:
                    item = {}
                    title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                    link_elem = entry.find(".//{http://www.w3.org/2005/Atom}link[@href]")
                    content_elem = entry.find(".//{http://www.w3.org/2005/Atom}content")
                    summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
                    updated_elem = entry.find("{http://www.w3.org/2005/Atom}updated")
                    published_elem = entry.find("{http://www.w3.org/2005/Atom}published")
                    id_elem = entry.find("{http://www.w3.org/2005/Atom}id")

                    item["title"] = title_elem.text if title_elem is not None else ""
                    item["link"] = link_elem.get("href") if link_elem is not None else ""

                    # Try content first, then summary, then title
                    if content_elem is not None and content_elem.text:
                        item["description"] = content_elem.text
                    elif summary_elem is not None and summary_elem.text:
                        item["description"] = summary_elem.text
                    else:
                        item["description"] = item["title"]

                    # Use published date if available, otherwise updated
                    if published_elem is not None and published_elem.text:
                        item["pubDate"] = published_elem.text
                    elif updated_elem is not None and updated_elem.text:
                        item["pubDate"] = updated_elem.text
                    else:
                        item["pubDate"] = None

                    item["guid"] = id_elem.text if id_elem is not None else item["link"]

                    if item["title"] and item["link"]:
                        items.append(item)

            else:
                # RSS format
                channel = root.find('.//channel')
                if channel is None:
                    channel = root

                rss_items = channel.findall('.//item')
                for item_elem in rss_items:
                    item_dict = {}
                    title = item_elem.find('title')
                    link = item_elem.find('link')
                    description = item_elem.find('description')
                    pub_date = item_elem.find('pubDate')
                    guid = item_elem.find('guid')

                    if title is None or link is None:
                        continue

                    item_dict["title"] = title.text if title is not None else ""
                    item_dict["link"] = link.text if link is not None else ""
                    item_dict["description"] = description.text if description is not None else item_dict["title"]
                    item_dict["pubDate"] = pub_date.text if pub_date is not None else None
                    item_dict["guid"] = guid.text if guid is not None else item_dict["link"]

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
            os.makedirs('rss', exist_ok=True)

            # Save to file with pretty print
            output_path = os.path.join('rss', self.output_file)
            rss_content = feed.rss_str(pretty=True)
            with open(output_path, 'wb') as f:
                f.write(rss_content)

            print(f"✓ RSS saved to: {output_path}")
            print(f"  Processed {len(items)} items")
            return True

        except Exception as e:
            print(f"✗ Error fetching RSS: {e}")
            return False

def main():
    importer = ExternalRSSImporter(
        rss_url='https://www.theverge.com/rss/ai-artificial-intelligence/index.xml',
        output_file='verge_ai_rss.xml',
        feed_title='The Verge AI',
        feed_link='https://www.theverge.com/ai-artificial-intelligence',
        feed_description='AI news and insights from The Verge'
    )
    success = importer.fetch_and_reformat()

    if success:
        print("The Verge AI RSS imported successfully!")
    else:
        print("Failed to import The Verge AI RSS")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
