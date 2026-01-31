#!/usr/bin/env python3
"""Fetch external RSS feed and reformat with ElementTree."""

import requests
import os
from datetime import datetime, timezone
from email.utils import format_datetime
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
        """Fetch RSS from URL and reformat with ElementTree"""
        print(f"Fetching RSS from: {self.rss_url}")

        try:
            response = requests.get(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            # Parse the external RSS
            root = ET.fromstring(response.content)

            # Find the channel element
            channel = root.find('.//channel')
            if channel is None:
                channel = root  # Some RSS don't have channel wrapper

            # Create new RSS with ElementTree
            new_rss = ET.Element('rss', attrib={'version': '2.0'})
            new_channel = ET.SubElement(new_rss, 'channel')

            ET.SubElement(new_channel, 'title').text = self.feed_title
            ET.SubElement(new_channel, 'link').text = self.feed_link
            ET.SubElement(new_channel, 'description').text = self.feed_description
            ET.SubElement(new_channel, 'language').text = 'en'
            ET.SubElement(new_channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))

            # Find all items and collect them for sorting
            items = channel.findall('.//item')

            # Parse all items first for sorting
            parsed_items = []
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

                    parsed_date = None
                    if pub_date_text:
                        parsed_date = self.parse_date(pub_date_text)

                    parsed_items.append({
                        'title': title_text,
                        'link': link_text,
                        'description': description_text,
                        'guid': guid_text,
                        'pub_date': parsed_date
                    })

                except Exception as e:
                    print(f"Warning: Error processing item: {e}")
                    continue

            # Sort items by date (newest first), items without dates go last
            parsed_items.sort(key=lambda x: x['pub_date'] if x['pub_date'] else datetime.min.replace(tzinfo=timezone.utc), reverse=True)

            # Add sorted entries to channel
            for item_data in parsed_items:
                item_elem = ET.SubElement(new_channel, 'item')
                ET.SubElement(item_elem, 'title').text = item_data['title']
                ET.SubElement(item_elem, 'link').text = item_data['link']
                ET.SubElement(item_elem, 'description').text = item_data['description']
                guid_elem = ET.SubElement(item_elem, 'guid', attrib={'isPermaLink': 'true'})
                guid_elem.text = item_data['guid']

                if item_data['pub_date']:
                    ET.SubElement(item_elem, 'pubDate').text = format_datetime(item_data['pub_date'])

            # Create rss directory if it doesn't exist
            os.makedirs('rss', exist_ok=True)

            # Save to file with pretty print
            output_path = os.path.join('rss', self.output_file)
            xml_bytes = ET.tostring(new_rss, encoding='utf-8', xml_declaration=True)

            # Pretty print by parsing and re-serializing
            parsed = ET.fromstring(xml_bytes)
            ET.indent(parsed, space='  ')
            with open(output_path, 'wb') as f:
                f.write(ET.tostring(parsed, encoding='utf-8', xml_declaration=True))

            print(f"✓ RSS saved to: {output_path}")
            print(f"  Processed {len(items)} items")
            return True

        except Exception as e:
            print(f"✗ Error fetching RSS: {e}")
            return False

def main():
    importer = ExternalRSSImporter(
        rss_url='https://tldr.tech/api/rss/tech',
        output_file='tldr_tech_rss.xml',
        feed_title='TLDR Tech Newsletter',
        feed_link='https://tldr.tech',
        feed_description='Daily tech news summaries from TLDR'
    )
    success = importer.fetch_and_reformat()

    if success:
        print("TLDR Tech RSS imported successfully!")
    else:
        print("Failed to import TLDR Tech RSS")

    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
