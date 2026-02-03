import asyncio
from datetime import datetime, timezone
from feedgen.feed import FeedGenerator
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
import os

class CursorRSSGenerator:
    def __init__(self):
        self.base_url = "https://cursor.com/blog"

    def parse_date(self, date_text):
        """Parse date text and return a datetime object with timezone"""
        try:
            # Clean up the date text
            date_text = date_text.strip()

            # Try to parse the date
            parsed_date = date_parser.parse(date_text, tzinfos={"UT": timezone.utc, "UTC": timezone.utc})

            # If no timezone info, assume UTC
            if parsed_date.tzinfo is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)

            return parsed_date
        except Exception as e:
            print(f"Error parsing date '{date_text}': {e}")
            # Return current date as fallback with UTC timezone
            return datetime.now(timezone.utc)

    async def fetch_posts(self):
        # Fetch the blog page
        response = requests.get(self.base_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Store articles data for sorting
        articles_data = []
        seen_urls = set()

        # Try different selectors that might match blog posts
        selectors = [
            'a[href*="/blog/"]',      # Links to blog posts
            'article a',               # Links inside articles
            '[class*="post"] a',       # Links in post containers
            '[class*="entry"] a',      # Links in entry containers
        ]

        for selector in selectors:
            for link in soup.select(selector):
                try:
                    url = link.get('href')
                    title = link.get_text(strip=True)

                    if not url or not title:
                        continue

                    # Skip if already seen
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    # Build full URL if relative
                    if not url.startswith('http'):
                        if url.startswith('/'):
                            url = f"https://cursor.com{url}"
                        else:
                            url = f"https://cursor.com/blog/{url}"

                    # Skip non-blog links or index/category/topic pages
                    if '/blog/' not in url:
                        continue
                    # Skip topic/category/tag pages and navigation
                    if any(x in url for x in ['/topic/', '/tag/', '/category/']):
                        continue
                    # Skip navigation links that don't point to actual posts
                    if any(x in url for x in ['next', 'older', 'previous']):
                        continue
                    # Must have a slug after /blog/ (not just /blog/ or /blog)
                    path_parts = url.split('/blog/')
                    if len(path_parts) < 2 or not path_parts[1].strip():
                        continue

                    # Clean up title - remove category and date suffixes
                    # Pattern: "Titlecategory·Jan 15, 2026" -> "Title"
                    import re
                    # Remove category/date suffix (e.g., "research·Jan 15, 2026")
                    title = re.sub(r'[a-z]+·[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}$', '', title)
                    # Remove standalone category names and navigation text
                    if title.lower() in ['product', 'research', 'company', 'older posts', 'next', 'older', 'next →older posts']:
                        continue
                    # Skip if title contains navigation arrows
                    if '→' in title or '←' in title:
                        continue
                    # Add space between sentences:
                    # 1. After period + capital letter: "Sentence one.Sentence two" -> "Sentence one. Sentence two"
                    title = re.sub(r'\.([A-Z])', r'. \1', title)
                    # 2. CamelCase: "sentenceOneSentenceTwo" -> "sentenceOne SentenceTwo"
                    title = re.sub(r'([a-z])([A-Z])', r'\1 \2', title)

                    # Clean up title
                    title = title.strip()
                    if not title or len(title) < 10:
                        continue

                    # Try to find date near the link (look in parent and sibling elements)
                    date_text = None
                    # Check parent and its siblings for date elements
                    current = link.parent
                    for _ in range(3):  # Check up to 3 levels up
                        if current:
                            # Look for time tag or date spans
                            date_elem = current.find(['time', 'span', 'div'], class_=lambda x: x and any(d in x.lower() for d in ['date', 'time', 'published']))
                            if date_elem:
                                date_text = date_elem.get_text(strip=True)
                                break
                            # Also check all spans/divs in parent
                            for elem in current.find_all(['span', 'div', 'time']):
                                text = elem.get_text(strip=True)
                                # Check for date pattern like "Jan 15, 2026"
                                if re.search(r'^[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}$', text):
                                    date_text = text
                                    break
                            if date_text:
                                break
                            current = current.parent

                    parsed_date = datetime.now(timezone.utc)
                    if date_text:
                        parsed_date = self.parse_date(date_text)
                    else:
                        date_text = parsed_date.strftime('%Y-%m-%d')

                    articles_data.append({
                        'title': title,
                        'url': url,
                        'date': parsed_date,
                        'date_text': date_text
                    })

                    print(f"Found: {title} ({date_text})")

                except Exception as e:
                    print(f"Error processing element: {e}")
                    continue

        # Sort articles by date (newest first)
        articles_data.sort(key=lambda x: x['date'], reverse=True)

        return articles_data

    def create_feed(self):
        """Create a fresh feed instance"""
        feed = FeedGenerator()
        feed.title('Cursor Blog')
        feed.link(href=self.base_url, rel='alternate')
        feed.description('Latest posts from Cursor blog')
        feed.language('en')

        return feed

    def generate_rss(self, articles_data):
        # Create a fresh feed and add entries in sorted order
        feed = self.create_feed()

        # Use order='append' to maintain the sorted order (newest first)
        for article_data in articles_data:
            entry = feed.add_entry(order='append')
            entry.title(article_data['title'])
            entry.link(href=article_data['url'])
            entry.pubDate(article_data['date'])
            entry.description(article_data['title'])
            entry.guid(article_data['url'], permalink=True)

        # Generate RSS feed content
        rss_content = feed.rss_str(pretty=True)
        return rss_content

async def main():
    generator = CursorRSSGenerator()
    articles_data = await generator.fetch_posts()
    rss_content = generator.generate_rss(articles_data)

    # Create rss directory if it doesn't exist
    os.makedirs('rss', exist_ok=True)

    # Write to file in rss directory
    with open('rss/cursor_blog_rss.xml', 'wb') as f:
        f.write(rss_content)

    print(f"RSS feed generated successfully with {len(articles_data)} articles!")

if __name__ == "__main__":
    asyncio.run(main())
