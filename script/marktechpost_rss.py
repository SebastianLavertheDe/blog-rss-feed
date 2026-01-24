#!/usr/bin/env python3
"""Fetch external RSS feed and reformat with feedgen."""

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
        """Fetch RSS from URL and reformat with feedgen"""
        print(f"Fetching RSS from: {self.rss_url}")

        try:
            response = requests.get(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)
            channel = root.find('.//channel')
            if channel is None:
                channel = root

            feed = FeedGenerator()
            feed.title(self.feed_title)
            feed.link(href=self.feed_link, rel='alternate')
            feed.description(self.feed_description)
            feed.language('en')

            items = channel.findall('.//item')

            for item in items:
                try:
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    pub_date = item.find('pubDate')
                    guid = item.find('guid')

                    if title is None or link is None:
                        continue

                    title_text = title.text if title is not None else ''
                    link_text = link.text if link is not None else ''
                    description_text = description.text if description is not None else title_text
                    pub_date_text = pub_date.text if pub_date is not None else None
                    guid_text = guid.text if guid is not None else link_text

                    entry = feed.add_entry()
                    entry.title(title_text)
                    entry.link(href=link_text)
                    entry.description(description_text)
                    entry.guid(guid_text, permalink=True)

                    if pub_date_text:
                        parsed_date = self.parse_date(pub_date_text)
                        entry.pubDate(parsed_date)

                except Exception as e:
                    print(f"Warning: Error processing item: {e}")
                    continue

            os.makedirs('rss', exist_ok=True)
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
        rss_url='https://www.marktechpost.com/feed/',
        output_file='marktechpost_rss.xml',
        feed_title='MarkTechPost',
        feed_link='https://www.marktechpost.com',
        feed_description='Latest posts from MarkTechPost'
    )
    success = importer.fetch_and_reformat()

    if success:
        print("MarkTechPost RSS imported successfully!")
    else:
        print("Failed to import MarkTechPost RSS")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
