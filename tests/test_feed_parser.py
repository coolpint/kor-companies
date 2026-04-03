from pathlib import Path
import unittest

from src.kor_companies.feed_parser import parse_feed
from src.kor_companies.models import SourceConfig


FIXTURES = Path(__file__).parent / "fixtures"


class FeedParserTests(unittest.TestCase):
    def test_parse_rss_feed(self):
        source = SourceConfig(
            source_id="rss",
            source_name="Sample RSS",
            country_code="US",
            feed_url="file://sample",
            homepage_url="https://example.com",
            language="en",
            category="business",
        )
        entries = parse_feed(source, (FIXTURES / "sample_rss.xml").read_bytes())
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].title, "Samsung Electronics expands AI chip production")
        self.assertEqual(entries[0].link, "https://example.com/articles/samsung-ai?utm_source=test")

    def test_parse_atom_feed(self):
        source = SourceConfig(
            source_id="atom",
            source_name="Sample Atom",
            country_code="JP",
            feed_url="file://sample",
            homepage_url="https://example.org",
            language="en",
            category="business",
        )
        entries = parse_feed(source, (FIXTURES / "sample_atom.xml").read_bytes())
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "Hyundai Motor signs EV battery deal")
        self.assertEqual(entries[0].link, "https://example.org/news/hyundai-deal")

    def test_parse_google_news_feed(self):
        source = SourceConfig(
            source_id="google_news_us_01",
            source_name="Google News US #1",
            country_code="US",
            feed_url="https://news.google.com/rss/search?q=Samsung&hl=en-US&gl=US&ceid=US:en",
            homepage_url="https://news.google.com/",
            language="en",
            category="google_news",
        )
        entries = parse_feed(source, (FIXTURES / "google_news_rss.xml").read_bytes())
        self.assertEqual(len(entries), 2)
        self.assertEqual(
            entries[0].title,
            "Helium stocks of South Korea's chipmakers to last until June, sources say",
        )
        self.assertEqual(entries[0].origin_source_name, "Reuters")
        self.assertEqual(entries[0].origin_source_url, "https://www.reuters.com")
        self.assertEqual(entries[0].summary, "")


if __name__ == "__main__":
    unittest.main()
