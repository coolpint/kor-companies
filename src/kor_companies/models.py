from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class CountryConfig:
    country_code: str
    country_name_ko: str
    country_name_en: str
    priority: str
    languages: List[str]
    active: bool = True


@dataclass
class CompanyConfig:
    canonical_name_ko: str
    canonical_name_en: str
    group_name: str
    aliases_en: List[str]
    aliases_ko: List[str]
    aliases_local: List[str]
    primary_brands: List[str]
    active: bool = True

    def all_aliases(self) -> List[str]:
        merged: List[str] = [
            self.canonical_name_en,
            self.canonical_name_ko,
            *self.aliases_en,
            *self.aliases_ko,
            *self.aliases_local,
            *self.primary_brands,
        ]
        seen = set()
        deduped = []
        for alias in merged:
            value = alias.strip()
            if not value:
                continue
            lowered = value.casefold()
            if lowered in seen:
                continue
            seen.add(lowered)
            deduped.append(value)
        return deduped


@dataclass
class SourceConfig:
    source_id: str
    source_name: str
    country_code: str
    feed_url: str
    homepage_url: str
    language: str
    category: str
    enabled: bool = True
    trust_tier: int = 1
    max_items: Optional[int] = None
    notes: str = ""


@dataclass
class FeedEntry:
    source_id: str
    source_name: str
    country_code: str
    title: str
    link: str
    summary: str
    published_at: Optional[datetime]
    guid: str = ""
    origin_source_name: str = ""
    origin_source_url: str = ""


@dataclass
class MatchedArticle:
    article_key: str
    canonical_link: str
    link: str
    title: str
    summary: str
    published_at: Optional[datetime]
    source_id: str
    source_name: str
    country_code: str
    country_name_ko: str
    source_language: str = ""
    original_title: str = ""
    original_summary: str = ""
    company_summary: str = ""
    matched_companies: List[str] = field(default_factory=list)
    matched_aliases: List[str] = field(default_factory=list)
    is_new: bool = True


@dataclass
class SourceRunResult:
    source_id: str
    source_name: str
    country_code: str
    success: bool
    item_count: int = 0
    matched_count: int = 0
    error: str = ""


@dataclass
class GoogleNewsCountryConfig:
    country_code: str
    hl: str
    gl: str
    ceid: str
    language: str
    enabled: bool = True


@dataclass
class GoogleNewsConfig:
    enabled: bool = True
    batch_size: int = 6
    max_items_per_feed: int = 20
    countries: List[GoogleNewsCountryConfig] = field(default_factory=list)
    excluded_domains: List[str] = field(default_factory=list)
    excluded_source_names: List[str] = field(default_factory=list)
    excluded_title_patterns: List[str] = field(default_factory=list)
