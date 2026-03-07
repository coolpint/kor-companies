from __future__ import annotations

import gzip
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


USER_AGENT = "kor-companies-monitor/0.1 (+https://github.com/coolpint/kor-companies)"


class FetchError(RuntimeError):
    """Raised when a feed cannot be fetched."""


@dataclass
class FetchResponse:
    url: str
    body: bytes
    content_type: str


def fetch_feed(url: str, timeout: int = 20) -> FetchResponse:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
            "Accept-Encoding": "gzip",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            encoding = response.headers.get("Content-Encoding", "").lower()
            content_type = response.headers.get_content_type()
            if encoding == "gzip":
                body = gzip.decompress(body)
            return FetchResponse(url=response.geturl(), body=body, content_type=content_type)
    except HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} for {url}") from exc
    except URLError as exc:
        raise FetchError(f"URL error for {url}: {exc.reason}") from exc
    except OSError as exc:
        raise FetchError(f"I/O error for {url}: {exc}") from exc

