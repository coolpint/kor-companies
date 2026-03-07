from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .config import load_companies, load_countries, load_sources
from .feed_parser import FeedParseError, parse_feed
from .fetcher import FetchError, fetch_feed
from .matcher import CompanyMatcher
from .models import MatchedArticle, SourceRunResult
from .reporting import write_reports
from .state import StateStore, build_article_key
from .utils import canonicalize_url, normalize_whitespace, utc_now


@dataclass
class MonitorRunSummary:
    run_at: datetime
    matched_articles: List[MatchedArticle]
    new_articles: List[MatchedArticle]
    source_runs: List[SourceRunResult]
    report_paths: Dict[str, Path]


def run_monitor(
    config_dir: Path,
    output_dir: Path,
    state_path: Path,
    since_hours: int = 36,
    max_items_per_feed: int = 80,
    country_codes: Optional[Sequence[str]] = None,
) -> MonitorRunSummary:
    companies = load_companies(config_dir / "companies.json")
    countries = load_countries(config_dir / "countries.json")
    sources = load_sources(config_dir / "sources.json", allowed_countries=country_codes)
    matcher = CompanyMatcher(companies)
    state = StateStore(state_path)

    run_at = utc_now()
    cutoff = run_at - timedelta(hours=since_hours)

    matched_by_key: Dict[str, MatchedArticle] = {}
    source_runs: List[SourceRunResult] = []

    for source in sources:
        try:
            response = fetch_feed(source.feed_url)
            entries = parse_feed(source, response.body)
        except (FetchError, FeedParseError) as exc:
            source_runs.append(
                SourceRunResult(
                    source_id=source.source_id,
                    source_name=source.source_name,
                    country_code=source.country_code,
                    success=False,
                    error=str(exc),
                )
            )
            continue

        matched_count = 0
        for entry in entries[:max_items_per_feed]:
            if entry.published_at and entry.published_at < cutoff:
                continue

            match_results = matcher.match("\n".join([entry.title, entry.summary]))
            if not match_results:
                continue

            matched_count += 1
            canonical_link = canonicalize_url(entry.link)
            article_key = build_article_key(canonical_link, entry.title, source.source_id)
            country = countries.get(source.country_code)
            country_name_ko = country.country_name_ko if country else source.country_code

            article = matched_by_key.get(article_key)
            matched_companies = [result.company.canonical_name_en for result in match_results]
            matched_aliases = [alias for result in match_results for alias in result.aliases]

            if article is None:
                matched_by_key[article_key] = MatchedArticle(
                    article_key=article_key,
                    canonical_link=canonical_link,
                    link=entry.link,
                    title=normalize_whitespace(entry.title),
                    summary=normalize_whitespace(entry.summary),
                    published_at=entry.published_at,
                    source_id=source.source_id,
                    source_name=source.source_name,
                    country_code=source.country_code,
                    country_name_ko=country_name_ko,
                    matched_companies=_dedupe_preserve_order(matched_companies),
                    matched_aliases=_dedupe_preserve_order(matched_aliases),
                )
            else:
                article.matched_companies = _dedupe_preserve_order(
                    article.matched_companies + matched_companies
                )
                article.matched_aliases = _dedupe_preserve_order(
                    article.matched_aliases + matched_aliases
                )
                if not article.summary and entry.summary:
                    article.summary = normalize_whitespace(entry.summary)
                if article.published_at is None and entry.published_at is not None:
                    article.published_at = entry.published_at

        source_runs.append(
            SourceRunResult(
                source_id=source.source_id,
                source_name=source.source_name,
                country_code=source.country_code,
                success=True,
                item_count=len(entries),
                matched_count=matched_count,
            )
        )

    matched_articles = sorted(
        matched_by_key.values(),
        key=lambda item: item.published_at or run_at,
        reverse=True,
    )
    for article in matched_articles:
        article.is_new = not state.contains(article.article_key)
    new_articles = [item for item in matched_articles if item.is_new]

    state.mark_seen(matched_articles, run_at)
    state.prune()
    state.save()

    report_paths = write_reports(output_dir, run_at, matched_articles, new_articles, source_runs)
    return MonitorRunSummary(
        run_at=run_at,
        matched_articles=matched_articles,
        new_articles=new_articles,
        source_runs=source_runs,
        report_paths=report_paths,
    )


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    deduped = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped
