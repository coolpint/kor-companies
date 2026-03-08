from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .article_context import ArticleContext
from .matcher import is_short_latin_alias
from .utils import normalize_whitespace, short_text


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
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4.1-mini"
    base_url: str = "https://api.openai.com/v1/chat/completions"

    @classmethod
    def from_env(cls) -> Optional["OpenAIConfig"]:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            return None
        model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4.1-mini"
        return cls(api_key=api_key, model=model)


class ArticleEnricher:
    def __init__(self, config: Optional[OpenAIConfig]) -> None:
        self.config = config

    @classmethod
    def from_env(cls) -> "ArticleEnricher":
        return cls(OpenAIConfig.from_env())

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

        if self.config is None:
            return self._heuristic_result(title, summary, matched_companies, context)
        try:
            return self._openai_result(
                source_language=source_language,
                title=title,
                summary=summary,
                matched_companies=matched_companies,
                matched_aliases=matched_aliases,
                context=context,
            )
        except EnrichmentError:
            return self._heuristic_result(title, summary, matched_companies, context)

    def _heuristic_result(
        self,
        title: str,
        summary: str,
        matched_companies: List[str],
        context: ArticleContext,
    ) -> EnrichmentResult:
        company_summary = normalize_whitespace(
            " ".join(context.relevant_sentences[:2]) or context.meta_description or summary
        )
        if matched_companies and company_summary:
            company_summary = f"{', '.join(matched_companies)} 관련 내용: {company_summary}"
        return EnrichmentResult(
            is_related=True,
            translated_title=title,
            translated_summary=company_summary or summary or "요약 없음",
            company_summary=company_summary or summary or "요약 없음",
        )

    def _openai_result(
        self,
        source_language: str,
        title: str,
        summary: str,
        matched_companies: List[str],
        matched_aliases: List[str],
        context: ArticleContext,
    ) -> EnrichmentResult:
        assert self.config is not None
        prompt_payload = {
            "source_language": source_language,
            "title": title,
            "feed_summary": summary,
            "matched_companies": matched_companies,
            "matched_aliases": matched_aliases,
            "company_related_sentences": context.relevant_sentences,
            "article_context_excerpt": context.text_excerpt,
        }
        body = {
            "model": self.config.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You convert foreign news alerts into Korean monitoring output. "
                        "Always respond with JSON. "
                        "Rules: 1) translated_title must be natural Korean. "
                        "2) translated_summary must be Korean and must explicitly say how the Korean company is involved. "
                        "3) company_summary must focus only on the Korean company-related point in Korean. "
                        "4) If the article is not genuinely related to the matched Korean company, set is_related to false."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, ensure_ascii=False),
                },
            ],
        }

        request = Request(
            self.config.base_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EnrichmentError(f"OpenAI HTTP {exc.code}") from exc
        except URLError as exc:
            raise EnrichmentError(f"OpenAI URL error: {exc.reason}") from exc
        except OSError as exc:
            raise EnrichmentError(f"OpenAI I/O error: {exc}") from exc

        try:
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            raise EnrichmentError("OpenAI returned invalid JSON") from exc

        return EnrichmentResult(
            is_related=bool(parsed.get("is_related", True)),
            translated_title=normalize_whitespace(parsed.get("translated_title") or title),
            translated_summary=normalize_whitespace(parsed.get("translated_summary") or summary),
            company_summary=normalize_whitespace(
                parsed.get("company_summary") or parsed.get("translated_summary") or summary
            ),
            reason=normalize_whitespace(parsed.get("reason", "")),
        )

    def _looks_like_short_alias_false_positive(
        self, matched_aliases: List[str], context: ArticleContext
    ) -> bool:
        if context.has_relevant_sentences:
            return False
        if not matched_aliases:
            return False
        return all(is_short_latin_alias(alias) for alias in matched_aliases)

