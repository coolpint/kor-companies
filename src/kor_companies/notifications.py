from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from .models import MatchedArticle, SourceRunResult
from .utils import short_text

MAX_MESSAGE_LENGTH = 3800
KST = ZoneInfo("Asia/Seoul")


class TelegramConfigError(RuntimeError):
    """Raised when Telegram environment variables are inconsistent."""


class TelegramSendError(RuntimeError):
    """Raised when Telegram API delivery fails."""


@dataclass
class TelegramConfig:
    bot_token: str
    chat_id: str
    message_thread_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> Optional["TelegramConfig"]:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        message_thread_id = os.getenv("TELEGRAM_MESSAGE_THREAD_ID", "").strip() or None

        if not bot_token and not chat_id:
            return None
        if not bot_token or not chat_id:
            raise TelegramConfigError(
                "Both TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set together."
            )
        return cls(
            bot_token=bot_token,
            chat_id=chat_id,
            message_thread_id=message_thread_id,
        )


def build_run_summary_messages(
    run_at_label: str,
    matched_articles: List[MatchedArticle],
    new_articles: List[MatchedArticle],
    source_runs: List[SourceRunResult],
) -> List[str]:
    headline_lines = [
        "해외 언론 한국 기업 모니터링",
        f"실행: {run_at_label}",
        (
            "소스: "
            f"{len(source_runs)}개 "
            f"(성공 {sum(1 for item in source_runs if item.success)} / "
            f"실패 {sum(1 for item in source_runs if not item.success)})"
        ),
        f"매칭 기사: {len(matched_articles)}건",
        f"신규 기사: {len(new_articles)}건",
    ]
    if not new_articles:
        headline_lines.append("신규로 감지된 기사가 없다.")

    failed_sources = [item for item in source_runs if not item.success]
    if failed_sources:
        headline_lines.append("실패 소스:")
        for item in failed_sources[:8]:
            headline_lines.append(f"- {item.source_name}: {item.error}")

    messages = ["\n".join(headline_lines)]
    if not new_articles:
        return messages

    chunks: List[str] = []
    current = ""
    for index, article in enumerate(new_articles[:12], start=1):
        published = (
            article.published_at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S %Z")
            if article.published_at
            else "발행시각 없음"
        )
        block = "\n".join(
            [
                f"{index}. {article.title}",
                f"회사: {', '.join(article.matched_companies)}",
                f"국가/매체: {article.country_name_ko} / {article.source_name}",
                f"발행: {published}",
                f"링크: {article.link}",
                f"요약: {short_text(article.summary or '요약 없음', 200)}",
            ]
        )
        candidate = block if not current else f"{current}\n\n{block}"
        if len(candidate) > MAX_MESSAGE_LENGTH and current:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)

    if len(new_articles) > 12:
        chunks.append(f"추가 기사 {len(new_articles) - 12}건은 메시지에서만 생략됐다.")

    return messages + chunks


def send_telegram_messages(config: TelegramConfig, messages: List[str], timeout: int = 20) -> int:
    sent_count = 0
    for message in messages:
        payload = {
            "chat_id": config.chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        }
        if config.message_thread_id:
            payload["message_thread_id"] = config.message_thread_id

        body = urlencode(payload).encode("utf-8")
        request = Request(
            f"https://api.telegram.org/bot{config.bot_token}/sendMessage",
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise TelegramSendError(f"Telegram HTTP {exc.code}") from exc
        except URLError as exc:
            raise TelegramSendError(f"Telegram URL error: {exc.reason}") from exc
        except OSError as exc:
            raise TelegramSendError(f"Telegram I/O error: {exc}") from exc

        if not result.get("ok"):
            raise TelegramSendError(f"Telegram API error: {result}")
        sent_count += 1
    return sent_count
