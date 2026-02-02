#!/usr/bin/env python3
"""Import all RSS feeds from HN Popular Blogs OPML and generate individual RSS files."""

import requests
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from dateutil import parser as date_parser
import re
import fcntl
import time


class ExternalRSSImporter:
    def __init__(self, rss_url, output_file, feed_title, feed_link, feed_description):
        self.rss_url = rss_url
        self.output_file = output_file
        self.feed_title = feed_title
        self.feed_link = feed_link
        self.feed_description = feed_description

    def parse_date(self, date_str):
        """Parse various date formats"""
        try:
            parsed_date = date_parser.parse(date_str)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except:
            return datetime.now(timezone.utc)

    def fetch_and_reformat(self):
        """Fetch RSS from URL and reformat with ElementTree"""
        try:
            response = requests.get(self.rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
            response.raise_for_status()

            # Parse the external RSS
            root = ET.fromstring(response.content)

            # Handle both RSS and Atom feeds
            if root.tag == '{http://www.w3.org/2005/Atom}feed':
                return self.process_atom_feed(root)
            else:
                return self.process_rss_feed(root)

        except Exception as e:
            print(f"  ✗ Error fetching {self.feed_title}: {e}")
            return False

    def process_rss_feed(self, root):
        """Process RSS 2.0 feed"""
        # Find the channel element
        channel = root.find('.//channel')
        if channel is None:
            channel = root

        # Create new RSS with ElementTree
        new_rss = ET.Element('rss', attrib={'version': '2.0'})
        new_channel = ET.SubElement(new_rss, 'channel')

        ET.SubElement(new_channel, 'title').text = self.feed_title
        ET.SubElement(new_channel, 'link').text = self.feed_link
        ET.SubElement(new_channel, 'description').text = self.feed_description
        ET.SubElement(new_channel, 'language').text = 'en'
        ET.SubElement(new_channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))

        # Find all items
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
                continue

        # Sort items by date (newest first)
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

        return self.save_rss(new_rss, len(parsed_items))

    def process_atom_feed(self, root):
        """Process Atom feed"""
        # Create new RSS with ElementTree
        new_rss = ET.Element('rss', attrib={'version': '2.0'})
        new_channel = ET.SubElement(new_rss, 'channel')

        ET.SubElement(new_channel, 'title').text = self.feed_title
        ET.SubElement(new_channel, 'link').text = self.feed_link
        ET.SubElement(new_channel, 'description').text = self.feed_description
        ET.SubElement(new_channel, 'language').text = 'en'
        ET.SubElement(new_channel, 'lastBuildDate').text = format_datetime(datetime.now(timezone.utc))

        # Find all entries
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('.//atom:entry', ns)

        # Parse all entries
        parsed_items = []
        for entry in entries:
            try:
                title = entry.find('atom:title', ns)
                link = entry.find('atom:link[@rel="alternate"]', ns)
                if link is None:
                    link = entry.find('atom:link', ns)
                content = entry.find('atom:content', ns)
                if content is None:
                    content = entry.find('atom:summary', ns)
                updated = entry.find('atom:updated', ns)
                if updated is None:
                    updated = entry.find('atom:published', ns)
                entry_id = entry.find('atom:id', ns)

                if title is None or link is None:
                    continue

                title_text = title.text if title is not None else ''
                link_text = link.get('href') if link is not None else ''
                description_text = content.text if content is not None else title_text
                updated_text = updated.text if updated is not None else None
                guid_text = entry_id.text if entry_id is not None else link_text

                parsed_date = None
                if updated_text:
                    parsed_date = self.parse_date(updated_text)

                parsed_items.append({
                    'title': title_text,
                    'link': link_text,
                    'description': description_text,
                    'guid': guid_text,
                    'pub_date': parsed_date
                })

            except Exception as e:
                continue

        # Sort items by date (newest first)
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

        return self.save_rss(new_rss, len(parsed_items))

    def save_rss(self, rss_element, item_count):
        """Save RSS to file"""
        try:
            # Create rss directory if it doesn't exist
            os.makedirs('rss', exist_ok=True)

            # Save to file with pretty print
            output_path = os.path.join('rss', self.output_file)
            xml_bytes = ET.tostring(rss_element, encoding='utf-8', xml_declaration=True)

            # Pretty print
            parsed = ET.fromstring(xml_bytes)
            ET.indent(parsed, space='  ')
            with open(output_path, 'wb') as f:
                f.write(ET.tostring(parsed, encoding='utf-8', xml_declaration=True))

            print(f"  ✓ {self.feed_title} ({item_count} items)")
            return True

        except Exception as e:
            print(f"  ✗ Error saving {self.feed_title}: {e}")
            return False


