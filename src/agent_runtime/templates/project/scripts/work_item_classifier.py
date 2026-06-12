"""Generate human-readable hierarchy numbers for work items.

Stable file IDs remain UUID/timestamp backed. This classifier assigns the
Owner-facing ordinal view dynamically:

initiative 1 -> taskset 1.1 -> task 1.1.1 -> unit 1.1.1.1
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import backlog_board


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = Path("agents/project/work-items/WORK-ITEM-CLASSIFICATION.json")
DEFAULT_MD = Path("agents/project/work-items/WORK-ITEM-CLASSIFICATION.md")
UNASSIGNED_INITIATIVE = "INIT-UNASSIGNED"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _parse_meta(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return backlog_board.parse_frontmatter(text)


def _title(text: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def _sort_stamp(value: object) -> str:
    text = str(value or "").strip()
    return text if text else "9999-12-31T23:59:59+00:00"


def _md_cell(value: object) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()


def _record(
    *,
    level: str,
    number: str,
    item_id: str,
    title: str,
    path: str,
    parent_id: str = "",
    status: str = "",
) -> dict[str, str]:
    return {
        "key": f"{level}:{item_id}",
        "level": level,
        "number": number,
        "label": f"{level.title()} {number}",
        "id": item_id,
        "title": title,
        "path": path,
        "parent_id": parent_id,
        "status": status,
    }


def _initiative_records(root: Path) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    base = root / "agents" / "project" / "initiatives"
    if not base.is_dir():
        return records
    for path in sorted(base.glob("*.md")):
        meta, body = _parse_meta(path)
        initiative_id = str(meta.get("id") or path.stem).strip()
        if not initiative_id:
            continue
        records[initiative_id] = {
            "id": initiative_id,
            "title": _title(body, initiative_id),
            "path": _rel(root, path),
            "status": str(meta.get("status") or ""),
            "created_at": str(meta.get("created_at") or meta.get("registered_at") or ""),
        }
    return records


def _unit_records(root: Path) -> list[tuple[Path, dict[str, object], str]]:
    base = root / "agents" / "lead_engineer" / "tasks" / "units"
    if not base.is_dir():
        return []
    records: list[tuple[Path, dict[str, object], str]] = []
    for path in sorted(base.glob("**/UNIT-*.md")):
        meta, body = _parse_meta(path)
        if meta:
            records.append((path, meta, body))
    return records


def collect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    tasks = backlog_board.load_tasks(root / "agents" / "lead_engineer" / "tasks")
    task_by_id = {task.task_id: task for task in tasks}
    tasks_by_set: dict[str, list[backlog_board.Task]] = defaultdict(list)
    for task in tasks:
        tasks_by_set[task.task_set_id].append(task)

    initiatives = _initiative_records(root)
    taskset_initiative: dict[str, str] = {}
    findings: list[str] = []

    for task_set_id, grouped_tasks in tasks_by_set.items():
        explicit = sorted({task.initiative_id for task in grouped_tasks if task.initiative_id != "-"})
        if len(explicit) > 1:
            findings.append(f"taskset:multiple-initiatives:{task_set_id}:{','.join(explicit)}")
        initiative_id = explicit[0] if explicit else UNASSIGNED_INITIATIVE
        taskset_initiative[task_set_id] = initiative_id
        if initiative_id != UNASSIGNED_INITIATIVE and initiative_id not in initiatives:
            initiatives[initiative_id] = {
                "id": initiative_id,
                "title": initiative_id,
                "path": "-",
                "status": "referenced",
                "created_at": "",
            }

    if any(value == UNASSIGNED_INITIATIVE for value in taskset_initiative.values()):
        initiatives[UNASSIGNED_INITIATIVE] = {
            "id": UNASSIGNED_INITIATIVE,
            "title": "Unassigned / legacy work",
            "path": "-",
            "status": "synthetic",
            "created_at": "",
        }

    initiative_numbers: dict[str, str] = {}
    real_initiatives = [
        item
        for item in initiatives.values()
        if item["id"] != UNASSIGNED_INITIATIVE
    ]
    real_initiatives.sort(key=lambda item: (_sort_stamp(item["created_at"]), item["id"]))
    for index, item in enumerate(real_initiatives, start=1):
        initiative_numbers[item["id"]] = str(index)
    if UNASSIGNED_INITIATIVE in initiatives:
        initiative_numbers[UNASSIGNED_INITIATIVE] = "0"

    tasksets_by_initiative: dict[str, list[str]] = defaultdict(list)
    for task_set_id, initiative_id in taskset_initiative.items():
        tasksets_by_initiative[initiative_id].append(task_set_id)

    records: list[dict[str, str]] = []
    for initiative_id in sorted(
        initiatives,
        key=lambda value: (0 if value == UNASSIGNED_INITIATIVE else 1, int(initiative_numbers[value])),
    ):
        item = initiatives[initiative_id]
        records.append(
            _record(
                level="initiative",
                number=initiative_numbers[initiative_id],
                item_id=initiative_id,
                title=item["title"],
                path=item["path"],
                status=item["status"],
            )
        )

    taskset_numbers: dict[str, str] = {}
    for initiative_id, task_set_ids in tasksets_by_initiative.items():
        task_set_ids.sort(
            key=lambda task_set_id: (
                backlog_board.task_set_info(task_set_id).order,
                task_set_id,
            )
        )
        for index, task_set_id in enumerate(task_set_ids, start=1):
            number = f"{initiative_numbers[initiative_id]}.{index}"
            taskset_numbers[task_set_id] = number
            info = backlog_board.task_set_info(task_set_id)
            records.append(
                _record(
                    level="taskset",
                    number=number,
                    item_id=task_set_id,
                    title=info.display_name,
                    path="BACKLOG-BOARD.md",
                    parent_id=initiative_id,
                    status="active" if any(not backlog_board.is_done(task) for task in tasks_by_set[task_set_id]) else "complete",
                )
            )

    task_numbers: dict[str, str] = {}
    for task_set_id, grouped_tasks in tasks_by_set.items():
        grouped_tasks.sort(key=lambda task: (_sort_stamp(task.registered_at), task.task_id))
        for index, task in enumerate(grouped_tasks, start=1):
            number = f"{taskset_numbers[task.task_set_id]}.{index}"
            task_numbers[task.task_id] = number
            records.append(
                _record(
                    level="task",
                    number=number,
                    item_id=task.task_id,
                    title=task.goal or task.task_id,
                    path=_rel(root, task.path),
                    parent_id=task.task_set_id,
                    status=task.status,
                )
            )

    units_by_task: dict[str, list[tuple[Path, dict[str, object], str]]] = defaultdict(list)
    for path, meta, body in _unit_records(root):
        task_id = str(meta.get("task_id") or path.parent.name).strip()
        if task_id not in task_by_id:
            findings.append(f"unit:orphan-task:{_rel(root, path)}:{task_id}")
            continue
        units_by_task[task_id].append((path, meta, body))

    for task_id, units in units_by_task.items():
        units.sort(key=lambda item: (str(item[1].get("unit_id") or item[0].stem), _rel(root, item[0])))
        for index, (path, meta, body) in enumerate(units, start=1):
            unit_id = str(meta.get("unit_id") or path.stem).strip()
            records.append(
                _record(
                    level="unit",
                    number=f"{task_numbers[task_id]}.{index}",
                    item_id=unit_id,
                    title=_title(body, unit_id),
                    path=_rel(root, path),
                    parent_id=task_id,
                    status=str(meta.get("status") or ""),
                )
            )

    records.sort(key=lambda row: [int(part) for part in row["number"].split(".")])
    return {
        "schema": "agent-runtime-work-item-classification/v1",
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "record_count": len(records),
        "finding_count": len(findings),
        "findings": findings,
        "records": records,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    records = list(payload["records"])
    counts = defaultdict(int)
    for row in records:
        counts[row["level"]] += 1
    status = "watch" if payload["findings"] else "pass"
    lines = [
        "---",
        "type: work_item_classification",
        "id: WORK-ITEM-CLASSIFICATION-agent-runtime",
        "audience: owner",
        f"status: {status}",
        f"signal: {status}",
        "score: 95",
        "priority: High",
        "tags: [work-items, hierarchy, numbering, generated-index]",
        f"generated_at: {payload['generated_at']}",
        f"record_count: {payload['record_count']}",
        "---",
        "",
        "# Work Item Classification",
        "",
        "## Bottom Line",
        f"- Summary: generated Owner-facing numbers for `{payload['record_count']}` initiative/taskset/task/unit records.",
        "- Result: planners can register stable records without manually reserving human task numbers.",
        "",
        "## Signal",
        "| Metric | State | Evidence |",
        "| --- | --- | --- |",
        f"| Initiatives | pass | `{counts['initiative']}` records |",
        f"| Tasksets | pass | `{counts['taskset']}` records |",
        f"| Tasks | pass | `{counts['task']}` records |",
        f"| Units | pass | `{counts['unit']}` records |",
        f"| Findings | {status} | `{payload['finding_count']}` findings |",
        "",
        "## Insight",
        "- Human-readable numbers are generated views, not canonical identities.",
        "- Canonical identity remains stable IDs plus UUID metadata; this avoids concurrent pane number collisions.",
        "- `0.*` numbers are legacy/unassigned work that predates initiative metadata.",
        "",
        "## Decision",
        "- Decision: use generated `Initiative N -> Taskset N.N -> Task N.N.N -> Unit N.N.N.N` labels for Owner-facing recognition.",
        "- Decision: do not let planners hand-allocate display ordinals during registration.",
        "- Decision: keep `scripts/work_item_classifier.py --check` in governance so stale classification is blocked.",
        "",
        "## Action Board",
        "| Number | Label | Level | ID | Parent | Status | Path | Title |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in records:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["number"],
                    row["label"],
                    row["level"],
                    f"`{row['id']}`",
                    f"`{row['parent_id']}`" if row["parent_id"] else "-",
                    row["status"] or "-",
                    f"`{row['path']}`",
                    _md_cell(row["title"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Risks / Blockers",
            "- Risk: legacy `0.*` work stays readable but should gradually receive `initiative_id` when touched.",
            "- Risk: this generated view prevents human number collisions, but task file creation still needs the planned reservation API for strict concurrent writes.",
            "",
            "## Next Steps",
            "- Run `python scripts/work_item_classifier.py --write` after hierarchy metadata changes.",
            "- Run `python scripts/work_item_classifier.py --check` before closeout or owner-facing handoff.",
            "",
        ]
    )
    return "\n".join(lines)


def _stable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload["schema"],
        "record_count": payload["record_count"],
        "finding_count": payload["finding_count"],
        "findings": payload["findings"],
        "records": payload["records"],
    }


def check(root: Path, json_out: Path, md_out: Path) -> list[str]:
    payload = collect(root)
    findings = list(payload["findings"])
    if payload["record_count"] == 0 and not json_out.exists() and not md_out.exists():
        return findings
    if not json_out.exists():
        findings.append(f"{_rel(root, json_out)}: missing")
    else:
        try:
            existing_json = json.loads(json_out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            findings.append(f"{_rel(root, json_out)}: invalid-json")
        else:
            try:
                existing_stable = _stable_payload(existing_json)
            except KeyError:
                existing_stable = {}
            if existing_stable != _stable_payload(payload):
                findings.append(f"{_rel(root, json_out)}: stale")
    if not md_out.exists():
        findings.append(f"{_rel(root, md_out)}: missing")
    else:
        text = md_out.read_text(encoding="utf-8", errors="replace")
        if "## Bottom Line" not in text or "## Action Board" not in text:
            findings.append(f"{_rel(root, md_out)}: missing-owner-brief-sections")
        missing = [row["key"] for row in payload["records"] if row["id"] not in text]
        if missing:
            findings.append(f"{_rel(root, md_out)}: missing-records:{','.join(missing[:10])}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate/check work item classification numbers")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json-out", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    json_out = args.json_out if args.json_out.is_absolute() else root / args.json_out
    md_out = args.md_out if args.md_out.is_absolute() else root / args.md_out
    if args.write:
        payload = collect(root)
        json_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_out.write_text(render_markdown(payload), encoding="utf-8")
        print(f"wrote={_rel(root, json_out)}")
        print(f"wrote={_rel(root, md_out)}")
    findings = check(root, json_out, md_out)
    status = "fail" if findings else "pass"
    print(f"work-item-classifier: {status}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
