from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Dict, List
from zoneinfo import ZoneInfo

from .utils import normalize_whitespace

KST = ZoneInfo("Asia/Seoul")
UTC = ZoneInfo("UTC")
SCHEDULE_HOURS_KST = (8, 18)
SLOT_TOLERANCE = timedelta(hours=3)


@dataclass
class RunSnapshot:
    run_at: datetime
    source_count: int
    success_count: int
    failed_count: int
    matched_count: int
    new_count: int
    path: str


@dataclass
class WeeklyHealthSummary:
    status: str
    checked_at: datetime
    period_start: datetime
    period_end: datetime
    total_runs: int
    expected_slots: int
    covered_slots: int
    missed_slots: List[str]
    latest_run_at: datetime | None
    runs_with_failures: int
    severe_failure_runs: int
    max_failed_sources: int
    matched_articles: int
    new_articles: int
    notes: List[str]

    @property
    def status_label_ko(self) -> str:
        return "정상 작동중" if self.status == "ok" else "점검 필요"


def evaluate_weekly_health(
    output_dir: Path,
    checked_at: datetime | None = None,
) -> WeeklyHealthSummary:
    checked_at = checked_at or datetime.now(UTC)
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=UTC)

    period_end = checked_at
    period_start = checked_at - timedelta(days=7)
    runs = _load_run_snapshots(output_dir, period_start, period_end)
    expected_slots = _expected_slots(period_start, period_end)
    covered_slots = _covered_slots(expected_slots, runs)
    missed_slots = [slot.astimezone(KST).strftime("%Y-%m-%d %H:%M KST") for slot in expected_slots if slot not in covered_slots]
    latest_run_at = max((item.run_at for item in runs), default=None)
    runs_with_failures = sum(1 for item in runs if item.failed_count > 0)
    severe_failure_runs = sum(
        1
        for item in runs
        if item.success_count == 0
        or item.failed_count >= max(5, item.source_count // 4)
    )
    max_failed_sources = max((item.failed_count for item in runs), default=0)
    matched_articles = sum(item.matched_count for item in runs)
    new_articles = sum(item.new_count for item in runs)

    notes: List[str] = []
    if not runs:
        notes.append("지난 7일 동안 실행 로그가 없다.")
    if latest_run_at is None or period_end - latest_run_at > timedelta(hours=24):
        notes.append("최근 24시간 안에 실행된 기록이 없다.")
    if missed_slots:
        notes.append(f"예정된 실행 슬롯 {len(expected_slots)}개 중 {len(missed_slots)}개가 비었다.")
    if severe_failure_runs:
        notes.append(f"소스 실패가 크게 발생한 실행이 {severe_failure_runs}회 있었다.")
    elif runs_with_failures:
        notes.append(f"일부 소스 실패가 있었지만 치명적인 수준은 아니었다. ({runs_with_failures}회)")
    if not notes:
        notes.append("지난 7일 동안 예정된 실행이 모두 확인됐고 치명적인 수집 실패도 없었다.")

    status = "ok"
    if (
        not runs
        or latest_run_at is None
        or period_end - latest_run_at > timedelta(hours=24)
        or bool(missed_slots)
        or severe_failure_runs > 0
    ):
        status = "warning"

    return WeeklyHealthSummary(
        status=status,
        checked_at=checked_at,
        period_start=period_start,
        period_end=period_end,
        total_runs=len(runs),
        expected_slots=len(expected_slots),
        covered_slots=len(covered_slots),
        missed_slots=missed_slots,
        latest_run_at=latest_run_at,
        runs_with_failures=runs_with_failures,
        severe_failure_runs=severe_failure_runs,
        max_failed_sources=max_failed_sources,
        matched_articles=matched_articles,
        new_articles=new_articles,
        notes=notes,
    )


def write_weekly_health_reports(output_dir: Path, summary: WeeklyHealthSummary) -> Dict[str, Path]:
    health_dir = output_dir / "health"
    archive_dir = health_dir / "archive" / summary.checked_at.astimezone(KST).strftime("%Y-%m")
    health_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = summary.checked_at.astimezone(KST).strftime("%Y%m%d-%H%M%S")
    latest_md = health_dir / "latest-weekly.md"
    latest_json = health_dir / "latest-weekly.json"
    archive_md = archive_dir / f"health-{timestamp}.md"
    archive_json = archive_dir / f"health-{timestamp}.json"

    markdown = build_weekly_health_markdown(summary)
    payload = {
        "status": summary.status,
        "checked_at": summary.checked_at.astimezone(UTC).isoformat(),
        "period_start": summary.period_start.astimezone(UTC).isoformat(),
        "period_end": summary.period_end.astimezone(UTC).isoformat(),
        "total_runs": summary.total_runs,
        "expected_slots": summary.expected_slots,
        "covered_slots": summary.covered_slots,
        "missed_slots": summary.missed_slots,
        "latest_run_at": summary.latest_run_at.astimezone(UTC).isoformat() if summary.latest_run_at else None,
        "runs_with_failures": summary.runs_with_failures,
        "severe_failure_runs": summary.severe_failure_runs,
        "max_failed_sources": summary.max_failed_sources,
        "matched_articles": summary.matched_articles,
        "new_articles": summary.new_articles,
        "notes": summary.notes,
    }

    latest_md.write_text(markdown, encoding="utf-8")
    latest_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    archive_md.write_text(markdown, encoding="utf-8")
    archive_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "latest_md": latest_md,
        "latest_json": latest_json,
        "archive_md": archive_md,
        "archive_json": archive_json,
    }


