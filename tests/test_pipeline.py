import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from src.kor_companies.pipeline import run_monitor


FIXTURES = Path(__file__).parent / "fixtures"


class PipelineTests(unittest.TestCase):
    def test_pipeline_generates_reports_and_state(self):
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_dir = root / "config"
            output_dir = root / "reports"
            state_path = root / "data" / "state.json"
            config_dir.mkdir(parents=True)

            companies = [
                {
                    "canonical_name_ko": "삼성전자",
                    "canonical_name_en": "Samsung Electronics",
                    "group_name": "삼성",
                    "aliases_en": ["Samsung Electronics"],
                    "aliases_ko": ["삼성전자"],
                    "aliases_local": [],
                    "primary_brands": ["Galaxy"],
                    "active": True,
                },
                {
                    "canonical_name_ko": "현대자동차",
                    "canonical_name_en": "Hyundai Motor",
                    "group_name": "현대자동차그룹",
                    "aliases_en": ["Hyundai Motor", "Hyundai"],
                    "aliases_ko": ["현대자동차"],
                    "aliases_local": [],
                    "primary_brands": [],
                    "active": True,
                },
            ]
            countries = [
                {
                    "country_code": "US",
                    "country_name_ko": "미국",
                    "country_name_en": "United States",
                    "priority": "P1",
                    "languages": ["en"],
                    "active": True,
                },
                {
                    "country_code": "JP",
                    "country_name_ko": "일본",
                    "country_name_en": "Japan",
                    "priority": "P1",
                    "languages": ["en"],
                    "active": True,
                },
            ]
            sources = [
                {
                    "source_id": "rss",
                    "source_name": "Sample RSS",
                    "country_code": "US",
                    "feed_url": (FIXTURES / "sample_rss.xml").as_uri(),
                    "homepage_url": "https://example.com",
                    "language": "en",
                    "category": "business",
                    "enabled": True,
                    "trust_tier": 1,
                },
                {
                    "source_id": "atom",
                    "source_name": "Sample Atom",
                    "country_code": "JP",
                    "feed_url": (FIXTURES / "sample_atom.xml").as_uri(),
                    "homepage_url": "https://example.org",
                    "language": "en",
                    "category": "business",
                    "enabled": True,
                    "trust_tier": 1,
                },
            ]

            (config_dir / "companies.json").write_text(
                json.dumps(companies, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (config_dir / "countries.json").write_text(
                json.dumps(countries, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (config_dir / "sources.json").write_text(
                json.dumps(sources, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            first = run_monitor(
                config_dir=config_dir,
                output_dir=output_dir,
                state_path=state_path,
                since_hours=100000,
                max_items_per_feed=10,
            )
            self.assertEqual(len(first.matched_articles), 2)
            self.assertEqual(len(first.new_articles), 2)
            self.assertTrue((output_dir / "latest.md").exists())
            self.assertTrue(state_path.exists())

            second = run_monitor(
                config_dir=config_dir,
                output_dir=output_dir,
                state_path=state_path,
                since_hours=100000,
                max_items_per_feed=10,
            )
            self.assertEqual(len(second.matched_articles), 2)
            self.assertEqual(len(second.new_articles), 0)


if __name__ == "__main__":
    unittest.main()

