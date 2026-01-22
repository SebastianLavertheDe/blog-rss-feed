import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import json
import re

class AnthropicEngineeringRSSGenerator:
    def __init__(self):
        self.base_url = "https://www.anthropic.com/engineering"

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
        # Fetch the engineering page
        response = requests.get(self.base_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        articles_data = []
        seen_urls = set()

        # Look for script tags that might contain JSON data (Next.js data)
        script_tags = soup.find_all('script', type='application/json')
        for script in script_tags:
            try:
                data = json.loads(script.string)
                # Navigate the JSON structure to find posts
                if isinstance(data, dict):
                    # Check for common Next.js data structures
                    for key, value in data.items():
                        if isinstance(value, dict):
                            for k2, v2 in value.items():
                                if isinstance(v2, list):
                                    for item in v2:
                                        if isinstance(item, dict):
                                            self._extract_from_json(item, articles_data, seen_urls)
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    self._extract_from_json(item, articles_data, seen_urls)
            except:
                pass

        # Also try HTML parsing as fallback
        # Look for links to engineering blog posts
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/engineering/' in href and href != '/engineering':
                # Build full URL if relative
                if not href.startswith('http'):
                    href = f"https://www.anthropic.com{href}"

                # Skip duplicates
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Extract title from link text or nearby elements
                title = link.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                # Try to find date near the link
                date_text = None
                parent = link.parent
                if parent:
                    # Look for date patterns in parent and siblings
                    for elem in parent.find_all(string=True):
                        if re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+\d{4}', elem):
                            date_text = elem.strip()
                            break

                parsed_date = datetime.now(timezone.utc)
                if date_text:
                    parsed_date = self.parse_date(date_text)
                else:
                    # Try to extract date from URL or title
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

    def _extract_from_json(self, item, articles_data, seen_urls):
        """Extract article data from JSON structure"""
        if not isinstance(item, dict):
            return

        # Look for common article fields
        title = item.get('title') or item.get('heading') or item.get('headline')
        url = item.get('url') or item.get('slug') or item.get('link')
        date = item.get('date') or item.get('publishedAt') or item.get('pubDate')

        if title and url:
            # Build full URL if needed
            if not url.startswith('http'):
                if url.startswith('/'):
                    url = f"https://www.anthropic.com{url}"
                else:
                    url = f"https://www.anthropic.com/engineering/{url}"

            if url in seen_urls or '/engineering/' not in url:
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
        feed.title('Anthropic Engineering Blog')
        feed.link(href=self.base_url, rel='alternate')
        feed.description('Latest posts from Anthropic Engineering blog')
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
    generator = AnthropicEngineeringRSSGenerator()
    articles_data = await generator.fetch_posts()
    rss_content = generator.generate_rss(articles_data)

    # Write to file in root directory
    with open('anthropic_engineering_rss.xml', 'wb') as f:
        f.write(rss_content)

    print(f"RSS feed generated successfully with {len(articles_data)} articles!")

if __name__ == "__main__":
    asyncio.run(main())
