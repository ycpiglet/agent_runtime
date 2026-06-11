"""Classify multi-pane claim timeline and worktree drift without mutation."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"active", "assigned", "claimed", "in_progress", "review", "running", "waiting_review", "working"}
DONE_STATUSES = {"completed", "done", "released"}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_claims(root: Path, block: list[str]) -> list[dict[str, Any]]:
    claims_dir = root / "agents" / "runtime" / "task_claims"
    if not claims_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            block.append(f"claim-invalid:{path.as_posix()}:{exc}")
            continue
        if isinstance(payload, dict):
            payload["_path"] = path.as_posix()
            claims.append(payload)
    return claims


def check_root(root: Path | str, now: str | None = None) -> dict[str, Any]:
    root_path = Path(root).resolve()
    reference = _parse_dt(now) if now else datetime.now(timezone.utc).astimezone()
    if reference is None:
        return {"schema": "agent-runtime-multipane-drift-gate/v1", "status": "block", "block": ["invalid-now"], "watch": []}
    block: list[str] = []
    watch: list[str] = []
    claims = _load_claims(root_path, block)
    for claim in claims:
        claim_id = str(claim.get("claim_id") or claim.get("_path") or "unknown")
        status = str(claim.get("status") or "").strip().lower()
        heartbeat = _parse_dt(str(claim.get("last_heartbeat") or ""))
        if heartbeat and (heartbeat - reference).total_seconds() > 300:
            watch.append(f"future-heartbeat:{claim_id}")
        if status in DONE_STATUSES:
            phase = str(claim.get("phase") or "")
            try:
                progress = int(claim.get("progress_pct"))
            except (TypeError, ValueError):
                progress = -1
            if phase != "taskset-completed" or progress != 100:
                watch.append(f"released-claim-incomplete:{claim_id}")
        if status in ACTIVE_STATUSES:
            worktree = str(claim.get("worktree_path") or "").strip()
            if worktree and not (root_path / worktree).exists():
                watch.append(f"active-worktree-missing:{claim_id}")
    status = "block" if block else "watch" if watch else "pass"
    return {
        "schema": "agent-runtime-multipane-drift-gate/v1",
        "status": status,
        "block": block,
        "watch": watch,
        "claims_total": len(claims),
        "stale_worktree_candidates": [],
    }


def render_text(report: dict[str, Any], root: Path) -> str:
    lines = [
        f"multipane-drift-gate: {report['status']}",
        f"root={root.resolve()}",
        f"block={len(report['block'])}",
        f"watch={len(report['watch'])}",
    ]
    for item in report["block"]:
        lines.append(f"- block {item}")
    for item in report["watch"]:
        lines.append(f"- watch {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check multi-pane claim and worktree drift")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--now")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    report = check_root(args.root, now=args.now)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_text(report, args.root))
    return 1 if args.check and report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
