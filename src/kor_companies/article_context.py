from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any, List, Optional
from urllib.parse import urlsplit

from .feed_parser import parse_datetime
from .fetcher import FetchError, fetch_url
from .matcher import find_matching_aliases
from .utils import normalize_whitespace, short_text

META_DESCRIPTION_PATTERNS = (
    re.compile(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]+name=["\']twitter:description["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
)
META_DATE_PATTERNS = (
    re.compile(
        r'<meta[^>]+name=["\']date["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
        re.IGNORECASE,
    ),
    re.compile(
        r'"datePublished"\s*:\s*"([^"]+)"',
        re.IGNORECASE,
    ),
)
JSON_LD_SCRIPT_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?。！？])")
STRUCTURED_SUMMARY_KEYS = ("description", "alternativeHeadline")
SKIP_TEXT_TAGS = {
    "script",
    "style",
    "noscript",
    "svg",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "button",
    "head",
}
GENERIC_BOILERPLATE_MARKERS = (
    "メニュー",
    "閉じる",
    "シェアする",
    "NHKニュース",
    "注目ワード",
    "関連記事",
    "digital subscriber",
    "print edition",
    "link copied",
    "copy link",
    "continue reading",
    "read more",
    "sign up",
    "subscribe",
    "subscription",
    "latest news",
    "recommended stories",
    "related stories",
    "related articles",
    "privacy policy",
    "terms of use",
    "all rights reserved",
    "my account",
    "log out",
    "follow us",
    "home delivery",
    "newsletter",
    "advertisement",
    "supported by",
    "account settings",
    "デジタル版",
    "紙面",
    "購読",
    "共有",
    "ブックマーク",
    "最新ニュース",
    "sponsored content",
    "this content was commissioned",
)
TRAILING_BOILERPLATE_MARKERS = (
    "read next",
    "next article",
    "sponsored content",
    "sponsor content",
    "this content was commissioned",
    "nikkei global business bureau",
    "continue reading",
    "recommended stories",
    "related stories",
    "related articles",
)
TRAILING_BOILERPLATE_TOKENS = (
    "©",
    "copyright",
)
DOMAIN_BOILERPLATE_MARKERS = {
    "japantimes.co.jp": (
        "the japan times digital",
        "digital subscriber",
        "print edition",
        "share/save",
        "subscribe for full access",
    ),
    "asia.nikkei.com": (
        "exclusive subscriber content",
        "read next",
        "mission k-pop",
        "usg audio",
        "media & entertainment",
        "sponsored content",
        "nikkei global business bureau",
        "this content was commissioned",
    ),
    "theguardian.com": (
        "skip to main content",
        "support the guardian",
        "most viewed",
        "the week in patriarchy",
    ),
    "ft.com": (
        "subscribe to unlock",
        "make sense of",
        "share on x",
        "gift article",
    ),
}
SOCIAL_MARKERS = (
    "facebook",
    "linkedin",
    "reddit",
    "bluesky",
    "threads",
    "instagram",
    "youtube",
    "email",
    "bookmark",
    "copy link",
    "print",
)
AUTHOR_BIO_MARKERS = (
    "journalist",
    "columnist",
    "editor",
    "reporter",
    "producer",
    "filmmaker",
    "documentary",
    "podcast",
    "host",
)
CATEGORY_MARKERS = (
    "politics",
    "world",
    "business",
    "markets",
    "technology",
    "sports",
    "opinion",
    "lifestyle",
    "culture",
    "travel",
    "food",
    "style",
    "entertainment",
    "community",
    "economy",
    "science",
    "health",
    "society",
    "crime",
    "legal",
    "asia pacific",
    "asia-pacific",
    "environment",
    "climate",
    "energy",
    "history",
    "books",
    "music",
    "movies",
    "tv",
    "streaming",
    "baseball",
    "basketball",
    "tennis",
    "football",
    "soccer",
    "sustainability",
    "wildlife",
    "electric vehicles",
)
TITLE_CASE_WORD_RE = re.compile(r"\b[A-Z][a-z]+(?:'[a-z]+)?\b")


