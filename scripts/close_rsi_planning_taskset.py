from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASK_IDS = (
    "TASK-AR-234",
    "TASK-AR-235",
    "TASK-AR-236",
    "TASK-AR-237",
    "TASK-AR-238",
    "TASK-AR-239",
    "TASK-AR-241",
    "TASK-AR-242",
    "TASK-AR-244",
    "TASK-AR-245",
)
CLAIM_ID = "CLAIM-20260610-221124-task-ar-234-02c3"
VERIFY_REPORT = "reviews/RSI-PLANNING-TASKSET-VERIFY.json"
TASKSET_ID = "TASKSET-AR-RSI-PLANNING"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _task_path(root: Path, task_id: str) -> Path:
    path = root / "agents" / "lead_engineer" / "tasks" / f"{task_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"missing task file: {path}")
    return path


def _replace_or_insert_frontmatter_field(raw: str, key: str, value: str) -> str:
    pattern = rf"(?m)^{re.escape(key)}:\s*.*$"
    line = f"{key}: {value}"
    if re.search(pattern, raw):
        return re.sub(pattern, line, raw, count=1)
    return re.sub(r"(?m)^---\s*$", f"---\n{line}", raw, count=1)


def close_task_text(raw: str, *, completed_at: str, verify_report: str) -> str:
    verify_report = verify_report.replace("\\", "/")
    raw = _replace_or_insert_frontmatter_field(raw, "status", "completed")
    raw = _replace_or_insert_frontmatter_field(raw, "completed_at", completed_at)
    raw = _replace_or_insert_frontmatter_field(raw, "verification_status", "passed")
    if f"  - {verify_report}" not in raw:
        raw = re.sub(r"(?m)^created:", lambda _: f"  - {verify_report}\ncreated:", raw, count=1)
    section = f"""

## RSI Planning Taskset Closeout ({completed_at})

- Verification report: `{verify_report}`.
- Completion boundary: local RSI planning loop implementation, proposal-only B-mode, UI Planner visibility, guardrails, and C-mode blocking.
- External release, remote publication, dependency install, secret/prod-data, destructive changes, and owner-only decisions remain out of scope.
"""
    if "## RSI Planning Taskset Closeout" not in raw:
        raw = raw.rstrip() + section + "\n"
    return raw


def _load_verify_report(root: Path, report_path: str) -> dict[str, Any]:
    report_path = report_path.replace("\\", "/")
    path = root / report_path
    if not path.exists():
        raise FileNotFoundError(f"verification report is required: {report_path}")
    report = _read_json(path)
    if report.get("status") != "pass":
        raise RuntimeError(f"verification report must have status=pass, got {report.get('status')!r}")
    return report


