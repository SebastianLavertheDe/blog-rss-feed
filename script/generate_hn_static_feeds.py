#!/usr/bin/env python3
"""Generate static_feeds configuration for HN Popular Blogs."""

import requests
import xml.etree.ElementTree as ET
import yaml


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
                'xmlUrl': outline.get('xmlUrl'),
                'htmlUrl': outline.get('htmlUrl', ''),
            }
            feeds.append(feed_info)

        print(f"Found {len(feeds)} RSS feeds in OPML\n")
        return feeds

    except Exception as e:
        print(f"Error parsing OPML: {e}")
        return []


def main():
    opml_url = 'https://gist.githubusercontent.com/emschwartz/e6d2bf860ccc367fe37ff953ba6de66b/raw/hn-popular-blogs-2025.opml'

    # Parse OPML
    feeds = parse_opml(opml_url)

    if not feeds:
        print("No feeds found in OPML")
        return 1

    # Generate static_feeds YAML
    print("="*60)
    print("Add this to config.yaml under opml.outputs[0].static_feeds:")
    print("="*60)
    print()

    # Convert to YAML format
    static_feeds = []
    for feed in feeds:
        static_feeds.append({
            'title': feed['title'],
            'xmlUrl': feed['xmlUrl'],
            'htmlUrl': feed['htmlUrl']
        })

    # Print YAML
    yaml_str = yaml.dump(static_feeds, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Add proper indentation for config.yaml
    lines = yaml_str.split('\n')
    indented_lines = ['        ' + line if line and not line.startswith('  ') else '      ' + line for line in lines]
    print('\n'.join(indented_lines))

    print()
    print("="*60)
    print(f"Total: {len(feeds)} feeds")
    print("="*60)

    return 0


if __name__ == "__main__":
    exit(main())
