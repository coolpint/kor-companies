from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Dict, Iterable, List
from zoneinfo import ZoneInfo

from .models import MatchedArticle, SourceRunResult
from .utils import isoformat_or_none, short_text

KST = ZoneInfo("Asia/Seoul")


def write_reports(
    output_dir: Path,
    run_at,
    matched_articles: List[MatchedArticle],
    new_articles: List[MatchedArticle],
    source_runs: List[SourceRunResult],
) -> Dict[str, Path]:
    archive_dir = output_dir / "archive" / run_at.astimezone(KST).strftime("%Y-%m")
    archive_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = run_at.astimezone(KST).strftime("%Y%m%d-%H%M%S")
    archive_md = archive_dir / f"monitor-{timestamp}.md"
    archive_json = archive_dir / f"monitor-{timestamp}.json"
    latest_md = output_dir / "latest.md"
    latest_json = output_dir / "latest.json"

    markdown = _build_markdown(run_at, matched_articles, new_articles, source_runs)
    payload = _build_json(run_at, matched_articles, new_articles, source_runs)

    archive_md.write_text(markdown, encoding="utf-8")
    latest_md.write_text(markdown, encoding="utf-8")
    archive_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    latest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "archive_md": archive_md,
        "archive_json": archive_json,
        "latest_md": latest_md,
        "latest_json": latest_json,
    }


def _build_markdown(run_at, matched_articles, new_articles, source_runs) -> str:
    lines = [
        "# 해외 언론 한국 기업 모니터링",
        "",
        f"- 실행 시각: {run_at.astimezone(KST).strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"- 활성 소스: {len(source_runs)}개",
        f"- 정상 수집: {sum(1 for item in source_runs if item.success)}개",
        f"- 실패 소스: {sum(1 for item in source_runs if not item.success)}개",
        f"- 매칭 기사: {len(matched_articles)}건",
        f"- 신규 기사: {len(new_articles)}건",
        "",
        "## 신규 기사",
        "",
    ]

    if not new_articles:
        lines.append("- 신규로 감지된 기사가 없다.")
    else:
        for article in new_articles:
            published = (
                article.published_at.astimezone(KST).strftime("%Y-%m-%d %H:%M %Z")
                if article.published_at
                else "발행시각 없음"
            )
            lines.extend(
                [
                    f"### {article.title}",
                    "",
                    f"- 회사: {', '.join(article.matched_companies)}",
                    f"- 국가/매체: {article.country_name_ko} / {article.source_name}",
                    f"- 발행 시각: {published}",
                    f"- 링크: {article.link}",
                    f"- 매칭 별칭: {', '.join(article.matched_aliases)}",
                    f"- 원문 제목: {article.original_title or article.title}",
                    f"- 요약: {short_text(article.company_summary or article.summary or '요약 없음', 280)}",
                    "",
                ]
            )

    failed_sources = [item for item in source_runs if not item.success]
    if failed_sources:
        lines.extend(["## 실패한 소스", ""])
        for item in failed_sources:
            lines.append(f"- {item.source_name}: {item.error}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _build_json(run_at, matched_articles, new_articles, source_runs) -> Dict:
    return {
        "run_at": isoformat_or_none(run_at),
        "summary": {
            "source_count": len(source_runs),
            "success_count": sum(1 for item in source_runs if item.success),
            "failed_count": sum(1 for item in source_runs if not item.success),
            "matched_count": len(matched_articles),
            "new_count": len(new_articles),
        },
        "new_articles": [_serialize_article(item) for item in new_articles],
        "matched_articles": [_serialize_article(item) for item in matched_articles],
        "source_runs": [asdict(item) for item in source_runs],
    }


def _serialize_article(article: MatchedArticle) -> Dict:
    return {
        "article_key": article.article_key,
        "canonical_link": article.canonical_link,
        "link": article.link,
        "title": article.title,
        "summary": article.summary,
        "original_title": article.original_title,
        "original_summary": article.original_summary,
        "company_summary": article.company_summary,
        "published_at": isoformat_or_none(article.published_at),
        "source_id": article.source_id,
        "source_name": article.source_name,
        "country_code": article.country_code,
        "country_name_ko": article.country_name_ko,
        "source_language": article.source_language,
        "matched_companies": article.matched_companies,
        "matched_aliases": article.matched_aliases,
        "is_new": article.is_new,
    }
