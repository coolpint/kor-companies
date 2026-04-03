from __future__ import annotations

import re
from typing import Iterable, List, Sequence
from urllib.parse import urlencode, urlsplit

from .models import CompanyConfig, FeedEntry, GoogleNewsConfig, SourceConfig
from .utils import normalize_whitespace

GOOGLE_NEWS_BASE_URL = "https://news.google.com/rss/search"
HANGUL_RE = re.compile(r"[\uac00-\ud7a3]")


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
        if source_host and (
            self._host_matches(source_host, self._blocked_domains)
            or self._host_matches(source_host, self._existing_hosts)
            or source_host.endswith(".kr")
        ):
            return False
        if HANGUL_RE.search(source_name):
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
