import unittest

from src.kor_companies.matcher import CompanyMatcher, find_matching_aliases
from src.kor_companies.models import CompanyConfig


class MatcherTests(unittest.TestCase):
    def test_non_latin_alias_does_not_match_inside_longer_word(self):
        self.assertEqual(find_matching_aliases("ペゼシュキアン大統領", ["キア"]), [])

    def test_katakana_alias_matches_before_particle(self):
        self.assertEqual(find_matching_aliases("キアは日本で신형 EV를 공개했다.", ["キア"]), ["キア"])

    def test_non_latin_alias_matches_standalone_company_mention(self):
        self.assertEqual(find_matching_aliases("起亜は日本で新型EVを公開した。", ["起亜"]), ["起亜"])

    def test_company_matcher_avoids_false_positive_for_japanese_alias(self):
        matcher = CompanyMatcher(
            [
                CompanyConfig(
                    canonical_name_ko="기아",
                    canonical_name_en="Kia",
                    group_name="현대자동차그룹",
                    aliases_ko=["기아"],
                    aliases_en=["Kia"],
                    aliases_local=["キア", "起亜"],
                    primary_brands=[],
                    active=True,
                )
            ]
        )
        self.assertEqual(
            matcher.match("トランプ大統領は成果を強調 湾岸諸国ではイランの攻撃相次ぐ ペゼシュキアン大統領"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
