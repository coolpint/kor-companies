from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .models import (
    CompanyConfig,
    CountryConfig,
    GoogleNewsConfig,
    GoogleNewsCountryConfig,
    SourceConfig,
)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_companies(path: Path) -> List[CompanyConfig]:
    data = _load_json(path)
    return [CompanyConfig(**item) for item in data if item.get("active", True)]


def load_countries(path: Path) -> Dict[str, CountryConfig]:
    data = _load_json(path)
    countries = [CountryConfig(**item) for item in data if item.get("active", True)]
    return {country.country_code: country for country in countries}


def load_sources(path: Path, allowed_countries: Sequence[str] | None = None) -> List[SourceConfig]:
    country_filter = set(allowed_countries or [])
    data = _load_json(path)
    sources = []
    for item in data:
        if not item.get("enabled", True):
            continue
        if country_filter and item["country_code"] not in country_filter:
            continue
        sources.append(SourceConfig(**item))
    return sources


def load_google_news_config(
    path: Path, allowed_countries: Sequence[str] | None = None
) -> Optional[GoogleNewsConfig]:
    if not path.exists():
        return None

    data = _load_json(path)
    if not data.get("enabled", True):
        return None

    country_filter = set(allowed_countries or [])
    countries = []
    for item in data.get("countries", []):
        if not item.get("enabled", True):
            continue
        if country_filter and item["country_code"] not in country_filter:
            continue
        countries.append(GoogleNewsCountryConfig(**item))

    if not countries:
        return None

    return GoogleNewsConfig(
        enabled=True,
        batch_size=data.get("batch_size", 6),
        max_items_per_feed=data.get("max_items_per_feed", 20),
        countries=countries,
        excluded_domains=data.get("excluded_domains", []),
        excluded_source_names=data.get("excluded_source_names", []),
        excluded_title_patterns=data.get("excluded_title_patterns", []),
    )