@dataclass
class ArticleContext:
    relevant_sentences: List[str]
    summary_sentences: List[str] = field(default_factory=list)
    meta_description: str = ""
    text_excerpt: str = ""
    fetch_error: str = ""
    low_confidence: bool = False
    published_at_hint: Optional[datetime] = None

    @property
    def has_relevant_sentences(self) -> bool:
        return bool(self.relevant_sentences)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self._parts: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP_TEXT_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in SKIP_TEXT_TAGS and self._skip_depth > 0:
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
    published_at_hint = _extract_meta_published_at(html)
    text = _extract_text(html)
    boilerplate_markers = _boilerplate_markers_for_url(response.url or url)
    sentences = _extract_candidate_sentences(text, boilerplate_markers)
    relevant_indices = _find_relevant_sentence_indices(sentences, aliases)
    relevant_sentences = [sentences[index] for index in relevant_indices[:3]]
    summary_sentences, summary_scores = _select_summary_sentences(
        sentences,
        relevant_indices,
        aliases,
        boilerplate_markers,
    )
    low_confidence = _is_low_confidence(
        summary_sentences=summary_sentences,
        relevant_sentences=relevant_sentences,
        summary_scores=summary_scores,
        meta_description=meta_description,
    )
    if low_confidence:
        summary_sentences = []
    excerpt_source = " ".join(summary_sentences) if summary_sentences else meta_description or text

    return ArticleContext(
        relevant_sentences=relevant_sentences[:3],
        summary_sentences=summary_sentences[:5],
        meta_description=meta_description,
        text_excerpt=short_text(excerpt_source, 1200),
        low_confidence=low_confidence,
        published_at_hint=published_at_hint,
    )


def _decode_html(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "shift_jis", "euc-jp", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="ignore")


def _extract_meta_description(html: str) -> str:
    candidates = _collect_meta_description_candidates(html)
    if not candidates:
        return ""

    scored_candidates = sorted(
        candidates,
        key=lambda candidate: (_meta_description_score(candidate), len(candidate)),
        reverse=True,
    )
    selected: List[str] = []
    for candidate in scored_candidates:
        if any(candidate.casefold() in existing.casefold() for existing in selected):
            continue
        selected.append(candidate)
        if len(selected) >= 2:
            break
    joined = " ".join(_ensure_terminal_punctuation(candidate) for candidate in selected)
    return normalize_whitespace(joined)


def _extract_meta_published_at(html: str):
    for pattern in META_DATE_PATTERNS:
        match = pattern.search(html)
        if not match:
            continue
        published_at = parse_datetime(unescape(match.group(1)))
        if published_at is not None:
            return published_at
    return None


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def _boilerplate_markers_for_url(url: str) -> List[str]:
    netloc = urlsplit(url).netloc.casefold()
    markers = list(GENERIC_BOILERPLATE_MARKERS)
    for domain, domain_markers in DOMAIN_BOILERPLATE_MARKERS.items():
        if netloc == domain or netloc.endswith("." + domain):
            markers.extend(domain_markers)
    return markers


def _collect_meta_description_candidates(html: str) -> List[str]:
    candidates: List[str] = []
    for pattern in META_DESCRIPTION_PATTERNS:
        for match in pattern.finditer(html):
            _append_unique_candidate(candidates, _clean_meta_candidate(match.group(1)))

    for script_body in JSON_LD_SCRIPT_RE.findall(html):
        for candidate in _extract_structured_summaries(script_body):
            _append_unique_candidate(candidates, _clean_meta_candidate(candidate))

    return candidates


def _extract_structured_summaries(script_body: str) -> List[str]:
    try:
        payload = json.loads(unescape(script_body))
    except json.JSONDecodeError:
        return []

    candidates: List[str] = []
    for value in _walk_structured_values(payload):
        if not isinstance(value, dict):
            continue
        for key in STRUCTURED_SUMMARY_KEYS:
            _append_unique_candidate(candidates, _clean_meta_candidate(value.get(key, "")))
    return candidates


