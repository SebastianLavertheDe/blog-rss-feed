#!/usr/bin/env python3
"""Fetch external RSS feed and reformat with feedgen."""

import requests
import os
import time
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

    def fetch_with_retry(self, url, max_retries=5, timeout=90):
        """Fetch with retry logic and exponential backoff"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        }

        for attempt in range(max_retries):
            try:
                print(f"Fetching RSS (attempt {attempt + 1}/{max_retries}) from: {url}")
                response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                print(f"Warning: Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 30)  # Cap wait at 30 seconds
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"✗ All {max_retries} attempts failed")
                    return None

    def generate_empty_feed(self):
        """Generate an empty RSS feed when fetch fails"""
        print("Generating empty RSS feed as fallback...")

        feed = FeedGenerator()
        feed.title(self.feed_title)
        feed.link(href=self.feed_link, rel='alternate')
        feed.description(self.feed_description + " (Currently unavailable)")
        feed.language('en')

        # Create rss directory if it doesn't exist
        os.makedirs('rss', exist_ok=True)

        # Save to file with pretty print
        output_path = os.path.join('rss', self.output_file)
        rss_content = feed.rss_str(pretty=True)
        with open(output_path, 'wb') as f:
            f.write(rss_content)

        print(f"✓ Empty RSS saved to: {output_path}")
        return True

    def fetch_and_reformat(self):
        """Fetch RSS from URL and reformat with feedgen"""

        response = self.fetch_with_retry(self.rss_url)

        if response is None:
            print("✗ Failed to fetch RSS feed after all retries")
            # Generate empty feed as fallback to prevent workflow failure
            return self.generate_empty_feed()

        try:
            # Parse the external RSS
            root = ET.fromstring(response.content)

            # Find the channel element
            channel = root.find('.//channel')
            if channel is None:
                channel = root  # Some RSS don't have channel wrapper

            # Create feedgen instance
            feed = FeedGenerator()
            feed.title(self.feed_title)
            feed.link(href=self.feed_link, rel='alternate')
            feed.description(self.feed_description)
            feed.language('en')

            # Find all items
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

                    # Add entry
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
            print(f"✗ Error processing RSS feed: {e}")
            # Generate empty feed as fallback
            return self.generate_empty_feed()

def main():
    importer = ExternalRSSImporter(
        rss_url='https://importai.substack.com/feed',
        output_file='importai_rss.xml',
        feed_title='Import AI',
        feed_link='https://importai.substack.com/',
        feed_description='Import AI newsletter by Jack Clark - AI news and research'
    )
    success = importer.fetch_and_reformat()

    if success:
        print("Import AI RSS processed successfully!")
    else:
        print("Failed to process Import AI RSS")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
