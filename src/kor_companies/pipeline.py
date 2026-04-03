from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .article_context import ArticleContext, build_article_context
from .config import load_companies, load_countries, load_google_news_config, load_sources
from .enrichment import ArticleEnricher
from .feed_parser import FeedParseError, parse_feed
from .fetcher import FetchError, fetch_feed
from .google_news import GoogleNewsEntryFilter, build_google_news_sources, is_google_news_source
from .matcher import CompanyMatcher
from .models import CompanyConfig, MatchedArticle, SourceRunResult
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
    static_sources = load_sources(config_dir / "sources.json", allowed_countries=country_codes)
    google_news_config = load_google_news_config(
        config_dir / "google_news.json",
        allowed_countries=country_codes,
    )
    google_news_sources = build_google_news_sources(google_news_config, companies)
    sources = static_sources + google_news_sources
    matcher = CompanyMatcher(companies)
    google_news_matcher = CompanyMatcher(_companies_without_primary_brands(companies))
    google_news_filter = (
        GoogleNewsEntryFilter(
            config=google_news_config,
            companies=companies,
            existing_sources=static_sources,
        )
        if google_news_config is not None
        else None
    )
    enricher = ArticleEnricher.from_env()
    state = StateStore(state_path)

    run_at = utc_now()
    cutoff = run_at - timedelta(hours=since_hours)

    matched_by_key: Dict[str, MatchedArticle] = {}
    matched_by_fingerprint: Dict[str, str] = {}
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

        if google_news_filter is not None and is_google_news_source(source):
            entries = [entry for entry in entries if google_news_filter.allow(entry)]

        matched_count = 0
        limit = source.max_items or max_items_per_feed
        for entry in entries[:limit]:
            if entry.published_at and entry.published_at < cutoff:
                continue

            active_matcher = google_news_matcher if is_google_news_source(source) else matcher
            match_results = active_matcher.match("\n".join([entry.title, entry.summary]))
            if not match_results:
                continue

            matched_count += 1
            canonical_link = canonicalize_url(entry.link)
            display_source_name = entry.origin_source_name or source.source_name
            if is_google_news_source(source):
                article_key = _build_google_news_article_key(
                    source_name=display_source_name,
                    source_url=entry.origin_source_url,
                    title=entry.title,
                )
            else:
                article_key = build_article_key(canonical_link, entry.title, source.source_id)
            country = countries.get(source.country_code)
            country_name_ko = country.country_name_ko if country else source.country_code

            validation_aliases = _dedupe_preserve_order(
                [alias for result in match_results for alias in result.company.all_aliases()]
            )
            matched_companies = [result.company.canonical_name_en for result in match_results]
            article = matched_by_key.get(article_key)
            article_fingerprint = _build_article_fingerprint(display_source_name, entry.title)
            if article is None:
                existing_key = matched_by_fingerprint.get(article_fingerprint)
                if existing_key:
                    article = matched_by_key.get(existing_key)
            matched_aliases = [alias for result in match_results for alias in result.aliases]
            feed_summary = normalize_whitespace(entry.summary)
            if is_google_news_source(source):
                article_context = ArticleContext(relevant_sentences=[], low_confidence=True)
                if not feed_summary:
                    feed_summary = (
                        f"This article was picked up by Google News from {display_source_name}."
                    )
            else:
                article_context = build_article_context(entry.link, validation_aliases)
            resolved_published_at = entry.published_at or article_context.published_at_hint
            enrichment = enricher.enrich(
                source_language=source.language,
                title=normalize_whitespace(entry.title),
                summary=feed_summary,
                matched_companies=matched_companies,
                matched_aliases=matched_aliases,
                context=article_context,
                allow_title_only_matches=is_google_news_source(source),
            )
            if not enrichment.is_related:
                matched_count -= 1
                continue

            if article is None:
                matched_by_key[article_key] = MatchedArticle(
                    article_key=article_key,
                    canonical_link=canonical_link,
                    link=entry.link,
                    title=enrichment.translated_title or normalize_whitespace(entry.title),
                    summary=enrichment.translated_summary or feed_summary,
                    published_at=resolved_published_at,
                    source_id=source.source_id,
                    source_name=display_source_name,
                    country_code=source.country_code,
                    country_name_ko=country_name_ko,
                    source_language=source.language,
                    original_title=normalize_whitespace(entry.title),
                    original_summary=feed_summary,
                    company_summary=enrichment.company_summary,
                    matched_companies=_dedupe_preserve_order(matched_companies),
                    matched_aliases=_dedupe_preserve_order(matched_aliases),
                )
                matched_by_fingerprint[article_fingerprint] = article_key
            else:
                article.matched_companies = _dedupe_preserve_order(
                    article.matched_companies + matched_companies
                )
                article.matched_aliases = _dedupe_preserve_order(
                    article.matched_aliases + matched_aliases
                )
                if not article.summary and enrichment.translated_summary:
                    article.summary = enrichment.translated_summary
                if not article.company_summary and enrichment.company_summary:
                    article.company_summary = enrichment.company_summary
                if article.published_at is None and resolved_published_at is not None:
                    article.published_at = resolved_published_at
                if article.source_name == source.source_name and display_source_name:
                    article.source_name = display_source_name

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


def _build_article_fingerprint(source_name: str, title: str) -> str:
    return "\n".join(
        [
            normalize_whitespace(source_name).casefold(),
            normalize_whitespace(title).casefold(),
        ]
    )


def _build_google_news_article_key(source_name: str, source_url: str, title: str) -> str:
    return "\n".join(
        [
            normalize_whitespace(source_url or source_name).casefold(),
            normalize_whitespace(title).casefold(),
            "google_news",
        ]
    )


def _companies_without_primary_brands(companies: Sequence[CompanyConfig]) -> List[CompanyConfig]:
    return [
        CompanyConfig(
            canonical_name_ko=company.canonical_name_ko,
            canonical_name_en=company.canonical_name_en,
            group_name=company.group_name,
            aliases_en=list(company.aliases_en),
            aliases_ko=list(company.aliases_ko),
            aliases_local=list(company.aliases_local),
            primary_brands=[],
            active=company.active,
        )
        for company in companies
    ]
