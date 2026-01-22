import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import json
import re
import os

class ClaudeBlogRSSGenerator:
    def __init__(self):
        self.base_url = "https://claude.com/blog"

    def parse_date(self, date_text):
        """Parse date text and return a datetime object with timezone"""
        try:
            date_text = date_text.strip()
            parsed_date = date_parser.parse(date_text)
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except Exception as e:
            print(f"Error parsing date '{date_text}': {e}")
            return datetime.now(timezone.utc)

    async def fetch_posts(self):
        # Fetch the blog page
        response = requests.get(self.base_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        articles_data = []
        seen_urls = set()

        # Look for script tags that might contain JSON data
        script_tags = soup.find_all('script')
        for script in script_tags:
            try:
                script_content = script.string or ''
                # Look for JSON-like data in script tags
                if '__DATA__' in script_content or 'window.__DATA' in script_content:
                    # Try to extract JSON
                    json_match = re.search(r'window\.__DATA__\s*=\s*({.*?});', script_content, re.DOTALL)
                    if json_match:
                        try:
                            data = json.loads(json_match.group(1))
                            self._extract_from_json(data, articles_data, seen_urls)
                        except:
                            pass
            except:
                pass

        # Also try HTML parsing - look for blog post links
        # Claude blog uses Webflow, so we look for specific patterns
        for link in soup.find_all('a', href=True):
            href = link.get('href')

            # Look for blog post links
            if href and ('/blog/' in href or href.startswith('/blog')):
                # Skip the main blog page
                if href == '/blog' or href.endswith('/blog'):
                    continue

                # Build full URL if relative
                if not href.startswith('http'):
                    href = f"https://claude.com{href}"

                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Get title from link text or nearby elements
                title = link.get_text(strip=True)

                # Also check for heading elements near the link
                if not title or len(title) < 10:
                    parent = link.parent
                    if parent:
                        heading = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                        if heading:
                            title = heading.get_text(strip=True)

                if not title or len(title) < 10:
                    continue

                # Try to find date near the link
                date_text = None
                parent = link.parent
                if parent:
                    # Look for date patterns in parent and siblings
                    for elem in parent.find_all(string=True):
                        if re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)[a-z]*\s+\d{1,2},\s+\d{4}', elem):
                            date_text = elem.strip()
                            break
                        # Also match abbreviated months
                        elif re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}', elem):
                            date_text = elem.strip()
                            break

                parsed_date = datetime.now(timezone.utc)
                if date_text:
                    parsed_date = self.parse_date(date_text)
                else:
                    date_text = parsed_date.strftime('%b %d, %Y')

                articles_data.append({
                    'title': title,
                    'url': href,
                    'date': parsed_date,
                    'date_text': date_text
                })

                print(f"Found: {title} ({date_text})")

        # Sort articles by date (newest first)
        articles_data.sort(key=lambda x: x['date'], reverse=True)

        # Remove duplicates based on URL
        unique_articles = []
        seen = set()
        for article in articles_data:
            if article['url'] not in seen:
                seen.add(article['url'])
                unique_articles.append(article)

        return unique_articles

    def _extract_from_json(self, data, articles_data, seen_urls):
        """Extract article data from JSON structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.lower() in ['posts', 'articles', 'items', 'entries', 'blog']:
                    if isinstance(value, list):
                        for item in value:
                            self._extract_article_from_item(item, articles_data, seen_urls)
                elif isinstance(value, (dict, list)):
                    self._extract_from_json(value, articles_data, seen_urls)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    self._extract_article_from_item(item, articles_data, seen_urls)

    def _extract_article_from_item(self, item, articles_data, seen_urls):
        """Extract article from a single item"""
        if not isinstance(item, dict):
            return

        title = item.get('title') or item.get('heading') or item.get('name')
        url = item.get('url') or item.get('slug') or item.get('link') or item.get('href')
        date = item.get('date') or item.get('publishedAt') or item.get('pubDate') or item.get('published-date')

        if title and url:
            # Build full URL if needed
            if not url.startswith('http'):
                if url.startswith('/'):
                    url = f"https://claude.com{url}"
                else:
                    url = f"https://claude.com/blog/{url}"

            if url in seen_urls or '/blog/' not in url:
                return

            seen_urls.add(url)

            parsed_date = datetime.now(timezone.utc)
            date_text = None
            if date:
                try:
                    parsed_date = self.parse_date(date)
                    date_text = date
                except:
                    pass

            articles_data.append({
                'title': title,
                'url': url,
                'date': parsed_date,
                'date_text': date_text or parsed_date.strftime('%b %d, %Y')
            })

            print(f"Found: {title} ({date_text or 'N/A'})")

    def create_feed(self):
        """Create a fresh feed instance"""
        feed = FeedGenerator()
        feed.title('Claude Blog')
        feed.link(href=self.base_url, rel='alternate')
        feed.description('Latest posts from Claude blog')
        feed.language('en')
        return feed

    def generate_rss(self, articles_data):
        feed = self.create_feed()

        for article_data in articles_data:
            entry = feed.add_entry(order='append')
            entry.title(article_data['title'])
            entry.link(href=article_data['url'])
            entry.pubDate(article_data['date'])
            entry.description(article_data['title'])
            entry.guid(article_data['url'], permalink=True)

        rss_content = feed.rss_str(pretty=True)
        return rss_content

async def main():
    generator = ClaudeBlogRSSGenerator()
    articles_data = await generator.fetch_posts()
    rss_content = generator.generate_rss(articles_data)

    # Create rss directory if it doesn't exist
    os.makedirs('rss', exist_ok=True)

    # Write to file in rss directory
    with open('rss/claude_blog_rss.xml', 'wb') as f:
        f.write(rss_content)

    print(f"RSS feed generated successfully with {len(articles_data)} articles!")

if __name__ == "__main__":
    asyncio.run(main())