def sanitize_filename(name):
    """Convert feed name to valid filename"""
    # Remove special characters and convert to lowercase
    name = re.sub(r'[^\w\s-]', '', name.lower())
    # Replace spaces with underscores
    name = re.sub(r'[-\s]+', '_', name)
    return name


def parse_opml(opml_url):
    """Parse OPML file and extract all RSS feeds"""
    print(f"Fetching OPML from: {opml_url}")

    try:
        response = requests.get(opml_url, timeout=30)
        response.raise_for_status()

        root = ET.fromstring(response.content)

        # Find all outline elements with xmlUrl attribute
        feeds = []
        for outline in root.findall('.//outline[@xmlUrl]'):
            feed_info = {
                'title': outline.get('text') or outline.get('title', 'Unknown'),
                'rss_url': outline.get('xmlUrl'),
                'html_url': outline.get('htmlUrl', ''),
            }
            feeds.append(feed_info)

        print(f"Found {len(feeds)} RSS feeds in OPML\n")
        return feeds

    except Exception as e:
        print(f"Error parsing OPML: {e}")
        return []


def generate_config_entries(feeds):
    """Generate config.yaml entries for all feeds"""
    print("\n" + "="*60)
    print("Config entries to add to config.yaml:")
    print("="*60)

    for feed in feeds:
        filename = sanitize_filename(feed['title'])
        print(f"""
  - name: {feed['title']}
    file: hn_popular_blogs_rss.py
    output: hn_{filename}_rss.xml
    title: {feed['title']}
    category: blog
    enabled: true""")

    print("\n" + "="*60)


def main():
    opml_url = 'https://gist.githubusercontent.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b/raw/hn-popular-blogs-2025.opml'

    # Use a lock file to ensure only one instance runs at a time
    lock_file_path = '/tmp/hn_popular_blogs_rss.lock'

    try:
        lock_file = open(lock_file_path, 'w')

        # Try to acquire an exclusive lock (non-blocking)
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Another instance is running, just exit successfully
            print("Another instance is already running. Skipping.")
            return 0

        # Parse OPML
        feeds = parse_opml(opml_url)

        if not feeds:
            print("No feeds found in OPML")
            return 1

        # Process each feed
        success_count = 0
        fail_count = 0

        print("Processing feeds:")
        print("-" * 60)

        for feed in feeds:
            filename = sanitize_filename(feed['title'])
            output_file = f"hn_{filename}_rss.xml"

            importer = ExternalRSSImporter(
                rss_url=feed['rss_url'],
                output_file=output_file,
                feed_title=feed['title'],
                feed_link=feed['html_url'] or feed['rss_url'],
                feed_description=f"RSS feed from {feed['title']}"
            )

            if importer.fetch_and_reformat():
                success_count += 1
            else:
                fail_count += 1

        print("-" * 60)
        print(f"\nSummary: {success_count} succeeded, {fail_count} failed")

        # Generate config entries
        generate_config_entries(feeds)

        # Release the lock
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        os.remove(lock_file_path)

        return 0 if fail_count == 0 else 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
