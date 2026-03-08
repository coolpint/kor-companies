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
