from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from .models import FeedEntry, SourceConfig
from .utils import strip_html

NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "rss": "http://purl.org/rss/1.0/",
}


class FeedParseError(RuntimeError):
    """Raised when the downloaded payload is not a supported feed."""


def _text(element: Optional[ET.Element], path: str, default: str = "") -> str:
    if element is None:
        return default
    child = element.find(path, NAMESPACES)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def parse_datetime(value: str) -> Optional[datetime]:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    normalized = raw.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_feed(source: SourceConfig, payload: bytes) -> List[FeedEntry]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise FeedParseError(f"{source.source_name}: invalid XML") from exc

    tag = _local_name(root.tag)
    if tag == "rss":
        return _parse_rss(source, root)
    if tag == "feed":
        return _parse_atom(source, root)
    if tag == "RDF":
        return _parse_rdf(source, root)
    if tag == "html":
        raise FeedParseError(f"{source.source_name}: HTML returned instead of feed")
    raise FeedParseError(f"{source.source_name}: unsupported feed format {root.tag}")


def _parse_rss(source: SourceConfig, root: ET.Element) -> List[FeedEntry]:
    channel = root.find("channel")
    if channel is None:
        raise FeedParseError(f"{source.source_name}: RSS channel not found")

    entries: List[FeedEntry] = []
    for item in channel.findall("item"):
        title = strip_html(_text(item, "title"))
        link = strip_html(_text(item, "link"))
        summary = strip_html(_text(item, "description") or _text(item, "content:encoded"))
        origin_source_name, origin_source_url = _parse_origin_source(item)
        published_at = parse_datetime(
            _text(item, "pubDate") or _text(item, "dc:date") or _text(item, "published")
        )
        guid = strip_html(_text(item, "guid"))
        if _is_google_news_source(source):
            title = _trim_google_news_title(title, origin_source_name)
            summary = ""
        if not title or not link:
            continue
        entries.append(
            FeedEntry(
                source_id=source.source_id,
                source_name=source.source_name,
                country_code=source.country_code,
                title=title,
                link=link,
                summary=summary,
                published_at=published_at,
                guid=guid,
                origin_source_name=origin_source_name,
                origin_source_url=origin_source_url,
            )
        )
    return entries


def _parse_atom(source: SourceConfig, root: ET.Element) -> List[FeedEntry]:
    entries: List[FeedEntry] = []
    for entry in root.findall("atom:entry", NAMESPACES):
        title = strip_html(_text(entry, "atom:title"))
        summary = strip_html(_text(entry, "atom:summary") or _text(entry, "atom:content"))
        published_at = parse_datetime(
            _text(entry, "atom:published") or _text(entry, "atom:updated")
        )
        guid = strip_html(_text(entry, "atom:id"))

        link = ""
        for link_element in entry.findall("atom:link", NAMESPACES):
            rel = link_element.attrib.get("rel", "alternate")
            href = link_element.attrib.get("href", "").strip()
            if href and rel in ("alternate", ""):
                link = href
                break
        if not title or not link:
            continue
        entries.append(
            FeedEntry(
                source_id=source.source_id,
                source_name=source.source_name,
                country_code=source.country_code,
                title=title,
                link=link,
                summary=summary,
                published_at=published_at,
                guid=guid,
            )
        )
    return entries


def _parse_rdf(source: SourceConfig, root: ET.Element) -> List[FeedEntry]:
    entries: List[FeedEntry] = []
    for item in root.findall("rss:item", NAMESPACES):
        title = strip_html(_text(item, "rss:title"))
        link = strip_html(_text(item, "rss:link"))
        summary = strip_html(_text(item, "rss:description") or _text(item, "content:encoded"))
        origin_source_name, origin_source_url = _parse_origin_source(item)
        published_at = parse_datetime(_text(item, "dc:date"))
        guid = strip_html(_text(item, "dc:identifier"))
        if not title or not link:
            continue
        entries.append(
            FeedEntry(
                source_id=source.source_id,
                source_name=source.source_name,
                country_code=source.country_code,
                title=title,
                link=link,
                summary=summary,
                published_at=published_at,
                guid=guid,
                origin_source_name=origin_source_name,
                origin_source_url=origin_source_url,
            )
        )
    return entries


def _local_name(tag: str) -> str:
    if "}" not in tag:
        return tag
    return tag.rsplit("}", 1)[-1]


def _parse_origin_source(item: ET.Element) -> tuple[str, str]:
    source_element = item.find("source")
    if source_element is None:
        return "", ""
    return (
        strip_html(source_element.text or ""),
        source_element.attrib.get("url", "").strip(),
    )


def _is_google_news_source(source: SourceConfig) -> bool:
    if source.category == "google_news":
        return True
    return urlsplit(source.feed_url).netloc.casefold().endswith("news.google.com")


def _trim_google_news_title(title: str, origin_source_name: str) -> str:
    cleaned_title = strip_html(title)
    cleaned_source = strip_html(origin_source_name)
    if not cleaned_title or not cleaned_source:
        return cleaned_title
    for separator in (" - ", " | ", " — ", " – "):
        suffix = separator + cleaned_source
        if cleaned_title.casefold().endswith(suffix.casefold()):
            return cleaned_title[: -len(suffix)].rstrip()
    return cleaned_title
