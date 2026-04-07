from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable, List, Sequence
from urllib.parse import urlencode, urlsplit

from .models import CompanyConfig, FeedEntry, GoogleNewsConfig, SourceConfig
from .utils import normalize_whitespace

GOOGLE_NEWS_BASE_URL = "https://news.google.com/rss/search"
HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")
GOOGLE_NEWS_TITLE_TOKEN_RE = re.compile(r"[^\w\u00c0-\u024f\u3040-\u30ff\u3400-\u9fff\uac00-\ud7a3]+")
TRAILING_BRACKET_BLOCK_RE = re.compile(
    r"^(?P<prefix>.*?)(?:\s*[\(\（\[](?P<content>[^()\[\]（）]{1,40})[\)\）\]])\s*$"
)
KOREAN_NEWS_MARKERS = (
    "korea",
    "korean",
    "chosun",
    "joongang",
    "hankyung",
    "maeil",
    "mk.co",
    "sedaily",
    "yna",
    "yonhap",
    "donga",
    "khan",
    "munhwa",
    "newsis",
    "edaily",
    "etnews",
    "bizwatch",
    "dealsite",
    "seoulwire",
    "heraldcorp",
    "koreatimes",
    "koreaherald",
    "koreajoongangdaily",
    "kedglobal",
    "thelec",
    "businesskorea",
    "ajunews",
    "ajupress",
    "aju press",
    "아주경제",
    "매일경제",
    "조선일보",
    "중앙일보",
    "동아일보",
    "한국경제",
    "서울경제",
    "연합뉴스",
    "뉴스1",
    "뉴시스",
    "전자신문",
)
KOREAN_CITATION_MARKERS = (
    "yonhap",
    "yonhap news",
    "yonhap news agency",
    "연합뉴스",
    "聯合ニュース",
    "韩联社",
    "joongang",
    "중앙일보",
    "chosun",
    "조선일보",
    "maeil business",
    "매일경제",
    "hankyung",
    "한국경제",
    "seoul economic daily",
    "서울경제",
    "newsis",
    "뉴시스",
)
GOOGLE_NEWS_SYNDICATOR_MARKERS = (
    "yahoo",
    "news.yahoo.co.jp",
    "livedoor",
    "ライブドア",
    "msn",
    "smartnews",
    "newsbreak",
    "line news",
    "googlenews",
    "gooニュース",
    "infoseek",
)
TITLE_METADATA_MARKERS = (
    "掲載",
    "게재",
    "posted",
    "updated",
    "edition",
    "yahoo",
    "oricon",
    "オリコン",
    "livedoor",
    "ライブドア",
    "reuters",
)
GOOGLE_NEWS_FUZZY_DUPLICATE_MIN_RATIO = 0.58
GOOGLE_NEWS_NEAR_DUPLICATE_RATIO = 0.72
AMBIGUOUS_GOOGLE_NEWS_PATTERNS = {
    "kia": (
        re.compile(r"\bkia forum\b", re.IGNORECASE),
        re.compile(r"\bopen kia\b", re.IGNORECASE),
    ),
    "kakao": (
        re.compile(r"\bpreisalarm\b", re.IGNORECASE),
        re.compile(r"\bkaffee\b", re.IGNORECASE),
        re.compile(r"\btee\b", re.IGNORECASE),
        re.compile(r"\bmassiv teurer\b", re.IGNORECASE),
    ),
    "nexon": (
        re.compile(r"prix du carburant", re.IGNORECASE),
        re.compile(r"stations essence", re.IGNORECASE),
    ),
}


def build_google_news_sources(
    config: GoogleNewsConfig | None,
    companies: Sequence[CompanyConfig],
) -> List[SourceConfig]:
    if config is None or not config.enabled:
        return []

    terms = [company.canonical_name_en.strip() for company in companies if company.active]
    if not terms:
        return []

    sources: List[SourceConfig] = []
    for country in config.countries:
        for index, batch in enumerate(_chunked(terms, config.batch_size), start=1):
            query = " OR ".join(_quote_term(term) for term in batch)
            feed_url = f"{GOOGLE_NEWS_BASE_URL}?{urlencode({'q': query, 'hl': country.hl, 'gl': country.gl, 'ceid': country.ceid})}"
            sources.append(
                SourceConfig(
                    source_id=f"google_news_{country.country_code.casefold()}_{index:02d}",
                    source_name=f"Google News {country.country_code} #{index}",
                    country_code=country.country_code,
                    feed_url=feed_url,
                    homepage_url=(
                        "https://news.google.com/search?"
                        + urlencode({"q": query, "hl": country.hl, "gl": country.gl, "ceid": country.ceid})
                    ),
                    language=country.language,
                    category="google_news",
                    trust_tier=2,
                    max_items=config.max_items_per_feed,
                    notes="Google News 보조 수집. 원 매체 RSS 미보유 영역 확장용",
                )
            )
    return sources


