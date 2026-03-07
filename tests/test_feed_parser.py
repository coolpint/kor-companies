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


if __name__ == "__main__":
    unittest.main()

