"""Role concentration advisory gate.

Reads agents/runtime/task_claims/*.json, tallies share by agent_role, and
emits non-blocking watch findings when:

  (a) any single role's share exceeds --threshold (default 0.60), or
  (b) any role in the configurable review/verify role set has zero claims.

Exit 0 always (advisory/watch-only). ASCII output.

JSON report shape (--json)
--------------------------
    {
      "schema": "agent-runtime-role-concentration/v1",
      "root": "<absolute repo root>",
      "generated_at": "<local iso timestamp>",
      "status": "pass" | "watch",
      "counts": {
        "total_claims": N,
        "roles": {"role-name": N, ...}
      },
      "findings": [
        {
          "severity": "watch",
          "code": "role-concentration" | "dormant-review-role",
          "role": "<role>",
          "share": 0.76,            # for role-concentration only
          "threshold": 0.60,        # for role-concentration only
          "detail": "<human text>"
        }
      ]
    }
"""

from __future__ import annotations

import argparse
import datetime
import json
from pathlib import Path
from typing import Any

REPORT_SCHEMA = "agent-runtime-role-concentration/v1"
CLAIMS_DIR = Path("agents") / "runtime" / "task_claims"

DEFAULT_THRESHOLD = 0.60
DEFAULT_REVIEW_ROLES: frozenset[str] = frozenset(
    {
        "reviewer",
        "independent-auditor",
        "qa",
        "council",
        "skeptic",
        "progress-scout",
        "scribe",
    }
)


def _local_iso() -> str:
    text = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime(
        "%Y-%m-%dT%H:%M:%S%z"
    )
    if len(text) >= 5 and text[-5] in "+-":
        text = text[:-2] + ":" + text[-2:]
    return text


def _load_claims(root: Path) -> list[dict[str, Any]]:
    claims_dir = root / CLAIMS_DIR
    if not claims_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claims_dir.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            claims.append(payload)
    return claims


def analyze(
    root: Path,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    review_roles: frozenset[str] | set[str] = DEFAULT_REVIEW_ROLES,
) -> list[dict[str, Any]]:
    """Analyze claims under root and return a list of finding dicts."""
    root = root.resolve()
    claims = _load_claims(root)

    role_counts: dict[str, int] = {}
    for claim in claims:
        role = str(claim.get("agent_role") or "unknown").strip()
        role_counts[role] = role_counts.get(role, 0) + 1

    total = sum(role_counts.values())
    findings: list[dict[str, Any]] = []

    # (a) Concentration finding
    for role, count in sorted(role_counts.items(), key=lambda kv: -kv[1]):
        share = count / total if total else 0.0
        if share > threshold:
            findings.append(
                {
                    "severity": "watch",
                    "code": "role-concentration",
                    "role": role,
                    "share": round(share, 4),
                    "threshold": threshold,
                    "detail": (
                        f"role '{role}' holds {share:.1%} of {total} claims"
                        f" (threshold {threshold:.0%}); consider distributing"
                        " work across reviewer/auditor/qa roles"
                    ),
                }
            )

    # (b) Dormant review-role finding
    for role in sorted(review_roles):
        if role_counts.get(role, 0) == 0:
            findings.append(
                {
                    "severity": "watch",
                    "code": "dormant-review-role",
                    "role": role,
                    "detail": (
                        f"review/verify role '{role}' has zero claims in window;"
                        " independent checks may be under-represented"
                    ),
                }
            )

    return findings


def build_report(
    root: Path,
    findings: list[dict[str, Any]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    review_roles: frozenset[str] | set[str] = DEFAULT_REVIEW_ROLES,
) -> dict[str, Any]:
    claims = _load_claims(root.resolve())
    role_counts: dict[str, int] = {}
    for claim in claims:
        role = str(claim.get("agent_role") or "unknown").strip()
        role_counts[role] = role_counts.get(role, 0) + 1

    total = sum(role_counts.values())
    return {
        "schema": REPORT_SCHEMA,
        "root": str(root.resolve()),
        "generated_at": _local_iso(),
        "status": "watch" if findings else "pass",
        "counts": {
            "total_claims": total,
            "roles": role_counts,
        },
        "findings": findings,
    }


def render(
    root: Path,
    findings: list[dict[str, Any]],
    *,
    threshold: float = DEFAULT_THRESHOLD,
    review_roles: frozenset[str] | set[str] = DEFAULT_REVIEW_ROLES,
) -> str:
    report = build_report(root, findings, threshold=threshold, review_roles=review_roles)
    counts = report["counts"]
    lines = [
        f"role-concentration-gate: {report['status']}",
        f"root={report['root']}",
        f"total_claims={counts['total_claims']}",
        f"threshold={threshold:.0%}",
        f"watch={len([f for f in findings if f['severity'] == 'watch'])}",
    ]
    # Role breakdown
    for role, count in sorted(counts["roles"].items(), key=lambda kv: -kv[1]):
        share = count / counts["total_claims"] if counts["total_claims"] else 0.0
        lines.append(f"  role={role} count={count} share={share:.1%}")
    # Findings
    for finding in findings:
        lines.append(f"- {finding['severity']} [{finding['code']}] role={finding['role']}: {finding['detail']}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Role concentration advisory gate (watch-only, exit 0)"
    )
    parser.add_argument("--check", action="store_true", help="Run check (always exits 0)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help="Share threshold above which a role triggers watch (default: 0.6)",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: cwd)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Emit machine-readable JSON report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    findings = analyze(root, threshold=args.threshold)
    if args.as_json:
        report = build_report(root, findings, threshold=args.threshold)
        print(json.dumps(report, ensure_ascii=True, indent=2))
    else:
        print(render(root, findings, threshold=args.threshold))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
