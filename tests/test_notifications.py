import unittest

from src.kor_companies.models import MatchedArticle, SourceRunResult
from src.kor_companies.notifications import build_run_summary_messages


class NotificationTests(unittest.TestCase):
    def test_build_summary_without_articles(self):
        messages = build_run_summary_messages(
            run_at_label="2026-03-07 18:00:00 KST",
            matched_articles=[],
            new_articles=[],
            source_runs=[
                SourceRunResult(
                    source_id="a",
                    source_name="Source A",
                    country_code="US",
                    success=True,
                    item_count=10,
                    matched_count=0,
                )
            ],
        )
        self.assertEqual(messages, [])

    def test_build_summary_without_articles_but_with_failures(self):
        messages = build_run_summary_messages(
            run_at_label="2026-03-07 18:00:00 KST",
            matched_articles=[],
            new_articles=[],
            source_runs=[
                SourceRunResult(
                    source_id="a",
                    source_name="Source A",
                    country_code="US",
                    success=False,
                    error="timeout",
                )
            ],
        )
        self.assertEqual(messages, [])

    def test_build_summary_with_article(self):
        article = MatchedArticle(
            article_key="key",
            canonical_link="https://example.com",
            link="https://example.com",
            title="Samsung Electronics expands AI chip output",
            summary="Samsung Electronics plans to expand output.",
            published_at=None,
            source_id="src",
            source_name="Example Source",
            country_code="US",
            country_name_ko="미국",
            matched_companies=["Samsung Electronics"],
            matched_aliases=["Samsung Electronics"],
        )
        messages = build_run_summary_messages(
            run_at_label="2026-03-07 18:00:00 KST",
            matched_articles=[article],
            new_articles=[article],
            source_runs=[
                SourceRunResult(
                    source_id="src",
                    source_name="Example Source",
                    country_code="US",
                    success=True,
                    item_count=10,
                    matched_count=1,
                )
            ],
        )
        self.assertEqual(len(messages), 2)
        self.assertIn("신규 기사: 1건", messages[0])
        self.assertIn("Samsung Electronics expands AI chip output", messages[1])


if __name__ == "__main__":
    unittest.main()
