"""Audit process and role evidence for multi-pane runtime work."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


POLICY_PATH = Path("agents/project/MULTIPANE-PROCESS-POLICY.yml")


def _parse_simple_yaml_lists(text: str) -> dict[str, list[str]]:
    data: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            current = line[:-1].strip()
            data.setdefault(current, [])
            continue
        if current and line.strip().startswith("- "):
            data[current].append(line.strip()[2:].strip().strip("\"'"))
    return data


def _load_policy(root: Path) -> tuple[dict[str, list[str]], list[str]]:
    path = root / POLICY_PATH
    if not path.exists():
        return {"required_artifacts": [], "required_roles": [], "monitored_roles": [], "waived_subjects": []}, [POLICY_PATH.as_posix()]
    return _parse_simple_yaml_lists(path.read_text(encoding="utf-8")), []


def _artifact_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    reviews = root / "reviews"
    if reviews.is_dir():
        for path in reviews.iterdir():
            if path.is_file():
                counts[path.name.split("-", 1)[0].upper()] += 1
    plans = root / "docs" / "superpowers" / "plans"
    if plans.is_dir():
        counts["PLAN"] += len([path for path in plans.glob("*.md") if path.is_file()])
    return counts


def _role_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    claims = root / "agents" / "runtime" / "task_claims"
    if not claims.is_dir():
        return counts
    for path in sorted(claims.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            role = str(payload.get("agent_role") or "").strip()
            if role:
                counts[role] += 1
    return counts


def audit(root: Path | str) -> dict[str, Any]:
    root_path = Path(root).resolve()
    policy, data_gaps = _load_policy(root_path)
    artifacts = _artifact_counts(root_path)
    roles = _role_counts(root_path)
    missing: list[str] = []
    waived_subjects = set(policy.get("waived_subjects", []))
    waived: list[str] = []

    for artifact in sorted(str(item).upper() for item in policy.get("required_artifacts", []) if item):
        subject = f"artifact:{artifact}"
        if artifacts.get(artifact, 0) == 0:
            (waived if subject in waived_subjects else missing).append(subject)
    for role in sorted(str(item) for item in policy.get("required_roles", []) if item):
        subject = f"role:{role}"
        if roles.get(role, 0) == 0:
            (waived if subject in waived_subjects else missing).append(subject)
    monitored_missing = [
        f"role-monitor:{role}"
        for role in sorted(str(item) for item in policy.get("monitored_roles", []) if item)
        if roles.get(role, 0) == 0
    ]
    status = "pass"
    if missing or monitored_missing or data_gaps:
        status = "watch"
    return {
        "schema": "agent-runtime-multipane-process-audit/v1",
        "status": status,
        "missing": missing,
        "waived": waived,
        "monitored_missing": monitored_missing,
        "data_gaps": data_gaps,
        "observed": {"artifacts": dict(artifacts), "roles": dict(roles)},
    }


def render_text(report: dict[str, Any], root: Path) -> str:
    lines = [
        f"multipane-process-audit: {report['status']}",
        f"root={root.resolve()}",
        f"missing={len(report['missing'])}",
        f"waived={len(report['waived'])}",
        f"monitored_missing={len(report['monitored_missing'])}",
    ]
    for key in ("missing", "waived", "monitored_missing", "data_gaps"):
        for item in report[key]:
            lines.append(f"- {key}: {item}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit multi-pane process compliance")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    report = audit(args.root)
    print(json.dumps(report, ensure_ascii=False, indent=2) if args.json else render_text(report, args.root))
    return 1 if args.check and report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
