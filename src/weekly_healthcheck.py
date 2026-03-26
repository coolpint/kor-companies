from __future__ import annotations

import argparse
from pathlib import Path

from .kor_companies.healthcheck import (
    build_weekly_health_teams_payload,
    evaluate_weekly_health,
    write_weekly_health_reports,
)
from .kor_companies.teams import TeamsConfigError, TeamsSendError, TeamsWebhookConfig, send_teams_payload


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
        teams_config = TeamsWebhookConfig.from_env()
        if teams_config is None:
            print("teams=skipped")
        else:
            payload = build_weekly_health_teams_payload(summary)
            send_teams_payload(teams_config, payload)
            print("teams=sent")
    except (TeamsConfigError, TeamsSendError) as exc:
        print(f"teams=failed error={exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
