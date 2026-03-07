from __future__ import annotations

import argparse
from pathlib import Path
from zoneinfo import ZoneInfo

from .kor_companies.notifications import (
    TelegramConfig,
    TelegramConfigError,
    TelegramSendError,
    build_run_summary_messages,
    send_telegram_messages,
)
from .kor_companies.pipeline import run_monitor

KST = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor Korean companies in foreign news feeds.")
    parser.add_argument("--config-dir", default="config", help="Directory containing JSON config files.")
    parser.add_argument("--output-dir", default="reports", help="Directory for generated reports.")
    parser.add_argument(
        "--state-path",
        default="data/state/state.json",
        help="JSON file used to persist seen articles.",
    )
    parser.add_argument(
        "--since-hours",
        default=36,
        type=int,
        help="Only consider feed items newer than this many hours when a publish date exists.",
    )
    parser.add_argument(
        "--max-items-per-feed",
        default=80,
        type=int,
        help="Maximum number of feed entries to inspect from each source.",
    )
    parser.add_argument(
        "--countries",
        nargs="*",
        help="Optional list of country codes to run, for example US JP VN.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_monitor(
        config_dir=Path(args.config_dir),
        output_dir=Path(args.output_dir),
        state_path=Path(args.state_path),
        since_hours=args.since_hours,
        max_items_per_feed=args.max_items_per_feed,
        country_codes=args.countries,
    )
    success_count = sum(1 for item in summary.source_runs if item.success)
    failure_count = sum(1 for item in summary.source_runs if not item.success)
    print(f"sources={len(summary.source_runs)} success={success_count} failed={failure_count}")
    print(f"matched={len(summary.matched_articles)} new={len(summary.new_articles)}")
    print(f"report={summary.report_paths['latest_md']}")
    try:
        telegram_config = TelegramConfig.from_env()
        if telegram_config is None:
            print("telegram=skipped")
        else:
            run_at_label = summary.run_at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S %Z")
            messages = build_run_summary_messages(
                run_at_label=run_at_label,
                matched_articles=summary.matched_articles,
                new_articles=summary.new_articles,
                source_runs=summary.source_runs,
            )
            sent_count = send_telegram_messages(telegram_config, messages)
            print(f"telegram=sent messages={sent_count}")
    except (TelegramConfigError, TelegramSendError) as exc:
        print(f"telegram=failed error={exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
