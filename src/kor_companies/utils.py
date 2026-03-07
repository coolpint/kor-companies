from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from typing import Iterable, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "at_", "cmpid", "ocid")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def strip_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return normalize_whitespace(unescape(without_tags))


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query_items = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.startswith(TRACKING_QUERY_PREFIXES)
    ]
    normalized_path = parts.path.rstrip("/") or "/"
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            normalized_path,
            urlencode(query_items),
            "",
        )
    )


def isoformat_or_none(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def short_text(value: str, max_length: int = 220) -> str:
    cleaned = normalize_whitespace(value)
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "…"


def sha1_digest(values: Iterable[str]) -> str:
    digest = hashlib.sha1()
    for value in values:
        digest.update((value or "").encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()

