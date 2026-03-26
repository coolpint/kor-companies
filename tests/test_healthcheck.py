import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.kor_companies.healthcheck import build_weekly_health_teams_payload, evaluate_weekly_health

UTC = ZoneInfo("UTC")
KST = ZoneInfo("Asia/Seoul")


class HealthcheckTests(unittest.TestCase):
    def test_evaluate_weekly_health_ok_when_all_slots_are_covered(self):
        checked_at = datetime(2026, 3, 27, 6, 51, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            archive_dir = reports_dir / "archive" / "2026-03"
            archive_dir.mkdir(parents=True, exist_ok=True)

            run_times_kst = [
                datetime(2026, 3, 20, 18, 20, tzinfo=KST),
                datetime(2026, 3, 21, 8, 15, tzinfo=KST),
                datetime(2026, 3, 21, 18, 10, tzinfo=KST),
                datetime(2026, 3, 22, 8, 35, tzinfo=KST),
                datetime(2026, 3, 22, 18, 5, tzinfo=KST),
                datetime(2026, 3, 23, 8, 25, tzinfo=KST),
                datetime(2026, 3, 23, 18, 12, tzinfo=KST),
                datetime(2026, 3, 24, 8, 18, tzinfo=KST),
                datetime(2026, 3, 24, 18, 9, tzinfo=KST),
                datetime(2026, 3, 25, 8, 17, tzinfo=KST),
                datetime(2026, 3, 25, 18, 8, tzinfo=KST),
                datetime(2026, 3, 26, 8, 16, tzinfo=KST),
                datetime(2026, 3, 26, 18, 11, tzinfo=KST),
                datetime(2026, 3, 27, 8, 14, tzinfo=KST),
            ]
            for index, run_time in enumerate(run_times_kst, start=1):
                payload = {
                    "run_at": run_time.astimezone(UTC).isoformat(),
                    "summary": {
                        "source_count": 31,
                        "success_count": 30,
                        "failed_count": 1 if index == 3 else 0,
                        "matched_count": 1,
                        "new_count": 0,
                    },
                    "new_articles": [],
                    "matched_articles": [],
                    "source_runs": [],
                }
                path = archive_dir / f"monitor-{run_time.strftime('%Y%m%d-%H%M%S')}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")

            summary = evaluate_weekly_health(reports_dir, checked_at=checked_at)

            self.assertEqual(summary.status, "ok")
            self.assertEqual(summary.expected_slots, 14)
            self.assertEqual(summary.covered_slots, 14)
            self.assertEqual(summary.severe_failure_runs, 0)
            self.assertEqual(summary.runs_with_failures, 1)

    def test_evaluate_weekly_health_warns_when_slot_is_missing(self):
        checked_at = datetime(2026, 3, 27, 6, 51, tzinfo=UTC)
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = Path(temp_dir) / "reports"
            archive_dir = reports_dir / "archive" / "2026-03"
            archive_dir.mkdir(parents=True, exist_ok=True)

            run_times_kst = [
                datetime(2026, 3, 20, 18, 20, tzinfo=KST),
                datetime(2026, 3, 21, 8, 15, tzinfo=KST),
                datetime(2026, 3, 21, 18, 10, tzinfo=KST),
                datetime(2026, 3, 22, 8, 35, tzinfo=KST),
                datetime(2026, 3, 22, 18, 5, tzinfo=KST),
                datetime(2026, 3, 23, 8, 25, tzinfo=KST),
                datetime(2026, 3, 23, 18, 12, tzinfo=KST),
                datetime(2026, 3, 24, 8, 18, tzinfo=KST),
                datetime(2026, 3, 25, 8, 17, tzinfo=KST),
                datetime(2026, 3, 25, 18, 8, tzinfo=KST),
                datetime(2026, 3, 26, 8, 16, tzinfo=KST),
                datetime(2026, 3, 26, 18, 11, tzinfo=KST),
                datetime(2026, 3, 27, 8, 14, tzinfo=KST),
            ]
            for run_time in run_times_kst:
                payload = {
                    "run_at": run_time.astimezone(UTC).isoformat(),
                    "summary": {
                        "source_count": 31,
                        "success_count": 31,
                        "failed_count": 0,
                        "matched_count": 0,
                        "new_count": 0,
                    },
                    "new_articles": [],
                    "matched_articles": [],
                    "source_runs": [],
                }
                path = archive_dir / f"monitor-{run_time.strftime('%Y%m%d-%H%M%S')}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")

            summary = evaluate_weekly_health(reports_dir, checked_at=checked_at)

            self.assertEqual(summary.status, "warning")
            self.assertEqual(summary.expected_slots, 14)
            self.assertEqual(summary.covered_slots, 13)
            self.assertEqual(len(summary.missed_slots), 1)

    def test_build_weekly_health_teams_payload_contains_status(self):
        checked_at = datetime(2026, 3, 27, 6, 51, tzinfo=UTC)
        summary = evaluate_weekly_health(Path("/tmp/not-used"), checked_at=checked_at)
        payload = build_weekly_health_teams_payload(summary)

        self.assertIn("@type", payload)
        self.assertIn("title", payload)
        self.assertIn("sections", payload)


if __name__ == "__main__":
    unittest.main()
