"""Deferred plan revalidation: snapshot plan assumptions, verify at dispatch time.

A taskset plan is registered against the repository state at planning time.
Parallel sessions (codex/claude) can land structural changes between
registration and implementation, silently invalidating the plan. This gate
implements lazy evaluation for plans: anchors (files the plan depends on,
or files the plan assumes do not exist yet) are recorded with hashes at
registration time, and evaluation is deferred to the moment of use.

Trigger points:
  T0 registration : `record` writes the assumption snapshot.
  T1 observation  : `--check` after any merge (informational, non-blocking).
  T2 dispatch     : `--check --taskset X` before claiming an implementation
                    task; drift means the plan must be revalidated through a
                    replan review before work starts.
  T3 replan       : the replan review re-runs `record` to re-anchor the plan.

This gate is intentionally NOT part of the owner governance commit chain:
drift after a merge is an expected state that must block dispatch, not
unrelated commits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REGISTRY_REL = "agents/project/work-items/PLAN-ASSUMPTIONS.json"
SCHEMA = "agent-runtime-plan-assumptions/v1"
KST = timezone(timedelta(hours=9))


def _now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _registry_path(root: Path) -> Path:
    return root / REGISTRY_REL


def _load_registry(root: Path) -> dict:
    path = _registry_path(root)
    if not path.exists():
        return {"schema": SCHEMA, "updated_at": "", "assumption_sets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_registry(root: Path, registry: dict) -> None:
    registry["schema"] = SCHEMA
    registry["updated_at"] = _now_iso()
    path = _registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _build_anchor(root: Path, rel: str) -> dict:
    target = root / rel
    if target.exists():
        return {"path": rel, "kind": "sha256", "value": _sha256(target)}
    return {"path": rel, "kind": "absent", "value": ""}


def cmd_record(root: Path, taskset: str, design_record: str, anchors: list[str]) -> int:
    registry = _load_registry(root)
    entry = {
        "taskset_id": taskset,
        "design_record": design_record,
        "recorded_at": _now_iso(),
        "revalidation_policy": "block_dispatch_on_drift",
        "anchors": [_build_anchor(root, rel) for rel in anchors],
    }
    sets = [s for s in registry["assumption_sets"] if s.get("taskset_id") != taskset]
    sets.append(entry)
    registry["assumption_sets"] = sorted(sets, key=lambda s: s["taskset_id"])
    _save_registry(root, registry)
    print(f"plan-assumption-gate: recorded {taskset}")
    print(f"anchors={len(entry['anchors'])}")
    for anchor in entry["anchors"]:
        print(f"- {anchor['kind']}:{anchor['path']}")
    return 0


def _check_anchor(root: Path, anchor: dict) -> str | None:
    target = root / anchor["path"]
    if anchor["kind"] == "sha256":
        if not target.exists():
            return f"anchor-missing:{anchor['path']}"
        if _sha256(target) != anchor["value"]:
            return f"anchor-hash-changed:{anchor['path']}"
        return None
    if anchor["kind"] == "absent":
        if target.exists():
            return f"anchor-appeared:{anchor['path']}"
        return None
    return f"anchor-unknown-kind:{anchor['kind']}:{anchor['path']}"


def cmd_check(root: Path, taskset: str | None) -> int:
    registry = _load_registry(root)
    sets = registry.get("assumption_sets", [])
    if taskset is not None:
        sets = [s for s in sets if s.get("taskset_id") == taskset]
        if not sets:
            print(f"plan-assumption-gate: fail")
            print("findings=1")
            print(f"- registry:missing-taskset:{taskset}")
            return 1
    findings: list[str] = []
    for entry in sets:
        for anchor in entry.get("anchors", []):
            finding = _check_anchor(root, anchor)
            if finding is not None:
                findings.append(f"{entry['taskset_id']}: {finding}")
    status = "fail" if findings else "pass"
    print(f"plan-assumption-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    if findings:
        print(
            "action=drifted plan assumptions; run a replan review for the "
            "affected taskset, then re-record anchors before dispatch"
        )
    return 1 if findings else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Snapshot plan assumptions and verify them at dispatch time"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command")

    record = sub.add_parser("record", help="Record/refresh an assumption snapshot")
    record.add_argument("--taskset", required=True)
    record.add_argument("--design-record", required=True)
    record.add_argument(
        "--anchor",
        action="append",
        required=True,
        help="Repo-relative path; existing file is hashed, missing path is pinned as absent",
    )

    parser.add_argument("--check", action="store_true", help="Verify recorded anchors")
    parser.add_argument("--taskset", dest="check_taskset", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.command == "record":
        return cmd_record(root, args.taskset, args.design_record, args.anchor)
    if args.check:
        return cmd_check(root, args.check_taskset)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
