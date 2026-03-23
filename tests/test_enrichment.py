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
        self.assertIn("Kia 관련 기사다.", result.company_summary)
        self.assertIn("기사 제목은 '起亜が新型EVを日本で公開'이다.", result.company_summary)
        self.assertIn("起亜", result.company_summary)
        self.assertIn("現地 딜러 네트워크 확대 계획도 밝혔다.", result.company_summary)
        self.assertGreaterEqual(
            result.company_summary.count(".") + result.company_summary.count("。"),
            5,
        )

    def test_boilerplate_sentences_are_skipped_from_company_summary(self):
        enricher = ArticleEnricher(config=None)
        result = enricher.enrich(
            source_language="ko",
            title="미국 법원, AI 활용 인수 분쟁에서 크래프톤에 불리한 판결",
            summary="크래프톤은 미국 자회사 경영진 해임이 부당했다는 판결을 받았다.",
            matched_companies=["Krafton"],
            matched_aliases=["Krafton"],
            context=ArticleContext(
                relevant_sentences=["크래프톤은 미국 자회사 경영진 해임이 부당했다는 판결을 받았다."],
                summary_sentences=[
                    "디지털 구독 인쇄판 최신 뉴스 북마크 링크 복사.",
                    "크래프톤은 미국 자회사 경영진 해임이 부당했다는 판결을 받았다.",
                    "델라웨어 법원은 경영진 복직을 명령했다.",
                    "회사는 2억5천만달러 규모 분쟁 대응 방식을 다시 검토하게 됐다.",
                ],
            ),
        )

        self.assertIn("크래프톤은 미국 자회사 경영진 해임이 부당했다는 판결을 받았다.", result.company_summary)
        self.assertIn("델라웨어 법원은 경영진 복직을 명령했다.", result.company_summary)
        self.assertNotIn("디지털 구독 인쇄판", result.company_summary)

    def test_low_confidence_context_falls_back_to_meta_description(self):
        enricher = ArticleEnricher(config=None)
        result = enricher.enrich(
            source_language="ko",
            title="BTS 복귀 앞두고 하이브에 더 큰 검증 요구",
            summary="",
            matched_companies=["HYBE"],
            matched_aliases=["하이브"],
            context=ArticleContext(
                relevant_sentences=[],
                summary_sentences=[
                    "강해련은 서울에서 활동하는 영화 제작자이자 저널리스트입니다.",
                    "다음 기사 보기 미디어 & 엔터테인먼트 BTS 컴백 쇼.",
                ],
                meta_description="BTS 복귀를 앞두고 HYBE의 지배구조와 해외 확장 전략에 대한 검증 요구가 커지고 있다.",
                low_confidence=True,
            ),
        )

        self.assertIn(
            "BTS 복귀를 앞두고 HYBE의 지배구조와 해외 확장 전략에 대한 검증 요구가 커지고 있다.",
            result.company_summary,
        )
        self.assertNotIn("영화 제작자이자 저널리스트", result.company_summary)
        self.assertNotIn("다음 기사 보기", result.company_summary)

    @patch("src.kor_companies.enrichment.urlopen")
    def test_google_translate_translates_title_and_company_summary(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(
            {
                "data": {
                    "translations": [
                        {"translatedText": "기아가 일본에서 신형 EV를 공개"},
                        {"translatedText": "전시회에서 신형 EV를 소개했다."},
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
        self.assertIn("Kia 관련 기사다.", result.company_summary)
        self.assertIn("기사 제목은 '기아가 일본에서 신형 EV를 공개'이다.", result.company_summary)
        self.assertIn("전시회에서 신형 EV를 소개했다.", result.company_summary)
        self.assertIn("현지 딜러 네트워크 확대 계획도 공개했다.", result.company_summary)
        self.assertGreaterEqual(
            result.company_summary.count(".") + result.company_summary.count("。"),
            5,
        )
        self.assertEqual(result.translated_summary, result.company_summary)


if __name__ == "__main__":
    unittest.main()
