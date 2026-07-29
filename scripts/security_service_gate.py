"""Profile-scoped claim guard for security and production-risk paths."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src"
if SOURCE_ROOT.is_dir() and str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from agent_runtime.security_service import (  # noqa: E402
    SecurityPolicyError,
    analyze_active_claims,
    analyze_unit,
)


def _policy_path(root: Path) -> Path:
    return root / "agents" / "project" / "SECURITY-SERVICE-POLICY.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check security-service claim metadata without reading target contents"
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--unit-spec")
    mode.add_argument("--check-active", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--unit-id")
    parser.add_argument("--target-file", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    policy_path = _policy_path(root)

    try:
        if args.check_active:
            reports = analyze_active_claims(root, policy_path=policy_path)
        else:
            if not args.task_id or not args.unit_id:
                raise SecurityPolicyError(
                    "unit checks require canonical task and unit identities"
                )
            reports = (
                analyze_unit(
                    root,
                    args.unit_spec,
                    task_id=args.task_id,
                    unit_id=args.unit_id,
                    target_files=args.target_file or None,
                    policy_path=policy_path,
                ),
            )
    except SecurityPolicyError:
        payload = {
            "status": "block",
            "reason": "security_policy_error",
            "reports": [],
        }
        if args.json:
            print(json.dumps(payload, sort_keys=True))
        else:
            print("security-service-gate: block policy_error", file=sys.stderr)
        return 1

    blocked = any(report.status == "block" for report in reports)
    payload = {
        "status": "block" if blocked else "pass",
        "reports": [report.to_dict() for report in reports],
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        classification_count = sum(len(report.classifications) for report in reports)
        finding_count = sum(len(report.findings) for report in reports)
        print(
            "security-service-gate: "
            f"{payload['status']} reports={len(reports)} "
            f"classifications={classification_count} findings={finding_count}"
        )
        for report in reports:
            for finding in report.findings:
                print(
                    f"- {finding.risk_class} {finding.path} "
                    f"{finding.requirement}: {finding.detail}",
                    file=sys.stderr,
                )
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
