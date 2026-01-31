#!/usr/bin/env python3
"""Import AI RSS feed generator with robust parsing."""

import re
import os
import time
import requests
import feedparser
from email.utils import format_datetime
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

FEED_URL = "https://importai.substack.com/feed"
OUTPUT_FILE = "importai_rss.xml"
FEED_TITLE = "Import AI"
FEED_LINK = "https://importai.substack.com/"
FEED_DESC = "Import AI newsletter by Jack Clark - AI news and research"

# Remove invalid XML 1.0 chars
INVALID_XML_RE = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

def clean_xml_text(s: str) -> str:
    """Remove invalid XML characters."""
    if not s:
        return ""
    s = INVALID_XML_RE.sub("", s)
    return s

def fetch(url: str, max_retries=5, timeout=90) -> bytes:
    """Fetch feed with retry logic."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; rss-generator/1.0; +https://github.com/)",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    }

    for attempt in range(max_retries):
        try:
            print(f"Fetching RSS (attempt {attempt + 1}/{max_retries}) from: {url}")
            r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            r.raise_for_status()
            return r.content
        except requests.exceptions.RequestException as e:
            print(f"Warning: Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                print(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise

def build_rss(parsed: feedparser.FeedParserDict) -> bytes:
    """Build RSS XML from parsed feed."""
    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")

    title = parsed.feed.get("title", FEED_TITLE)
    link = parsed.feed.get("link", FEED_LINK)
    desc = parsed.feed.get("subtitle", parsed.feed.get("description", FEED_DESC))

    ET.SubElement(channel, "title").text = clean_xml_text(title)
    ET.SubElement(channel, "link").text = clean_xml_text(link)
    ET.SubElement(channel, "description").text = clean_xml_text(desc)

    now = datetime.now(timezone.utc)
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(now)

    # Sort entries by date (newest first)
    sorted_entries = sorted(
        parsed.entries[:30],
        key=lambda e: (
            e.get("published_parsed") or e.get("updated_parsed") or (0, 0, 0, 0, 0, 0)
        ),
        reverse=True
    )

    count = 0
    for e in sorted_entries:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = clean_xml_text(e.get("title", ""))
        ET.SubElement(item, "link").text = clean_xml_text(e.get("link", ""))

        guid_val = e.get("id") or e.get("guid") or e.get("link", "")
        guid = ET.SubElement(item, "guid", attrib={"isPermaLink": "false"})
        guid.text = clean_xml_text(guid_val)

        # pubDate
        published_parsed = e.get("published_parsed") or e.get("updated_parsed")
        if published_parsed:
            dt = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        else:
            dt = now
        ET.SubElement(item, "pubDate").text = format_datetime(dt)

        # description: prefer summary
        summary = e.get("summary", "")
        ET.SubElement(item, "description").text = clean_xml_text(summary)
        count += 1

    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    return xml_bytes, count

def generate_empty_feed() -> bool:
    """Generate empty RSS feed as fallback."""
    print("Generating empty RSS feed as fallback...")

    rss = ET.Element("rss", attrib={"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = FEED_TITLE
    ET.SubElement(channel, "link").text = FEED_LINK
    ET.SubElement(channel, "description").text = FEED_DESC + " (Currently unavailable)"

    os.makedirs("rss", exist_ok=True)
    output_path = os.path.join("rss", OUTPUT_FILE)
    xml_bytes = ET.tostring(rss, encoding="utf-8", xml_declaration=True)

    with open(output_path, "wb") as f:
        f.write(xml_bytes)

    print(f"✓ Empty RSS saved to: {output_path}")
    return True

def main():
    """Main entry point."""
    try:
        # Fetch feed
        raw = fetch(FEED_URL)

        # Parse with feedparser
        parsed = feedparser.parse(raw)

        if parsed.bozo and parsed.bozo_exception:
            print(f"Warning: Feed parse error: {parsed.bozo_exception}")
            print("Attempting to continue anyway...")

        # Build RSS
        out, count = build_rss(parsed)

        # Save output
        os.makedirs("rss", exist_ok=True)
        output_path = os.path.join("rss", OUTPUT_FILE)

        with open(output_path, "wb") as f:
            f.write(out)

        print(f"✓ RSS saved to: {output_path}")
        print(f"  Processed {count} items")
        print("Import AI RSS processed successfully!")
        return 0

    except Exception as e:
        print(f"✗ Error processing Import AI RSS: {e}")
        # Generate empty feed as fallback to prevent workflow failure
        return 0 if generate_empty_feed() else 1

if __name__ == "__main__":
    exit(main())
