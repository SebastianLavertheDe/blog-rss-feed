import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

from script.external_rss_importer import ExternalRSSImporter


class ExternalRSSImporterTests(unittest.TestCase):
    def test_langchain_empty_item_does_not_hide_valid_articles(self):
        source = b"""<?xml version="1.0" encoding="UTF-8"?>
            <rss version="2.0"><channel>
                <title>LangChain Blog</title>
                <link>https://www.langchain.com/blog</link>
                <description>LangChain articles</description>
                <item>
                    <title>Older article</title>
                    <link>https://www.langchain.com/blog/older</link>
                    <description>An older article</description>
                    <pubDate>Fri, 23 Oct 2026 12:00:00 GMT</pubDate>
                </item>
                <item>
                    <title/>
                    <link>https://www.langchain.com/blog/agents-that-pay-how-nevermined-empowers-langchain-agents-to-buy-and-sell-services</link>
                    <description/>
                    <pubDate>Thu, 03 Sep 2026 06:21:13 GMT</pubDate>
                </item>
                <item>
                    <title>Newest article &amp; guide</title>
                    <link>https://www.langchain.com/blog/newest</link>
                    <description>New article summary</description>
                    <pubDate>Sat, 24 Oct 2026 01:05:29 GMT</pubDate>
                </item>
                <item>
                    <title>Article with a blank link</title>
                    <link> </link>
                    <pubDate>Sat, 24 Oct 2026 01:00:00 GMT</pubDate>
                </item>
            </channel></rss>
        """
        importer = ExternalRSSImporter(
            "https://www.langchain.com/blog/rss.xml", "langchain_blog_rss.xml"
        )
        original_dir = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                os.chdir(temp_dir)
                with patch.object(importer, "fetch_with_retry", return_value=source):
                    self.assertTrue(importer.fetch_and_reformat())
                root = ET.parse("rss/langchain_blog_rss.xml").getroot()
            finally:
                os.chdir(original_dir)

        items = root.findall("channel/item")
        self.assertEqual([item.findtext("title") for item in items],
                         ["Newest article & guide", "Older article"])
        self.assertEqual(items[0].findtext("description"), "New article summary")
        self.assertEqual(items[0].findtext("pubDate"), "Sat, 24 Oct 2026 01:05:29 +0000")
        self.assertEqual([item.findtext("link") for item in items],
                         ["https://www.langchain.com/blog/newest",
                          "https://www.langchain.com/blog/older"])
        self.assertTrue(all(item.findtext("guid") == item.findtext("link") for item in items))


if __name__ == "__main__":
    unittest.main()
