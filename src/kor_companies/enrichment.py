from __future__ import annotations

import json
import os
from dataclasses import dataclass
from html import unescape
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .article_context import ArticleContext
from .matcher import is_short_latin_alias
from .utils import normalize_whitespace


class EnrichmentError(RuntimeError):
    """Raised when enrichment fails."""


@dataclass
class EnrichmentResult:
    is_related: bool
    translated_title: str
    translated_summary: str
    company_summary: str
    reason: str = ""


@dataclass
class GoogleTranslateConfig:
    api_key: str
    base_url: str = "https://translation.googleapis.com/language/translate/v2"

    @classmethod
    def from_env(cls) -> Optional["GoogleTranslateConfig"]:
        api_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "").strip()
        if not api_key:
            return None
        return cls(api_key=api_key)


class ArticleEnricher:
    def __init__(self, config: Optional[GoogleTranslateConfig]) -> None:
        self.config = config

    @classmethod
    def from_env(cls) -> "ArticleEnricher":
        return cls(GoogleTranslateConfig.from_env())

    def enrich(
        self,
        source_language: str,
        title: str,
        summary: str,
        matched_companies: List[str],
        matched_aliases: List[str],
        context: ArticleContext,
    ) -> EnrichmentResult:
        if self._looks_like_short_alias_false_positive(matched_aliases, context):
            return EnrichmentResult(
                is_related=False,
                translated_title=title,
                translated_summary=summary,
                company_summary="",
                reason="short_alias_without_company_context",
            )

        company_summary_source = self._build_company_summary_source(summary, context)
        if self.config is None or source_language.casefold().startswith("ko"):
            return self._heuristic_result(title, summary, matched_companies, company_summary_source)

        try:
            translated_title, translated_company_summary = self._translate_texts(
                [title, company_summary_source],
                target_language="ko",
            )
        except EnrichmentError:
            return self._heuristic_result(title, summary, matched_companies, company_summary_source)

        formatted_company_summary = self._format_company_summary(
            matched_companies,
            translated_company_summary or company_summary_source or summary,
        )
        return EnrichmentResult(
            is_related=True,
            translated_title=translated_title or title,
            translated_summary=formatted_company_summary,
            company_summary=formatted_company_summary,
        )

    def _heuristic_result(
        self,
        title: str,
        summary: str,
        matched_companies: List[str],
        company_summary_source: str,
    ) -> EnrichmentResult:
        formatted_company_summary = self._format_company_summary(
            matched_companies,
            company_summary_source or summary or "요약 없음",
        )
        return EnrichmentResult(
            is_related=True,
            translated_title=title,
            translated_summary=formatted_company_summary,
            company_summary=formatted_company_summary,
        )

    def _build_company_summary_source(self, summary: str, context: ArticleContext) -> str:
        return normalize_whitespace(
            " ".join(context.relevant_sentences[:2]) or context.meta_description or summary
        )

    def _format_company_summary(self, matched_companies: List[str], body: str) -> str:
        normalized_body = normalize_whitespace(body)
        if not normalized_body:
            return "요약 없음"
        if matched_companies:
            return f"{', '.join(matched_companies)} 관련 내용: {normalized_body}"
        return normalized_body

    def _translate_texts(self, texts: List[str], target_language: str) -> List[str]:
        assert self.config is not None
        translated = list(texts)
        indexed_texts = [
            (index, normalize_whitespace(text))
            for index, text in enumerate(texts)
            if normalize_whitespace(text)
        ]
        if not indexed_texts:
            return translated

        request_url = f"{self.config.base_url}?{urlencode({'key': self.config.api_key})}"
        body = {
            "q": [text for _, text in indexed_texts],
            "target": target_language,
            "format": "text",
        }
        request = Request(
            request_url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EnrichmentError(f"Google Translate HTTP {exc.code}") from exc
        except URLError as exc:
            raise EnrichmentError(f"Google Translate URL error: {exc.reason}") from exc
        except OSError as exc:
            raise EnrichmentError(f"Google Translate I/O error: {exc}") from exc

        try:
            items = payload["data"]["translations"]
        except KeyError as exc:
            raise EnrichmentError("Google Translate returned invalid JSON") from exc
        if len(items) != len(indexed_texts):
            raise EnrichmentError("Google Translate returned an unexpected item count")

        for (index, _), item in zip(indexed_texts, items):
            translated[index] = normalize_whitespace(unescape(item.get("translatedText", "")))
        return translated

    def _looks_like_short_alias_false_positive(
        self, matched_aliases: List[str], context: ArticleContext
    ) -> bool:
        if context.has_relevant_sentences:
            return False
        if not matched_aliases:
            return False
        return all(is_short_latin_alias(alias) for alias in matched_aliases)
