from __future__ import annotations

import argparse
from pathlib import Path

from .kor_companies.healthcheck import (
    build_weekly_health_telegram_messages,
    evaluate_weekly_health,
    write_weekly_health_reports,
)
from .kor_companies.notifications import (
    TelegramConfig,
    TelegramConfigError,
    TelegramSendError,
    send_telegram_messages,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run weekly health checks for kor-companies.")
    parser.add_argument("--output-dir", default="reports", help="Directory containing monitoring reports.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = evaluate_weekly_health(output_dir=Path(args.output_dir))
    report_paths = write_weekly_health_reports(Path(args.output_dir), summary)
    print(
        f"status={summary.status} runs={summary.total_runs} slots={summary.covered_slots}/{summary.expected_slots}"
    )
    print(f"report={report_paths['latest_md']}")

    try:
        telegram_config = TelegramConfig.from_env()
        if telegram_config is None:
            print("telegram=skipped")
        else:
            messages = build_weekly_health_telegram_messages(summary)
            sent_count = send_telegram_messages(telegram_config, messages)
            print(f"telegram=sent messages={sent_count}")
    except (TelegramConfigError, TelegramSendError) as exc:
        print(f"telegram=failed error={exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