def is_google_news_source(source: SourceConfig) -> bool:
    if source.category == "google_news":
        return True
    return _normalize_host(urlsplit(source.feed_url).netloc).endswith("news.google.com")


class GoogleNewsEntryFilter:
    def __init__(
        self,
        config: GoogleNewsConfig | None,
        companies: Sequence[CompanyConfig],
        existing_sources: Sequence[SourceConfig],
    ) -> None:
        self._config = config
        self._existing_hosts = {
            host
            for source in existing_sources
            for host in (
                _normalize_host(urlsplit(source.homepage_url).netloc),
                _normalize_host(urlsplit(source.feed_url).netloc),
            )
            if host
        }
        self._blocked_domains = {
            _normalize_host(domain) for domain in (config.excluded_domains if config else [])
        }
        self._blocked_source_names = [
            normalize_whitespace(name).casefold()
            for name in (config.excluded_source_names if config else [])
            if normalize_whitespace(name)
        ]
        self._blocked_title_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in (config.excluded_title_patterns if config else [])
        ]
        self._company_aliases = sorted(
            {
                normalize_whitespace(alias).casefold()
                for company in companies
                for alias in company.all_aliases()
                if normalize_whitespace(alias)
            },
            key=len,
            reverse=True,
        )

    def allow(self, entry: FeedEntry) -> bool:
        title = normalize_whitespace(entry.title)
        title_lower = title.casefold()
        source_name = normalize_whitespace(entry.origin_source_name)
        source_name_lower = source_name.casefold()
        source_host = _normalize_host(urlsplit(entry.origin_source_url).netloc)

        if any(pattern.search(title) for pattern in self._blocked_title_patterns):
            return False
        if "reuters" in title_lower and "reuters" not in source_name_lower:
            return False
        if any(marker in title_lower for marker in KOREAN_CITATION_MARKERS):
            return False
        if HANGUL_RE.search(title):
            return False
        if source_host and (
            self._host_matches(source_host, self._blocked_domains)
            or self._host_matches(source_host, self._existing_hosts)
            or source_host.endswith(".kr")
        ):
            return False
        if HANGUL_RE.search(source_name):
            return False
        if self._looks_like_korean_news_source(source_name_lower, source_host):
            return False
        if any(blocked in source_name_lower for blocked in self._blocked_source_names):
            return False
        if self._looks_like_company_owned_source(source_name_lower):
            return False
        return True

    def _looks_like_company_owned_source(self, source_name_lower: str) -> bool:
        if not source_name_lower:
            return False
        for alias in self._company_aliases:
            if source_name_lower == alias:
                return True
            if source_name_lower.startswith(alias + " "):
                return True
            if source_name_lower.endswith(" " + alias):
                return True
            if f"({alias})" in source_name_lower:
                return True
        return False

    def _host_matches(self, host: str, candidates: Iterable[str]) -> bool:
        return any(host == candidate or host.endswith("." + candidate) for candidate in candidates)

    def _looks_like_korean_news_source(self, source_name_lower: str, source_host: str) -> bool:
        haystacks = [source_name_lower, source_host]
        for haystack in haystacks:
            if not haystack:
                continue
            if any(marker in haystack for marker in KOREAN_NEWS_MARKERS):
                return True
        return False


def _quote_term(value: str) -> str:
    escaped = value.replace('"', "")
    return f'"{escaped}"'


def _chunked(values: Sequence[str], size: int) -> List[List[str]]:
    if size <= 0:
        size = 6
    return [list(values[index : index + size]) for index in range(0, len(values), size)]


def _normalize_host(value: str) -> str:
    host = (value or "").strip().casefold()
    if host.startswith("www."):
        host = host[4:]
    return host


def build_google_news_title_signature(
    title: str,
    matched_companies: Sequence[str],
    country_code: str,
) -> str:
    normalized_title = _normalize_google_news_title_for_dedupe(title)
    companies_key = "|".join(
        sorted(normalize_whitespace(item).casefold() for item in matched_companies)
    )
    return "\n".join([country_code.casefold(), companies_key, normalized_title])


