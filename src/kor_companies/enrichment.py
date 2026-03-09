from __future__ import annotations

import json
import os
import re
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


SUMMARY_SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?。！？])\s*")


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

        feed_summary_source = normalize_whitespace(summary or context.meta_description)
        context_summary_source = self._build_company_summary_source(summary, context)
        if self.config is None or source_language.casefold().startswith("ko"):
            return self._heuristic_result(
                title=title,
                matched_companies=matched_companies,
                feed_summary_source=feed_summary_source,
                context_summary_source=context_summary_source,
            )

        try:
            translated_title, translated_feed_summary, translated_context_summary = self._translate_texts(
                [title, feed_summary_source, context_summary_source],
                target_language="ko",
            )
        except EnrichmentError:
            return self._heuristic_result(
                title=title,
                matched_companies=matched_companies,
                feed_summary_source=feed_summary_source,
                context_summary_source=context_summary_source,
            )

        formatted_company_summary = self._compose_company_summary(
            matched_companies=matched_companies,
            translated_title=translated_title or title,
            translated_feed_summary=translated_feed_summary or feed_summary_source,
            translated_context_summary=translated_context_summary or context_summary_source,
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
        matched_companies: List[str],
        feed_summary_source: str,
        context_summary_source: str,
    ) -> EnrichmentResult:
        formatted_company_summary = self._compose_company_summary(
            matched_companies=matched_companies,
            translated_title=title,
            translated_feed_summary=feed_summary_source,
            translated_context_summary=context_summary_source,
        )
        return EnrichmentResult(
            is_related=True,
            translated_title=title,
            translated_summary=formatted_company_summary,
            company_summary=formatted_company_summary,
        )

    def _build_company_summary_source(self, summary: str, context: ArticleContext) -> str:
        return normalize_whitespace(
            " ".join(context.summary_sentences[:5])
            or " ".join(context.relevant_sentences[:3])
            or context.meta_description
            or summary
        )

    def _compose_company_summary(
        self,
        matched_companies: List[str],
        translated_title: str,
        translated_feed_summary: str,
        translated_context_summary: str,
    ) -> str:
        sentences: List[str] = []

        if matched_companies:
            sentences.append(self._ensure_sentence(f"{', '.join(matched_companies)} 관련 기사다"))
        if translated_title:
            sentences.append(self._ensure_sentence(f"기사 제목은 '{translated_title}'이다"))

        for candidate in self._split_summary_sentences(translated_feed_summary):
            self._append_unique_sentence(sentences, candidate)
        for candidate in self._split_summary_sentences(translated_context_summary):
            self._append_unique_sentence(sentences, candidate)

        fallback_sentences = [
            "이 기사는 해당 기업과 연결된 해외 보도를 바탕으로 정리했다.",
            "가능한 경우 본문에서 회사 언급 전후 문맥을 함께 반영했다.",
            "세부 내용은 원문 링크에서 추가로 확인할 수 있다.",
        ]
        for candidate in fallback_sentences:
            self._append_unique_sentence(sentences, candidate)
            if len(sentences) >= 5:
                break

        if not sentences:
            return "요약 없음"
        return " ".join(sentences[:8])

    def _split_summary_sentences(self, text: str) -> List[str]:
        normalized = normalize_whitespace(text)
        if not normalized:
            return []
        return [
            self._ensure_sentence(part)
            for part in SUMMARY_SENTENCE_SPLIT_RE.split(normalized)
            if normalize_whitespace(part)
        ]

    def _append_unique_sentence(self, sentences: List[str], candidate: str) -> None:
        normalized_candidate = normalize_whitespace(candidate)
        if not normalized_candidate:
            return
        candidate_key = self._sentence_key(normalized_candidate)
        if any(self._sentence_key(existing) == candidate_key for existing in sentences):
            return
        sentences.append(normalized_candidate)

    def _sentence_key(self, sentence: str) -> str:
        return re.sub(r"[^\w가-힣\u3040-\u30ff\u3400-\u9fff]+", "", sentence).casefold()

    def _ensure_sentence(self, text: str) -> str:
        normalized = normalize_whitespace(text)
        if not normalized:
            return ""
        if normalized[-1] in ".!?。！？":
            return normalized
        return normalized + "."

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