def build_weekly_health_markdown(summary: WeeklyHealthSummary) -> str:
    latest_run_label = (
        summary.latest_run_at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")
        if summary.latest_run_at
        else "없음"
    )
    lines = [
        "# 주간 모니터링 점검",
        "",
        f"- 점검 시각: {summary.checked_at.astimezone(KST).strftime('%Y-%m-%d %H:%M:%S KST')}",
        (
            "- 점검 기간: "
            f"{summary.period_start.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')} ~ "
            f"{summary.period_end.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')}"
        ),
        f"- 상태: {summary.status_label_ko}",
        f"- 실행 로그: {summary.total_runs}건",
        f"- 예정 슬롯 커버: {summary.covered_slots}/{summary.expected_slots}",
        f"- 최근 실행: {latest_run_label}",
        f"- 소스 실패 포함 실행: {summary.runs_with_failures}건",
        f"- 최대 실패 소스 수: {summary.max_failed_sources}개",
        f"- 기간 중 매칭 기사: {summary.matched_articles}건",
        f"- 기간 중 신규 기사: {summary.new_articles}건",
        "",
        "## 점검 메모",
        "",
    ]
    for note in summary.notes:
        lines.append(f"- {note}")

    if summary.missed_slots:
        lines.extend(["", "## 누락된 예정 슬롯", ""])
        for item in summary.missed_slots:
            lines.append(f"- {item}")

    return "\n".join(lines).strip() + "\n"


def build_weekly_health_teams_payload(summary: WeeklyHealthSummary) -> Dict:
    theme_color = "2EB886" if summary.status == "ok" else "D83B01"
    facts = [
        {"name": "상태", "value": summary.status_label_ko},
        {"name": "점검 기간", "value": _period_label(summary.period_start, summary.period_end)},
        {"name": "실행 로그", "value": f"{summary.total_runs}건"},
        {"name": "예정 슬롯 커버", "value": f"{summary.covered_slots}/{summary.expected_slots}"},
        {
            "name": "최근 실행",
            "value": (
                summary.latest_run_at.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S KST")
                if summary.latest_run_at
                else "없음"
            ),
        },
        {"name": "소스 실패 포함 실행", "value": f"{summary.runs_with_failures}건"},
        {"name": "최대 실패 소스 수", "value": f"{summary.max_failed_sources}개"},
        {"name": "기간 중 신규 기사", "value": f"{summary.new_articles}건"},
    ]
    note_lines = [f"- {normalize_whitespace(note)}" for note in summary.notes]
    if summary.missed_slots:
        note_lines.append("")
        note_lines.append("누락된 예정 슬롯:")
        note_lines.extend(f"- {item}" for item in summary.missed_slots[:6])

    return {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"{summary.status_label_ko}: kor-companies 주간 점검",
        "themeColor": theme_color,
        "title": f"{summary.status_label_ko}: kor-companies 주간 점검",
        "sections": [
            {
                "facts": facts,
                "text": "<br>".join(note_lines),
            }
        ],
    }


def _period_label(period_start: datetime, period_end: datetime) -> str:
    return (
        f"{period_start.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')} ~ "
        f"{period_end.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')}"
    )


def _load_run_snapshots(output_dir: Path, period_start: datetime, period_end: datetime) -> List[RunSnapshot]:
    archive_root = output_dir / "archive"
    if not archive_root.exists():
        return []

    runs: List[RunSnapshot] = []
    for path in sorted(archive_root.glob("*/monitor-*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        run_at = datetime.fromisoformat(payload["run_at"])
        if run_at.tzinfo is None:
            run_at = run_at.replace(tzinfo=UTC)
        if run_at < period_start or run_at > period_end:
            continue
        summary = payload["summary"]
        runs.append(
            RunSnapshot(
                run_at=run_at,
                source_count=summary["source_count"],
                success_count=summary["success_count"],
                failed_count=summary["failed_count"],
                matched_count=summary["matched_count"],
                new_count=summary["new_count"],
                path=str(path),
            )
        )
    return runs


def _expected_slots(period_start: datetime, period_end: datetime) -> List[datetime]:
    slots: List[datetime] = []
    start_kst = period_start.astimezone(KST)
    end_kst = period_end.astimezone(KST)
    current_date = start_kst.date()
    while current_date <= end_kst.date():
        for hour in SCHEDULE_HOURS_KST:
            slot = datetime.combine(current_date, time(hour=hour, tzinfo=KST))
            slot_utc = slot.astimezone(UTC)
            if period_start <= slot_utc and slot_utc + SLOT_TOLERANCE <= period_end:
                slots.append(slot.astimezone(UTC))
        current_date += timedelta(days=1)
    return slots


def _covered_slots(expected_slots: List[datetime], runs: List[RunSnapshot]) -> List[datetime]:
    covered: List[datetime] = []
    for slot in expected_slots:
        if any(slot <= run.run_at <= slot + SLOT_TOLERANCE for run in runs):
            covered.append(slot)
    return covered
