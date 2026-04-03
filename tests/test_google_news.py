import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.kor_companies.config import load_google_news_config
from src.kor_companies.google_news import GoogleNewsEntryFilter, build_google_news_sources
from src.kor_companies.models import CompanyConfig, FeedEntry, SourceConfig


class GoogleNewsTests(unittest.TestCase):
    def test_load_config_and_build_sources(self):
        config_payload = {
            "enabled": True,
            "batch_size": 3,
            "max_items_per_feed": 15,
            "countries": [
                {
                    "country_code": "US",
                    "hl": "en-US",
                    "gl": "US",
                    "ceid": "US:en",
                    "language": "en",
                    "enabled": True,
                },
                {
                    "country_code": "JP",
                    "hl": "ja",
                    "gl": "JP",
                    "ceid": "JP:ja",
                    "language": "ja",
                    "enabled": True,
                },
            ],
        }
        companies = [
            CompanyConfig(
                canonical_name_ko="삼성전자",
                canonical_name_en="Samsung Electronics",
                group_name="삼성",
                aliases_en=["Samsung Electronics"],
                aliases_ko=["삼성전자"],
                aliases_local=[],
                primary_brands=[],
            ),
            CompanyConfig(
                canonical_name_ko="SK하이닉스",
                canonical_name_en="SK hynix",
                group_name="SK",
                aliases_en=["SK hynix"],
                aliases_ko=["SK하이닉스"],
                aliases_local=[],
                primary_brands=[],
            ),
            CompanyConfig(
                canonical_name_ko="현대자동차",
                canonical_name_en="Hyundai Motor",
                group_name="현대차",
                aliases_en=["Hyundai Motor"],
                aliases_ko=["현대자동차"],
                aliases_local=[],
                primary_brands=[],
            ),
            CompanyConfig(
                canonical_name_ko="기아",
                canonical_name_en="Kia",
                group_name="현대차",
                aliases_en=["Kia"],
                aliases_ko=["기아"],
                aliases_local=[],
                primary_brands=[],
            ),
        ]

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "google_news.json"
            path.write_text(json.dumps(config_payload), encoding="utf-8")
            config = load_google_news_config(path)

        self.assertIsNotNone(config)
        sources = build_google_news_sources(config, companies)
        self.assertEqual(len(sources), 4)
        self.assertEqual(sources[0].category, "google_news")
        self.assertEqual(sources[0].max_items, 15)
        self.assertIn("news.google.com/rss/search", sources[0].feed_url)
        self.assertIn("%22Samsung+Electronics%22+OR+%22SK+hynix%22+OR+%22Hyundai+Motor%22", sources[0].feed_url)

    def test_filter_blocks_korean_pr_company_and_known_hosts(self):
        companies = [
            CompanyConfig(
                canonical_name_ko="크래프톤",
                canonical_name_en="Krafton",
                group_name="크래프톤",
                aliases_en=["Krafton"],
                aliases_ko=["크래프톤"],
                aliases_local=[],
                primary_brands=[],
            )
        ]
        static_sources = [
            SourceConfig(
                source_id="nikkei_asia",
                source_name="Nikkei Asia",
                country_code="JP",
                feed_url="https://asia.nikkei.com/rss/feed/nar",
                homepage_url="https://asia.nikkei.com/",
                language="en",
                category="general",
            )
        ]
        config_payload = {
            "enabled": True,
            "batch_size": 6,
            "max_items_per_feed": 20,
            "countries": [
                {
                    "country_code": "JP",
                    "hl": "ja",
                    "gl": "JP",
                    "ceid": "JP:ja",
                    "language": "ja",
                    "enabled": True,
                }
            ],
            "excluded_domains": ["prtimes.jp", "mk.co.kr"],
            "excluded_source_names": ["PR TIMES", "매일경제"],
            "excluded_title_patterns": ["^画像ギャラリー"],
        }

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "google_news.json"
            path.write_text(json.dumps(config_payload), encoding="utf-8")
            config = load_google_news_config(path)

        entry_filter = GoogleNewsEntryFilter(
            config=config,
            companies=companies,
            existing_sources=static_sources,
        )

        allowed = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="Krafton loses appeal in acquisition dispute",
            link="https://news.google.com/rss/articles/test1",
            summary="",
            published_at=None,
            origin_source_name="Reuters",
            origin_source_url="https://www.reuters.com",
        )
        blocked_pr = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="KRAFTON announces update",
            link="https://news.google.com/rss/articles/test2",
            summary="",
            published_at=None,
            origin_source_name="PR TIMES",
            origin_source_url="https://prtimes.jp/main/html/rd/p/test.html",
        )
        blocked_company = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="KRAFTON announces update",
            link="https://news.google.com/rss/articles/test3",
            summary="",
            published_at=None,
            origin_source_name="크래프톤",
            origin_source_url="https://www.krafton.com/news/test",
        )
        blocked_existing = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="Samsung SDI's Hungary woes cloud Orban's reelection bid",
            link="https://news.google.com/rss/articles/test4",
            summary="",
            published_at=None,
            origin_source_name="Nikkei Asia",
            origin_source_url="https://asia.nikkei.com/business/test",
        )
        blocked_title = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="画像ギャラリー No.001 | NEXON Korea signs publishing pact",
            link="https://news.google.com/rss/articles/test5",
            summary="",
            published_at=None,
            origin_source_name="4Gamer.net",
            origin_source_url="https://www.4gamer.net/games/test",
        )
        blocked_reuters_rehost = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="Hyundai Motor flags export disruptions as Middle East conflict hits shipping By Reuters",
            link="https://news.google.com/rss/articles/test6",
            summary="",
            published_at=None,
            origin_source_name="Investing.com",
            origin_source_url="https://www.investing.com/news/test",
        )
        blocked_korean_named_source = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="Samsung Electronics stock jumps on AI optimism",
            link="https://news.google.com/rss/articles/test7",
            summary="",
            published_at=None,
            origin_source_name="Korea IT Times",
            origin_source_url="https://www.koreaittimes.com/news/test",
        )
        blocked_hangul_title = FeedEntry(
            source_id="google_news_jp_01",
            source_name="Google News JP #1",
            country_code="JP",
            title="삼성전자와 SK하이닉스 주가 급등",
            link="https://news.google.com/rss/articles/test8",
            summary="",
            published_at=None,
            origin_source_name="Example Wire",
            origin_source_url="https://example.com/news/test",
        )

        self.assertTrue(entry_filter.allow(allowed))
        self.assertFalse(entry_filter.allow(blocked_pr))
        self.assertFalse(entry_filter.allow(blocked_company))
        self.assertFalse(entry_filter.allow(blocked_existing))
        self.assertFalse(entry_filter.allow(blocked_title))
        self.assertFalse(entry_filter.allow(blocked_reuters_rehost))
        self.assertFalse(entry_filter.allow(blocked_korean_named_source))
        self.assertFalse(entry_filter.allow(blocked_hangul_title))


if __name__ == "__main__":
    unittest.main()