def should_prefer_google_news_source(current_source_name: str, candidate_source_name: str) -> bool:
    current = normalize_whitespace(current_source_name).casefold()
    candidate = normalize_whitespace(candidate_source_name).casefold()
    if not candidate:
        return False
    if not current:
        return True

    current_is_syndicator = _looks_like_google_news_syndicator(current)
    candidate_is_syndicator = _looks_like_google_news_syndicator(candidate)
    if current_is_syndicator and not candidate_is_syndicator:
        return True
    if candidate_is_syndicator and not current_is_syndicator:
        return False
    return len(candidate) < len(current)


def are_google_news_titles_similar(
    left: str,
    right: str,
    matched_companies: Sequence[str] = (),
) -> bool:
    normalized_left = _normalize_google_news_title_for_dedupe(left)
    normalized_right = _normalize_google_news_title_for_dedupe(right)
    if not normalized_left or not normalized_right:
        return False
    if normalized_left == normalized_right:
        return True
    comparable_left = _strip_company_tokens(normalized_left, matched_companies)
    comparable_right = _strip_company_tokens(normalized_right, matched_companies)

    ratio = SequenceMatcher(None, comparable_left, comparable_right).ratio()
    if ratio >= GOOGLE_NEWS_NEAR_DUPLICATE_RATIO:
        return True

    tokens_left = {token for token in comparable_left.split() if len(token) >= 2}
    tokens_right = {token for token in comparable_right.split() if len(token) >= 2}
    shared_tokens = tokens_left & tokens_right
    if len(shared_tokens) >= 3 and ratio >= GOOGLE_NEWS_FUZZY_DUPLICATE_MIN_RATIO:
        return True
    if _shared_char_ngrams(comparable_left, comparable_right, 4) >= 6 and ratio >= 0.25:
        return True
    return False


def is_google_news_match_plausible(
    title: str,
    summary: str,
    matched_companies: Sequence[str],
) -> bool:
    text = normalize_whitespace(" ".join(part for part in (title, summary) if part))
    if not text:
        return True
    for company in matched_companies:
        patterns = AMBIGUOUS_GOOGLE_NEWS_PATTERNS.get(
            normalize_whitespace(company).casefold(),
            (),
        )
        if any(pattern.search(text) for pattern in patterns):
            return False
    return True


def _normalize_google_news_title_for_dedupe(title: str) -> str:
    value = normalize_whitespace(title)
    while True:
        match = TRAILING_BRACKET_BLOCK_RE.match(value)
        if not match:
            break
        content = normalize_whitespace(match.group("content"))
        if not _looks_like_title_metadata(content):
            break
        value = match.group("prefix").rstrip(" -|:")

    value = re.sub(r"\bby\s+reuters\b", "", value, flags=re.IGNORECASE)
    value = normalize_whitespace(value)
    tokenized = GOOGLE_NEWS_TITLE_TOKEN_RE.sub(" ", value)
    return normalize_whitespace(tokenized).casefold()


def _strip_company_tokens(title: str, matched_companies: Sequence[str]) -> str:
    cleaned = title
    for company in matched_companies:
        company_key = normalize_whitespace(company).casefold()
        if not company_key:
            continue
        cleaned = cleaned.replace(company_key, " ")
    return normalize_whitespace(cleaned)


def _shared_char_ngrams(left: str, right: str, size: int) -> int:
    compact_left = left.replace(" ", "")
    compact_right = right.replace(" ", "")
    if len(compact_left) < size or len(compact_right) < size:
        return 0
    left_ngrams = {compact_left[index : index + size] for index in range(len(compact_left) - size + 1)}
    right_ngrams = {
        compact_right[index : index + size] for index in range(len(compact_right) - size + 1)
    }
    return len(left_ngrams & right_ngrams)


def _looks_like_title_metadata(content: str) -> bool:
    lowered = content.casefold()
    if any(char.isdigit() for char in content):
        return True
    if any(marker in lowered for marker in TITLE_METADATA_MARKERS):
        return True
    return len(content) <= 12 and " " not in content


def _looks_like_google_news_syndicator(value: str) -> bool:
    lowered = normalize_whitespace(value).casefold()
    return any(marker in lowered for marker in GOOGLE_NEWS_SYNDICATOR_MARKERS)
