---
name: rss-feed-converter
description: Convert any URL to an RSS feed. Detects if URL is an existing RSS feed (uses external_rss_importer.py) or a web page requiring scraping (creates a custom scraper script). Use when user asks to add a new RSS feed source, convert a website URL to RSS, create an RSS generator for a blog without feeds, or import an external RSS feed into the blog-rss-feed project.
---

# RSS Feed Converter

## Quick Start

When a user provides a URL to convert to RSS:

1. **Detect URL type**: Check if URL is already an RSS feed or a web page
2. **If RSS feed**: Use `external_rss_importer.py` script
3. **If web page**: Create a custom scraping script following the template

## Workflow Decision Tree

```
User provides URL
    |
    v
Is it an RSS feed? (ends in .rss, .xml, /feed, /rss, contains rss+xml)
    |
    +-- YES --> Use external_rss_importer.py
    |              |
    |              v
    |          Add to config.yaml with rssUrl parameter
    |
    +-- NO --> Create custom scraper script
                   |
                   v
               Follow scraping pattern (like cursor_rss.py)
```

## Enhanced RSS Detection Rules

Use these checks in order. If any check passes, treat it as an RSS/Atom feed and use `external_rss_importer.py`.

1. **HTTP headers (strong signal)**: `Content-Type` includes `application/rss+xml`, `application/atom+xml`, or `application/xml` with feed content.
2. **Body sniff (strong signal)**: Response starts with `<rss`, `<feed`, or `<rdf:RDF` (RSS 1.0) after trimming BOM/whitespace.
3. **URL heuristics (weak signal)**: Ends with `.rss` / `.xml`, or contains `/feed`, `/rss`, `/atom`.
4. **HTML feed discovery**: If the URL is an HTML page, look for:
   - `<link rel="alternate" type="application/rss+xml" href="...">`
   - `<link rel="alternate" type="application/atom+xml" href="...">`
   If found, use that feed URL with `external_rss_importer.py` instead of scraping.

If none match and the page is HTML, treat it as a web page and create a custom scraper script.

## Naming Conventions (Normalize Names)

Define a `site_key` once and reuse it everywhere. Use lowercase ASCII `snake_case` (no spaces, no hyphens).

- **Script file**: `script/{site_key}_rss.py`
- **Output file**: `rss/{site_key}_rss.xml`
- **Config entry**:
  - `file: {site_key}_rss.py`
  - `output: {site_key}_rss.xml`
  - `name:` and `title:` use human-readable Title Case

Example:
```yaml
- name: Example Blog
  file: example_blog_rss.py
  output: example_blog_rss.xml
  title: Example Blog
  category: blog
  enabled: true
```

## Using external_rss_importer.py (For existing RSS feeds)

When the URL is already an RSS feed, use the generic importer.

**Command line usage:**
```bash
python script/external_rss_importer.py \
  --rss-url "https://example.com/feed.xml" \
  --output "example_rss.xml" \
  --title "Example Blog"
```

**Add to config.yaml:**
```yaml
- name: Example Blog
  file: external_rss_importer.py
  output: example_blog_rss.xml
  title: Example Blog
  category: blog
  enabled: true
  rssUrl: https://example.com/feed.xml
```

**Optional parameters:**
- `args: ["--use-atom"]` - For Atom feeds
- `args: ["--use-feedparser"]` - Use feedparser library
- `args: ["--max-retries", "5"]` - Increase retry attempts

## Creating Custom Scraper Scripts (For web pages)

When the URL is a web page without RSS, create a custom scraping script.

### Script Template

Use this template based on `script/cursor_rss.py`:

```python
import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import os

class SiteRSSGenerator:
    def __init__(self):
        self.base_url = "https://example.com/blog"

    def parse_date(self, date_text):
        """Parse date text and return a datetime object with timezone"""
        try:
            parsed_date = date_parser.parse(date_text, tzinfos={"UT": timezone.utc, "UTC": timezone.utc})
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except Exception as e:
            print(f"Error parsing date '{date_text}': {e}")
            return datetime.now(timezone.utc)

    async def fetch_posts(self):
        response = requests.get(self.base_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles_data = []
        seen_urls = set()

        # Define CSS selectors for article links
        selectors = [
            'a[href*="/blog/"]',
            'article a',
            '[class*="post"] a',
        ]

        for selector in selectors:
            for link in soup.select(selector):
                try:
                    url = link.get('href')
                    title = link.get_text(strip=True)

                    if not url or not title or url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Build full URL if relative
                    if not url.startswith('http'):
                        if url.startswith('/'):
                            url = f"https://example.com{url}"
                        else:
                            url = f"https://example.com/{url}"

                    # Extract date from near the link
                    date_text = None
                    # TODO: Add site-specific date extraction logic here

                    parsed_date = datetime.now(timezone.utc)
                    if date_text:
                        parsed_date = self.parse_date(date_text)

                    articles_data.append({
                        'title': title,
                        'url': url,
                        'date': parsed_date,
                    })

                except Exception as e:
                    print(f"Error processing element: {e}")
                    continue

        # Sort by date (newest first)
        articles_data.sort(key=lambda x: x['date'], reverse=True)
        return articles_data

    def create_feed(self):
        feed = FeedGenerator()
        feed.title('Site Name Blog')
        feed.link(href=self.base_url, rel='alternate')
        feed.description('Latest posts from Site Name')
        feed.language('en')
        return feed

    def generate_rss(self, articles_data):
        feed = self.create_feed()
        for article in articles_data:
            entry = feed.add_entry(order='append')
            entry.title(article['title'])
            entry.link(href=article['url'])
            entry.pubDate(article['date'])
            entry.description(article['title'])
            entry.guid(article['url'], permalink=True)
        return feed.rss_str(pretty=True)

async def main():
    generator = SiteRSSGenerator()
    articles_data = await generator.fetch_posts()
    rss_content = generator.generate_rss(articles_data)

    os.makedirs('rss', exist_ok=True)
    with open('rss/site_name_rss.xml', 'wb') as f:
        f.write(rss_content)

    print(f"RSS feed generated with {len(articles_data)} articles!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Key Customization Points

1. **CSS Selectors**: Modify `selectors` list to match the site's HTML structure
2. **URL Building**: Update base URL and relative URL handling
3. **Date Extraction**: Add site-specific logic to find dates
4. **Feed Metadata**: Set correct title, description in `create_feed()`

## Adding to config.yaml

After creating the script, add it to `config.yaml`:

```yaml
- name: Site Name
  file: site_name_rss.py
  output: site_name_rss.xml
  title: Site Name Blog
  category: blog
  enabled: true
```

## Testing

Test the new RSS source:

```bash
# Test script directly
python script/your_script.py

# Run all feeds
python run_all.py

# Check output
cat rss/your_output.xml
```

## Common Patterns by Site Type

### WordPress Blogs

Selectors: `'.post-title a', 'h2 a', 'h1 a'`
Date: Often in `.post-date`, `time[datetime]`, or `.entry-date`

### Medium/Substack

Selectors: `'h3 a', '.title a'`
Date: Usually in `time` element or near title

### Generic Blogs

Start with generic selectors and inspect HTML:
- `'article a'` - Links inside article tags
- `'[class*="post"] a'` - Links in post containers
- `'h1 a', h2 a, h3 a'` - Heading links

## Resources

### scripts/

No bundled scripts - all scripts are in the main project at `script/`.

### references/

No additional references needed - see existing scripts for examples:
- `script/cursor_rss.py` - Web scraping example
- `script/external_rss_importer.py` - RSS feed importer
- `script/claude_blog_rss.py` - Another scraping example
