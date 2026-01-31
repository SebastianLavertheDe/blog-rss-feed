#!/usr/bin/env python3
"""Fetch external RSS/Atom feed and reformat with ElementTree."""

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
        """Fetch RSS/Atom feed from URL and reformat with ElementTree"""
        print(f"Fetching RSS from: {self.rss_url}")

        try:
            response = requests.get(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            # Parse the external feed
            root = ET.fromstring(response.content)

            # Create new RSS with ElementTree
            new_rss = ET.Element('rss', attrib={'version': '2.0'})
            new_channel = ET.SubElement(new_rss, 'channel')

            ET.SubElement(new_channel, 'title').text = self.feed_title
            ET.SubElement(new_channel, 'link').text = self.feed_link
            ET.SubElement(new_channel, 'description').text = self.feed_description
            ET.SubElement(new_channel, 'language').text = 'en'
            ET.SubElement(new_channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))

            # Detect feed type and parse accordingly
            parsed_items = []

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
                    pub_date_text = None
                    if published_elem is not None and published_elem.text:
                        pub_date_text = published_elem.text
                    elif updated_elem is not None and updated_elem.text:
                        pub_date_text = updated_elem.text

                    parsed_date = None
                    if pub_date_text:
                        parsed_date = self.parse_date(pub_date_text)

                    item["guid"] = id_elem.text if id_elem is not None else item["link"]
                    item["pub_date"] = parsed_date

                    if item["title"] and item["link"]:
                        parsed_items.append(item)

            else:
                # RSS format
                channel = root.find('.//channel')
                if channel is None:
                    channel = root

                rss_items = channel.findall('.//item')
                for item_elem in rss_items:
                    title = item_elem.find('title')
                    link = item_elem.find('link')
                    description = item_elem.find('description')
                    pub_date = item_elem.find('pubDate')
                    guid = item_elem.find('guid')

                    if title is None or link is None:
                        continue

                    pub_date_text = pub_date.text if pub_date is not None else None
                    parsed_date = None
                    if pub_date_text:
                        parsed_date = self.parse_date(pub_date_text)

                    parsed_items.append({
                        'title': title.text if title is not None else "",
                        'link': link.text if link is not None else "",
                        'description': description.text if description is not None else (title.text if title is not None else ""),
                        'guid': guid.text if guid is not None else (link.text if link is not None else ""),
                        'pub_date': parsed_date
                    })

            # Sort items by date (newest first), items without dates go last
            parsed_items.sort(key=lambda x: x['pub_date'] if x.get('pub_date') else datetime.min.replace(tzinfo=timezone.utc), reverse=True)

            # Add sorted entries to channel
            for item in parsed_items:
                try:
                    item_elem = ET.SubElement(new_channel, 'item')
                    ET.SubElement(item_elem, 'title').text = item["title"]
                    ET.SubElement(item_elem, 'link').text = item["link"]
                    ET.SubElement(item_elem, 'description').text = item["description"]
                    guid_elem = ET.SubElement(item_elem, 'guid', attrib={'isPermaLink': 'true'})
                    guid_elem.text = item["guid"]

                    if item.get("pub_date"):
                        ET.SubElement(item_elem, 'pubDate').text = format_datetime(item["pub_date"])

                except Exception as e:
                    print(f"Warning: Error processing item: {e}")
                    continue

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
            print(f"  Processed {len(parsed_items)} items")
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
