from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class TeamsConfigError(RuntimeError):
    """Raised when Teams webhook configuration is invalid."""


class TeamsSendError(RuntimeError):
    """Raised when a Teams webhook delivery fails."""


@dataclass
class TeamsWebhookConfig:
    webhook_url: str

    @classmethod
    def from_env(cls) -> Optional["TeamsWebhookConfig"]:
        webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
        if not webhook_url:
            return None
        if not webhook_url.startswith("https://"):
            raise TeamsConfigError("TEAMS_WEBHOOK_URL must be an https URL.")
        return cls(webhook_url=webhook_url)


def send_teams_payload(config: TeamsWebhookConfig, payload: Dict, timeout: int = 20) -> None:
    request = Request(
        config.webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
    except HTTPError as exc:
        raise TeamsSendError(f"Teams HTTP {exc.code}") from exc
    except URLError as exc:
        raise TeamsSendError(f"Teams URL error: {exc.reason}") from exc
    except OSError as exc:
        raise TeamsSendError(f"Teams I/O error: {exc}") from exc