def _walk_structured_values(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_structured_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_structured_values(child)


def _append_unique_candidate(candidates: List[str], candidate: str) -> None:
    if not candidate:
        return
    key = candidate.casefold()
    if any(existing.casefold() == key for existing in candidates):
        return
    candidates.append(candidate)


def _clean_meta_candidate(value: str) -> str:
    cleaned = normalize_whitespace(unescape(value))
    if not cleaned:
        return ""
    if cleaned[-1] not in ".!?。！？":
        tokens = cleaned.split()
        if tokens and len(tokens[-1]) <= 3:
            cleaned = " ".join(tokens[:-1]).rstrip(" ,;:-")
    return normalize_whitespace(cleaned)


def _meta_description_score(candidate: str) -> int:
    lowered = candidate.casefold()
    score = 0
    if 40 <= len(candidate) <= 220:
        score += 3
    elif len(candidate) >= 24:
        score += 1
    if candidate[-1] in ".!?。！？":
        score += 2
    if " -- " in candidate or ": " in candidate:
        score += 1
    if sum(1 for marker in GENERIC_BOILERPLATE_MARKERS if marker.casefold() in lowered):
        score -= 10
    if _looks_like_headline_blob(candidate):
        score -= 4
    return score


def _ensure_terminal_punctuation(value: str) -> str:
    if not value:
        return ""
    if value[-1] in ".!?。！？":
        return value
    return value + "."


def _extract_candidate_sentences(text: str, boilerplate_markers: List[str]) -> List[str]:
    if not text:
        return []
    sentences = [normalize_whitespace(part) for part in SENTENCE_SPLIT_RE.split(text)]
    candidates = []
    for sentence in sentences:
        sentence = _trim_trailing_boilerplate(sentence)
        if len(sentence) < 12:
            continue
        if sentence.count("|") >= 2:
            continue
        if _is_noise_sentence(sentence, boilerplate_markers):
            continue
        candidates.append(sentence)
    return candidates


def _find_relevant_sentence_indices(sentences: List[str], aliases: List[str]) -> List[int]:
    relevant_indices = []
    for index, sentence in enumerate(sentences):
        if find_matching_aliases(sentence, aliases):
            relevant_indices.append(index)
    return relevant_indices


def _select_summary_sentences(
    sentences: List[str],
    relevant_indices: List[int],
    aliases: List[str],
    boilerplate_markers: List[str],
    max_sentences: int = 5,
) -> tuple[List[str], List[int]]:
    if not sentences:
        return [], []

    pool = _summary_candidate_pool(sentences, relevant_indices)
    scored_candidates = []
    for index in pool:
        sentence = sentences[index]
        score = _sentence_score(
            sentence=sentence,
            index=index,
            relevant_indices=relevant_indices,
            aliases=aliases,
            boilerplate_markers=boilerplate_markers,
        )
        if score <= 0:
            continue
        distance = _distance_to_relevant(index, relevant_indices)
        alias_count = len(find_matching_aliases(sentence, aliases))
        scored_candidates.append((score, alias_count, -distance, index))

    if not scored_candidates and relevant_indices:
        fallback = [
            (1, len(find_matching_aliases(sentences[index], aliases)), 0, index)
            for index in relevant_indices[:max_sentences]
        ]
        scored_candidates.extend(fallback)

    top_candidates = sorted(scored_candidates, reverse=True)[:max_sentences]
    selected_indices = sorted(item[3] for item in top_candidates)
    selected_scores = [item[0] for item in sorted(top_candidates, key=lambda item: item[3])]
    return [sentences[index] for index in selected_indices], selected_scores


def _summary_candidate_pool(sentences: List[str], relevant_indices: List[int]) -> List[int]:
    if not relevant_indices:
        return list(range(min(len(sentences), 6)))
    selected = set()
    for index in relevant_indices:
        for candidate_index in range(max(0, index - 2), min(len(sentences), index + 3)):
            selected.add(candidate_index)
    return sorted(selected)


def _sentence_score(
    sentence: str,
    index: int,
    relevant_indices: List[int],
    aliases: List[str],
    boilerplate_markers: List[str],
) -> int:
    score = 0
    alias_matches = find_matching_aliases(sentence, aliases)
    if alias_matches:
        score += 6

    distance = _distance_to_relevant(index, relevant_indices)
    if distance == 0:
        score += 4
    elif distance == 1:
        score += 3
    elif distance == 2:
        score += 2
    elif distance > 2:
        score -= 1

    if 35 <= len(sentence) <= 260:
        score += 1
    if re.search(
        r"\b(said|announced|ordered|ruled|plans?|expects?|told|reported|filed|acquired|reinstated)\b",
        sentence.casefold(),
    ):
        score += 1

    score -= _noise_penalty(sentence, boilerplate_markers)
    return score


def _distance_to_relevant(index: int, relevant_indices: List[int]) -> int:
    if not relevant_indices:
        return 99
    return min(abs(index - relevant_index) for relevant_index in relevant_indices)


def _noise_penalty(sentence: str, boilerplate_markers: List[str]) -> int:
    lowered = sentence.casefold()
    marker_hits = sum(1 for marker in boilerplate_markers if marker.casefold() in lowered)
    social_hits = sum(1 for marker in SOCIAL_MARKERS if marker in lowered)
    category_hits = sum(1 for marker in CATEGORY_MARKERS if marker in lowered)

    penalty = marker_hits * 4
    if social_hits >= 2:
        penalty += social_hits * 2
    if category_hits >= 4:
        penalty += 3 + category_hits
    if len(sentence) > 260 and (marker_hits or category_hits >= 3):
        penalty += 2
    return penalty


def _is_noise_sentence(sentence: str, boilerplate_markers: List[str]) -> bool:
    lowered = sentence.casefold()
    marker_hits = sum(1 for marker in boilerplate_markers if marker.casefold() in lowered)
    social_hits = sum(1 for marker in SOCIAL_MARKERS if marker in lowered)
    category_hits = sum(1 for marker in CATEGORY_MARKERS if marker in lowered)

    if _looks_like_author_bio(sentence):
        return True
    if _looks_like_headline_blob(sentence):
        return True
    if marker_hits >= 2:
        return True
    if social_hits >= 3:
        return True
    if category_hits >= 6:
        return True
    if category_hits >= 4 and (social_hits >= 1 or marker_hits >= 1):
        return True
    if len(sentence) > 220 and category_hits >= 4:
        return True
    return False


def _trim_trailing_boilerplate(sentence: str) -> str:
    trimmed = normalize_whitespace(sentence)
    if not trimmed:
        return ""

    lowered = trimmed.casefold()
    cut_positions = []
    for marker in TRAILING_BOILERPLATE_MARKERS:
        position = lowered.find(marker.casefold())
        if position > 0:
            cut_positions.append(position)
        elif position == 0:
            return ""
    for token in TRAILING_BOILERPLATE_TOKENS:
        position = trimmed.find(token)
        if position > 0:
            cut_positions.append(position)
        elif position == 0:
            return ""

    if cut_positions:
        trimmed = trimmed[: min(cut_positions)]
    return normalize_whitespace(trimmed.rstrip(" -|:;,.!"))


def _looks_like_author_bio(sentence: str) -> bool:
    lowered = sentence.casefold()
    bio_hits = sum(1 for marker in AUTHOR_BIO_MARKERS if marker in lowered)
    if bio_hits == 0:
        return False
    if "is a " in lowered or "is an " in lowered:
        return True
    if "host of" in lowered or "director of" in lowered:
        return True
    return bio_hits >= 2


def _looks_like_headline_blob(sentence: str) -> bool:
    lowered = sentence.casefold()
    if len(sentence) < 80:
        return False
    words = sentence.split()
    title_case_ratio = 0.0
    if words:
        title_case_ratio = len(TITLE_CASE_WORD_RE.findall(sentence)) / len(words)
    if any(lowered.startswith(marker + " ") for marker in CATEGORY_MARKERS):
        return True
    if not re.search(r"[.!?。！？]", sentence) and len(sentence) >= 110 and title_case_ratio >= 0.33:
        return True
    if sentence[-1:].isupper() and title_case_ratio >= 0.25:
        return True
    if len(words) >= 12 and title_case_ratio >= 0.45:
        return True
    return False


def _is_low_confidence(
    summary_sentences: List[str],
    relevant_sentences: List[str],
    summary_scores: List[int],
    meta_description: str,
) -> bool:
    if not summary_sentences and not relevant_sentences:
        return True
    if any(_looks_like_headline_blob(sentence) for sentence in summary_sentences + relevant_sentences):
        return True
    if relevant_sentences and summary_scores and max(summary_scores) >= 5:
        return False
    if summary_sentences and len(summary_sentences) >= 2:
        return False
    return not bool(relevant_sentences or meta_description)
