from __future__ import annotations

import re
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from typing import List
from urllib.parse import urlsplit

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
SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?。！？])")
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
)


@dataclass
class ArticleContext:
    relevant_sentences: List[str]
    summary_sentences: List[str] = field(default_factory=list)
    meta_description: str = ""
    text_excerpt: str = ""
    fetch_error: str = ""
    low_confidence: bool = False

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
    excerpt_source = " ".join(summary_sentences) if summary_sentences else meta_description or text
    low_confidence = _is_low_confidence(
        summary_sentences=summary_sentences,
        relevant_sentences=relevant_sentences,
        summary_scores=summary_scores,
        meta_description=meta_description,
    )

    return ArticleContext(
        relevant_sentences=relevant_sentences[:3],
        summary_sentences=summary_sentences[:5],
        meta_description=meta_description,
        text_excerpt=short_text(excerpt_source, 1200),
        low_confidence=low_confidence,
    )


def _decode_html(payload: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "shift_jis", "euc-jp", "latin-1"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="ignore")


def _extract_meta_description(html: str) -> str:
    for pattern in META_DESCRIPTION_PATTERNS:
        match = pattern.search(html)
        if match:
            return normalize_whitespace(unescape(match.group(1)))
    return ""


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


def _extract_candidate_sentences(text: str, boilerplate_markers: List[str]) -> List[str]:
    if not text:
        return []
    sentences = [normalize_whitespace(part) for part in SENTENCE_SPLIT_RE.split(text)]
    candidates = []
    for sentence in sentences:
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


def _is_low_confidence(
    summary_sentences: List[str],
    relevant_sentences: List[str],
    summary_scores: List[int],
    meta_description: str,
) -> bool:
    if not summary_sentences and not relevant_sentences:
        return True
    if relevant_sentences and summary_scores and max(summary_scores) >= 5:
        return False
    if summary_sentences and len(summary_sentences) >= 2:
        return False
    return not bool(relevant_sentences or meta_description)
