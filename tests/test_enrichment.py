import json
import unittest
from unittest.mock import patch

from src.kor_companies.article_context import ArticleContext
from src.kor_companies.enrichment import ArticleEnricher, GoogleTranslateConfig


class _FakeResponse:
    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class EnrichmentTests(unittest.TestCase):
    def test_short_alias_without_context_is_filtered(self):
        enricher = ArticleEnricher(config=None)
        result = enricher.enrich(
            source_language="ja",
            title="トランプ大統領は成果を強調",
            summary="湾岸諸国ではイランの攻撃相次ぐ",
            matched_companies=["Kia"],
            matched_aliases=["Kia"],
            context=ArticleContext(relevant_sentences=[]),
        )
        self.assertFalse(result.is_related)

    def test_context_sentence_is_used_for_company_summary(self):
        enricher = ArticleEnricher(config=None)
        result = enricher.enrich(
            source_language="ja",
            title="起亜が新型EVを日本で公開",
            summary="展示会で新型EVを紹介した。",
            matched_companies=["Kia"],
            matched_aliases=["起亜"],
            context=ArticleContext(
                relevant_sentences=["起亜は日本で新型EVを公開した。"],
                summary_sentences=[
                    "起亜は日本で新型EVを公開した。",
                    "同社は価格戦略もあわせて説明した。",
                    "展示会では充電 성능 개선도 강조했다.",
                    "販売時期は今年後半を見込んでいる。",
                    "現地 딜러 네트워크 확대 계획도 밝혔다.",
                ],
            ),
        )
        self.assertTrue(result.is_related)
        self.assertIn("Kia", result.company_summary)
        self.assertIn("起亜", result.company_summary)
        self.assertIn("現地 딜러 네트워크 확대 계획도 밝혔다.", result.company_summary)

    @patch("src.kor_companies.enrichment.urlopen")
    def test_google_translate_translates_title_and_company_summary(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(
            {
                "data": {
                    "translations": [
                        {"translatedText": "기아가 일본에서 신형 EV를 공개"},
                        {
                            "translatedText": (
                                "기아는 일본에서 신형 EV를 공개했다. "
                                "회사는 가격 전략도 함께 설명했다. "
                                "전시회에서는 충전 성능 개선을 강조했다. "
                                "판매 시점은 올해 하반기로 예상된다고 밝혔다. "
                                "현지 딜러 네트워크 확대 계획도 공개했다."
                            )
                        },
                    ]
                }
            }
        )
        enricher = ArticleEnricher(config=GoogleTranslateConfig(api_key="test-key"))
        result = enricher.enrich(
            source_language="ja",
            title="起亜が新型EVを日本で公開",
            summary="展示会で新型EVを紹介した。",
            matched_companies=["Kia"],
            matched_aliases=["起亜"],
            context=ArticleContext(
                relevant_sentences=["起亜は日本で新型EVを公開した。"],
                summary_sentences=[
                    "起亜は日本で新型EVを公開した。",
                    "同社は価格戦略もあわせて説明した。",
                    "展示会では充電性能の改善も強調した。",
                    "販売時期は今年後半を見込んでいる。",
                    "現地ディーラーネットワーク拡大計画も明らかにした。",
                ],
            ),
        )

        self.assertEqual(result.translated_title, "기아가 일본에서 신형 EV를 공개")
        self.assertEqual(
            result.company_summary,
            (
                "Kia 관련 내용: 기아는 일본에서 신형 EV를 공개했다. 회사는 가격 전략도 함께 설명했다. "
                "전시회에서는 충전 성능 개선을 강조했다. 판매 시점은 올해 하반기로 예상된다고 밝혔다. "
                "현지 딜러 네트워크 확대 계획도 공개했다."
            ),
        )
        self.assertEqual(result.translated_summary, result.company_summary)


if __name__ == "__main__":
    unittest.main()
