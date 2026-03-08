from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import List

from .fetcher import FetchError, fetch_url
from .matcher import find_matching_aliases
from .utils import normalize_whitespace, short_text

META_DESCRIPTION_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?。！？])")
BOILERPLATE_MARKERS = (
    "メニュー",
    "閉じる",
    "シェアする",
    "NHKニュース",
    "注目ワード",
    "関連記事",
)


@dataclass
class ArticleContext:
    relevant_sentences: List[str]
    meta_description: str = ""
    text_excerpt: str = ""
    fetch_error: str = ""

    @property
    def has_relevant_sentences(self) -> bool:
        return bool(self.relevant_sentences)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    def text(self) -> str:
        return normalize_whitespace(" ".join(self._parts))


def build_article_context(url: str, aliases: List[str], timeout: int = 20) -> ArticleContext:
    try:
        response = fetch_url(
            url,
            timeout=timeout,
            accept="text/html, application/xhtml+xml;q=0.9, text/plain;q=0.8, */*;q=0.5",
        )
    except FetchError as exc:
        return ArticleContext(relevant_sentences=[], fetch_error=str(exc))

    html = _decode_html(response.body)
    meta_description = _extract_meta_description(html)
    text = _extract_text(html)
    relevant_sentences = _select_relevant_sentences(text, aliases)
    excerpt_source = " ".join(relevant_sentences[:3]) if relevant_sentences else meta_description or text

    return ArticleContext(
        relevant_sentences=relevant_sentences[:3],
        meta_description=meta_description,
        text_excerpt=short_text(excerpt_source, 1200),
    )


def _decode_html(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "shift_jis", "euc-jp", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="ignore")


def _extract_meta_description(html: str) -> str:
    match = META_DESCRIPTION_RE.search(html)
    if not match:
        return ""
    return normalize_whitespace(unescape(match.group(1)))


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def _select_relevant_sentences(text: str, aliases: List[str]) -> List[str]:
    if not text:
        return []
    sentences = [normalize_whitespace(part) for part in SENTENCE_SPLIT_RE.split(text)]
    relevant = []
    for sentence in sentences:
        if len(sentence) < 12:
            continue
        if any(marker in sentence for marker in BOILERPLATE_MARKERS):
            continue
        if sentence.count("|") >= 2:
            continue
        if find_matching_aliases(sentence, aliases):
            relevant.append(sentence)
        if len(relevant) >= 3:
            break
    return relevant
