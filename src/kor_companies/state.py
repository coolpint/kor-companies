from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable

from .models import MatchedArticle
from .utils import isoformat_or_none, sha1_digest, utc_now


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> Dict:
        if not self.path.exists():
            return {"version": 1, "last_run_at": None, "seen_articles": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def contains(self, article_key: str) -> bool:
        return article_key in self.data.get("seen_articles", {})

    def mark_seen(self, articles: Iterable[MatchedArticle], run_at: datetime) -> None:
        seen_articles = self.data.setdefault("seen_articles", {})
        run_at_iso = isoformat_or_none(run_at)
        for article in articles:
            record = seen_articles.get(article.article_key, {})
            record["title"] = article.title
            record["link"] = article.canonical_link
            record["source_name"] = article.source_name
            record["country_code"] = article.country_code
            record["companies"] = article.matched_companies
            record["first_seen_at"] = record.get("first_seen_at") or run_at_iso
            record["last_seen_at"] = run_at_iso
            seen_articles[article.article_key] = record
        self.data["last_run_at"] = run_at_iso

    def prune(self, retention_days: int = 45) -> None:
        threshold = utc_now() - timedelta(days=retention_days)
        kept = {}
        for key, value in self.data.get("seen_articles", {}).items():
            last_seen = value.get("last_seen_at")
            if not last_seen:
                continue
            try:
                parsed = datetime.fromisoformat(last_seen)
            except ValueError:
                continue
            if parsed >= threshold:
                kept[key] = value
        self.data["seen_articles"] = kept

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_article_key(canonical_link: str, title: str, source_id: str) -> str:
    if canonical_link:
        return canonical_link
    return sha1_digest([title, source_id])