def _close_claim(root: Path, *, completed_at: str, verify_report: str) -> list[str]:
    changed: list[str] = []
    claim_path = root / "agents" / "runtime" / "task_claims" / f"{CLAIM_ID}.json"
    claim = _read_json(claim_path)
    claim["status"] = "completed"
    claim["phase"] = "taskset-completed"
    claim["progress_pct"] = 100
    claim["step_index"] = 10
    claim["step_total"] = 10
    claim["status_text"] = "TASKSET-AR-RSI-PLANNING completed after verification report passed."
    claim["completed_at"] = completed_at
    claim["updated_at"] = completed_at
    claim["last_heartbeat"] = completed_at
    claim["verification_report"] = verify_report
    _write_json(claim_path, claim)
    changed.append(claim_path.relative_to(root).as_posix())

    handoff_path = root / "agents" / "runtime" / "task_claims" / f"{CLAIM_ID}.handoff.md"
    handoff_path.write_text(
        "\n".join(
            [
                "# Handoff: lead_engineer@rsi-planning-01",
                "",
                f"- claim_id: {CLAIM_ID}",
                "- task_id: TASK-AR-234",
                f"- task_set_id: {TASKSET_ID}",
                "- phase: taskset-completed",
                "- step: 10/10",
                "- progress_pct: 100",
                "- status: completed",
                "- status_text: TASKSET-AR-RSI-PLANNING completed after verification report passed.",
                f"- verification_report: {verify_report}",
                "",
                "## Boundary",
                "",
                "- Local RSI planning loop is complete.",
                "- Owner-only/external/release/destructive actions remain gated and out of scope.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    changed.append(handoff_path.relative_to(root).as_posix())

    log_path = root / "agents" / "runtime" / "task_claims" / f"{CLAIM_ID}.log.md"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n## {completed_at}\n\n"
            "- phase: taskset-completed\n"
            "- progress_pct: 100\n"
            f"- verification_report: `{verify_report}`\n"
            "- closure: RSI planning task-set completed for local implementation and gates.\n"
        )
    changed.append(log_path.relative_to(root).as_posix())
    return changed


def _append_status(root: Path, *, completed_at: str, verify_report: str) -> str:
    status_path = root / "STATUS.md"
    raw = status_path.read_text(encoding="utf-8")
    marker = "TASKSET-AR-RSI-PLANNING final closeout"
    if marker in raw:
        return status_path.relative_to(root).as_posix()
    note = f"""

## 2026-06-10 - TASKSET-AR-RSI-PLANNING final closeout

### Bottom Line

- Summary: task set `TASKSET-AR-RSI-PLANNING` is complete for local bounded RSI planning loop implementation.
- Status: pass; verification report `{verify_report}` passed before closeout.
- Completed at: `{completed_at}`.

### Signal

| Signal | State | Evidence |
| --- | --- | --- |
| Contract/schema | pass | `agents/project/PLANNING-LOOP-CONTRACT.md`, `schemas/planning-proposal.schema.json` |
| Scan/proposal/outbox | pass | `scripts/planning_loop.py`, `agents/planning/scans/`, `agents/planning/outbox/` |
| UI Planner | pass | `src/agent_runtime/ui_state.py`, `src/agent_runtime/ui_console.py`, `src/agent_runtime/ui_commands.py` |
| Guardrail/C-mode | pass | `agents/project/PLANNING-GUARDRAILS.yml`, `agents/project/C-MODE-PROMOTION-CHECKLIST.md` |
| Verification | pass | `{verify_report}` |

### Decision

- B-mode proposal-only RSI planning is available locally.
- C-mode remains blocked until the promotion gate prerequisites are met.
- Owner-only/external/release/destructive actions remain out of scope.
"""
    raw = raw.rstrip() + note + "\n"
    status_path.write_text(raw, encoding="utf-8")
    return status_path.relative_to(root).as_posix()


def _update_pointer(root: Path, *, completed_at: str, verify_report: str) -> str:
    pointer_path = root / "agents" / "project" / "NEXT-SESSION-POINTER.yml"
    if not pointer_path.exists():
        return ""
    lines = pointer_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    in_rsi_agent = False
    for line in lines:
        stripped = line.strip()
        if stripped == "- task_id: TASK-AR-234":
            in_rsi_agent = True
            out.append(line)
            continue
        if in_rsi_agent and line.startswith("    - task_id: ") and stripped != "- task_id: TASK-AR-234":
            in_rsi_agent = False
        if in_rsi_agent:
            if stripped.startswith("status: "):
                out.append("      status: completed")
                continue
            if stripped.startswith("phase: "):
                out.append("      phase: taskset-completed")
                continue
            if stripped.startswith("progress_pct: "):
                out.append("      progress_pct: 100")
                continue
            if stripped.startswith("step_index: "):
                out.append("      step_index: 10")
                continue
            if stripped.startswith("step_total: "):
                out.append("      step_total: 10")
                continue
            if stripped.startswith("status_text: "):
                out.append('      status_text: "TASKSET-AR-RSI-PLANNING completed after verification report passed."')
                continue
        if stripped.startswith("updated_at: "):
            out.append(f"updated_at: {completed_at}")
            continue
        if "TASKSET-AR-RSI-PLANNING/TASK-AR-234 is implementation-patched and verification-pending" in line:
            out.append(
                line.replace(
                    "TASKSET-AR-RSI-PLANNING/TASK-AR-234 is implementation-patched and verification-pending",
                    "TASKSET-AR-RSI-PLANNING/TASK-AR-234 is complete",
                )
            )
            continue
        if "TASK-AR-234 RSI planning loop is patched and awaiting explicit verification" in line:
            out.append(
                line.replace(
                    "TASK-AR-234 RSI planning loop is patched and awaiting explicit verification",
                    "TASK-AR-234 RSI planning loop is complete",
                )
            )
            continue
        if "TASK-AR-234 RSI planning implementation patched with verification pending" in line:
            out.append(
                line.replace(
                    "TASK-AR-234 RSI planning implementation patched with verification pending",
                    f"TASK-AR-234 RSI planning task-set completed with `{verify_report}`",
                )
            )
            continue
        out.append(line)
    if not any("RSI planning completed verification report" in line for line in out):
        out.extend(
            [
                "  rsi_planning_completed:",
                f"    - {verify_report}",
                "  rsi_planning_note: RSI planning completed verification report is the canonical closeout evidence.",
            ]
        )
    pointer_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return pointer_path.relative_to(root).as_posix()


def _run(command: list[str], root: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=root, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def closeout(root: Path, *, verify_report: str, apply: bool) -> dict[str, Any]:
    verify_report = verify_report.replace("\\", "/")
    _load_verify_report(root, verify_report)
    completed_at = _now()
    planned_changes = [f"agents/lead_engineer/tasks/{task_id}.md" for task_id in TASK_IDS]
    planned_changes.extend(
        [
            f"agents/runtime/task_claims/{CLAIM_ID}.json",
            f"agents/runtime/task_claims/{CLAIM_ID}.handoff.md",
            f"agents/runtime/task_claims/{CLAIM_ID}.log.md",
            "STATUS.md",
            "BACKLOG-BOARD.md",
        ]
    )
    if not apply:
        return {
            "status": "dry_run",
            "verification_report": verify_report,
            "planned_changes": planned_changes,
        }

    changed: list[str] = []
    for task_id in TASK_IDS:
        path = _task_path(root, task_id)
        path.write_text(close_task_text(path.read_text(encoding="utf-8"), completed_at=completed_at, verify_report=verify_report), encoding="utf-8")
        changed.append(path.relative_to(root).as_posix())
    changed.extend(_close_claim(root, completed_at=completed_at, verify_report=verify_report))
    changed.append(_append_status(root, completed_at=completed_at, verify_report=verify_report))
    pointer = _update_pointer(root, completed_at=completed_at, verify_report=verify_report)
    if pointer:
        changed.append(pointer)

    board = _run([sys.executable, "scripts/backlog_board.py", "--write"], root)
    require_complete = _run(
        [sys.executable, "scripts/taskset_work_gate.py", "--task-set-id", TASKSET_ID, "--require-complete", "--check"],
        root,
    )
    owner_gate = _run([sys.executable, "scripts/owner_governance_gate.py"], root)
    return {
        "status": "pass" if board["returncode"] == 0 and require_complete["returncode"] == 0 and owner_gate["returncode"] == 0 else "block",
        "completed_at": completed_at,
        "verification_report": verify_report,
        "changed": changed,
        "post_checks": {
            "backlog_board": board,
            "taskset_require_complete": require_complete,
            "owner_governance": owner_gate,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Close TASKSET-AR-RSI-PLANNING after verification report passes")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--verification-report", default=VERIFY_REPORT)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    payload = closeout(Path(args.root).resolve(), verify_report=args.verification_report, apply=args.apply)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status={payload['status']}")
    return 0 if payload["status"] in {"pass", "dry_run"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
