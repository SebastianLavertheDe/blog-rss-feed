import asyncio
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from script.anthropic_engineering_rss import AnthropicEngineeringRSSGenerator, main


class AnthropicEngineeringRSSTests(unittest.TestCase):
    def fetch_from_html(self, html):
        generator = AnthropicEngineeringRSSGenerator()
        response = Mock(text=html)
        generator.session.get = Mock(return_value=response)
        return generator, asyncio.run(generator.fetch_posts())

    def test_research_links_and_repeated_card_links(self):
        generator, articles = self.fetch_from_html("""
            <article>
                <time>Oct 13, 2026</time>
                <a href="/research/redesigning-source-control"><img src="image.jpg"></a>
                <h3><a href="https://www.anthropic.com/research/redesigning-source-control">
                    Redesigning source control at Anthropic
                </a></h3>
                <p>How we migrated source control.</p>
            </article>
            <article>
                <time>Oct 13, 2026</time>
                <h3><a href="/research/redesigning-source-control?ref=featured#intro">
                    Redesigning source control at Anthropic
                </a></h3>
            </article>
        """)

        self.assertEqual(len(articles), 1)
        root = ET.fromstring(generator.generate_rss(articles))
        items = root.findall("channel/item")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].findtext("title"), "Redesigning source control at Anthropic")
        self.assertEqual(items[0].findtext("link"),
                         "https://www.anthropic.com/research/redesigning-source-control")
        self.assertEqual(items[0].findtext("description"), "How we migrated source control.")
        self.assertEqual(items[0].findtext("pubDate"), "Tue, 13 Oct 2026 00:00:00 +0000")

    def test_legacy_links_and_chronological_order(self):
        _, articles = self.fetch_from_html("""
            <article>
                <time datetime="2025-06-13">Jun 13, 2025</time>
                <h3><a href="/engineering/multi-agent-research-system">Multi-agent research</a></h3>
            </article>
            <article>
                <time>Oct 13, 2026</time>
                <h3><a href="/research/redesigning-source-control">Source control</a></h3>
            </article>
        """)

        self.assertEqual([article["title"] for article in articles],
                         ["Source control", "Multi-agent research"])
        self.assertEqual(articles[1]["url"],
                         "https://www.anthropic.com/engineering/multi-agent-research-system")

    def test_unrelated_links_do_not_become_articles(self):
        _, articles = self.fetch_from_html("""
            <article>
                <time>Oct 13, 2026</time>
                <h3><a href="/research/team/engineering">Engineering team</a></h3>
            </article>
            <article>
                <time>Oct 13, 2026</time>
                <h3><a href="https://other.example/research/post">External post</a></h3>
            </article>
            <article>
                <time>Oct 13, 2026</time>
                <h3><a href="/research">Research index</a></h3>
            </article>
        """)

        self.assertEqual(articles, [])

    def test_empty_scrape_preserves_existing_feed_and_fails(self):
        generator, articles = self.fetch_from_html("<html><body>No articles</body></html>")
        generator.fetch_posts = AsyncMock(return_value=articles)
        original_dir = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                output = Path("rss/anthropic_engineering_rss.xml")
                output.parent.mkdir()
                previous_feed = b"<rss><channel><item><title>Previous article</title></item></channel></rss>"
                output.write_bytes(previous_feed)
                with patch("script.anthropic_engineering_rss.AnthropicEngineeringRSSGenerator",
                           return_value=generator):
                    with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                        asyncio.run(main())
                self.assertEqual(output.read_bytes(), previous_feed)
            finally:
                os.chdir(original_dir)


if __name__ == "__main__":
    unittest.main()
