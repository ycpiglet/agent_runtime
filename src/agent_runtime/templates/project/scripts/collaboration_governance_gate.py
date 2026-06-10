"""Validate measurable multi-agent collaboration governance.

This gate turns collaboration expectations into observable signals:

- role usage from task claim records;
- process artifacts from `reviews/`;
- root runtime capability promotion from `scripts/`;
- explicit waiver records with expiry;
- lifecycle hygiene warnings such as future heartbeats and incomplete released
  claim metadata.

Only unwaived `block` findings fail `--check`. `watch` findings remain visible
so the system can track drift without blocking unrelated active panes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


POLICY_PATH = Path("agents/project/COLLABORATION-GOVERNANCE.json")
ACTIVE_STATUSES = {"assigned", "claimed", "in_progress", "review", "waiting_review", "working"}
DONE_STATUSES = {"completed", "done", "released"}


@dataclass(frozen=True)
class Finding:
    severity: str
    subject: str
    path: str
    detail: str
    waiver_id: str | None = None

    @property
    def effective_severity(self) -> str:
        return "waived" if self.waiver_id else self.severity


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


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
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _load_policy(root: Path, findings: list[Finding]) -> dict[str, Any]:
    path = root / POLICY_PATH
    policy = _read_json(path)
    if policy is None:
        findings.append(
            Finding(
                "block",
                "policy:missing-or-invalid",
                POLICY_PATH.as_posix(),
                "collaboration governance policy must be valid JSON",
            )
        )
        return {}
    if policy.get("schema") != "agent-runtime-collaboration-governance/v1":
        findings.append(
            Finding(
                "block",
                "policy:schema",
                POLICY_PATH.as_posix(),
                "policy schema must be agent-runtime-collaboration-governance/v1",
            )
        )
    return policy


def _waiver_dir(policy: dict[str, Any]) -> str:
    contract = policy.get("waiver_contract")
    if isinstance(contract, dict):
        directory = contract.get("directory")
        if isinstance(directory, str) and directory.strip():
            return directory
    return "agents/project/waivers"


def _valid_waivers(root: Path, policy: dict[str, Any], now: datetime, findings: list[Finding]) -> dict[str, str]:
    subject_to_waiver: dict[str, str] = {}
    contract = policy.get("waiver_contract") if isinstance(policy.get("waiver_contract"), dict) else {}
    expected_schema = str(contract.get("schema") or "agent-runtime-collaboration-waiver/v1")
    required_fields = contract.get("required_fields")
    if not isinstance(required_fields, list):
        required_fields = ["schema", "id", "subjects", "reason", "approved_by", "created_at", "expires_at", "mitigation"]

    base = root / _waiver_dir(policy)
    if not base.is_dir():
        return subject_to_waiver
    for path in sorted(base.glob("*.json"), key=lambda item: item.name.lower()):
        rel = _rel(root, path)
        waiver = _read_json(path)
        if waiver is None:
            findings.append(Finding("block", "waiver:invalid-json", rel, "waiver must be a JSON object"))
            continue
        waiver_id = str(waiver.get("id") or path.stem)
        for field in required_fields:
            value = waiver.get(str(field))
            if value is None or value == "" or value == []:
                findings.append(Finding("block", f"waiver:missing-field:{field}", rel, f"waiver {waiver_id} is missing {field}"))
        if waiver.get("schema") != expected_schema:
            findings.append(Finding("block", "waiver:schema", rel, f"waiver {waiver_id} has invalid schema"))
            continue
        expires_at = _parse_dt(str(waiver.get("expires_at") or ""))
        if expires_at is None:
            findings.append(Finding("block", "waiver:bad-expires-at", rel, f"waiver {waiver_id} has invalid expires_at"))
            continue
        if expires_at < now:
            findings.append(Finding("block", "waiver:expired", rel, f"waiver {waiver_id} expired at {expires_at.isoformat()}"))
            continue
        subjects = waiver.get("subjects")
        if not isinstance(subjects, list):
            findings.append(Finding("block", "waiver:subjects-not-list", rel, f"waiver {waiver_id} subjects must be a list"))
            continue
        for subject in subjects:
            if isinstance(subject, str) and subject.strip():
                subject_to_waiver[subject.strip()] = waiver_id
    return subject_to_waiver


def _apply_waivers(findings: list[Finding], waivers: dict[str, str]) -> list[Finding]:
    out: list[Finding] = []
    for finding in findings:
        waiver_id = waivers.get(finding.subject)
        if finding.severity == "block" and waiver_id:
            out.append(Finding(finding.severity, finding.subject, finding.path, finding.detail, waiver_id))
        else:
            out.append(finding)
    return out


def _claim_files(root: Path) -> list[Path]:
    base = root / "agents" / "runtime" / "task_claims"
    if not base.is_dir():
        return []
    return sorted(base.glob("*.json"), key=lambda item: item.name.lower())


def _read_claims(root: Path, findings: list[Finding]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    for path in _claim_files(root):
        payload = _read_json(path)
        rel = _rel(root, path)
        if payload is None:
            findings.append(Finding("block", "claim:invalid-json", rel, "claim must be a JSON object"))
            continue
        payload["_path"] = rel
        claims.append(payload)
    return claims


def _review_artifact_counts(root: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    reviews = root / "reviews"
    if not reviews.is_dir():
        return counts
    for path in reviews.iterdir():
        if not path.is_file():
            continue
        prefix = path.name.split("-", 1)[0].upper()
        counts[prefix] += 1
    return counts


def _check_roles(policy: dict[str, Any], claims: list[dict[str, Any]], findings: list[Finding]) -> None:
    role_counts = Counter(str(claim.get("agent_role") or "").strip() for claim in claims)
    min_claims = int(policy.get("min_claims_for_role_coverage") or 0)
    if len(claims) < min_claims:
        findings.append(
            Finding(
                "watch",
                "role-usage:coverage-below-threshold",
                "agents/runtime/task_claims",
                f"claim count {len(claims)} is below role coverage threshold {min_claims}",
            )
        )
        return

    minimums = policy.get("minimum_claim_roles")
    if isinstance(minimums, dict):
        for role, required in sorted(minimums.items()):
            try:
                required_count = int(required)
            except (TypeError, ValueError):
                required_count = 1
            actual = role_counts.get(str(role), 0)
            if actual < required_count:
                findings.append(
                    Finding(
                        "block",
                        f"role-usage:{role}",
                        "agents/runtime/task_claims",
                        f"role {role} has {actual} claims, expected at least {required_count}",
                    )
                )

    monitored = policy.get("monitored_roles")
    if isinstance(monitored, list):
        for role in sorted(str(role) for role in monitored if str(role).strip()):
            if role_counts.get(role, 0) == 0:
                findings.append(
                    Finding(
                        "watch",
                        f"role-monitor:{role}",
                        "agents/runtime/task_claims",
                        f"role {role} has no claim evidence in this window",
                    )
                )


def _check_artifacts(root: Path, policy: dict[str, Any], findings: list[Finding]) -> None:
    counts = _review_artifact_counts(root)
    required = policy.get("required_review_artifacts")
    if not isinstance(required, list):
        return
    for prefix in sorted(str(item).upper() for item in required if str(item).strip()):
        if counts.get(prefix, 0) == 0:
            findings.append(
                Finding(
                    "block",
                    f"artifact:{prefix}",
                    "reviews",
                    f"required review artifact prefix {prefix}-* is missing",
                )
            )


def _check_capabilities(root: Path, policy: dict[str, Any], findings: list[Finding]) -> None:
    capabilities = policy.get("required_root_capabilities")
    if not isinstance(capabilities, dict):
        return
    for capability, paths in sorted(capabilities.items()):
        if not isinstance(paths, list):
            paths = []
        existing = [str(path) for path in paths if isinstance(path, str) and (root / path).exists()]
        if not existing:
            findings.append(
                Finding(
                    "block",
                    f"root-capability:{capability}",
                    "scripts",
                    f"root runtime capability {capability} has no promoted path among {paths}",
                )
            )


def _check_lifecycle(root: Path, policy: dict[str, Any], claims: list[dict[str, Any]], now: datetime, findings: list[Finding]) -> None:
    thresholds = policy.get("lifecycle_thresholds") if isinstance(policy.get("lifecycle_thresholds"), dict) else {}
    future_watch = int(thresholds.get("future_heartbeat_watch_minutes") or 5)
    expected_phase = str(thresholds.get("released_claim_expected_phase") or "taskset-completed")
    expected_progress = int(thresholds.get("released_claim_expected_progress_pct") or 100)

    for claim in claims:
        rel = str(claim.get("_path") or "agents/runtime/task_claims")
        claim_id = str(claim.get("claim_id") or rel)
        status = str(claim.get("status") or "").strip().lower()
        heartbeat = _parse_dt(str(claim.get("last_heartbeat") or ""))
        if heartbeat is None:
            findings.append(Finding("watch", f"lifecycle:heartbeat-missing:{claim_id}", rel, "claim has no parseable last_heartbeat"))
        else:
            delta_minutes = (heartbeat - now).total_seconds() / 60
            if delta_minutes > future_watch:
                findings.append(
                    Finding(
                        "watch",
                        f"lifecycle:future-heartbeat:{claim_id}",
                        rel,
                        f"last_heartbeat is {delta_minutes:.1f} minutes in the future",
                    )
                )

        if status in DONE_STATUSES:
            phase = str(claim.get("phase") or "").strip()
            try:
                progress = int(claim.get("progress_pct"))
            except (TypeError, ValueError):
                progress = -1
            if phase != expected_phase or progress != expected_progress:
                findings.append(
                    Finding(
                        "watch",
                        f"lifecycle:released-claim-incomplete:{claim_id}",
                        rel,
                        f"released claim has phase={phase!r}, progress_pct={claim.get('progress_pct')!r}",
                    )
                )

        if status in ACTIVE_STATUSES:
            worktree = str(claim.get("worktree_path") or "").strip()
            if worktree and not (root / worktree).exists():
                findings.append(
                    Finding(
                        "watch",
                        f"lifecycle:active-worktree-missing:{claim_id}",
                        rel,
                        f"active claim worktree path does not exist: {worktree}",
                    )
                )


def analyze(root: Path, now: datetime) -> list[Finding]:
    root = root.resolve()
    raw_findings: list[Finding] = []
    policy = _load_policy(root, raw_findings)
    if not policy:
        return raw_findings
    waivers = _valid_waivers(root, policy, now, raw_findings)
    claims = _read_claims(root, raw_findings)
    _check_roles(policy, claims, raw_findings)
    _check_artifacts(root, policy, raw_findings)
    _check_capabilities(root, policy, raw_findings)
    _check_lifecycle(root, policy, claims, now, raw_findings)
    return _apply_waivers(raw_findings, waivers)


def render(root: Path, findings: list[Finding]) -> str:
    counts = Counter(finding.effective_severity for finding in findings)
    unwaived_blocks = [finding for finding in findings if finding.severity == "block" and not finding.waiver_id]
    status = "fail" if unwaived_blocks else "pass"
    lines = [
        f"collaboration-governance-gate: {status}",
        f"root={root.resolve()}",
        f"findings={len(findings)}",
        f"block={counts.get('block', 0)}",
        f"watch={counts.get('watch', 0)}",
        f"waived={counts.get('waived', 0)}",
    ]
    for finding in findings:
        waiver = f" waiver={finding.waiver_id}" if finding.waiver_id else ""
        lines.append(f"- {finding.effective_severity} {finding.subject} {finding.path}:{waiver} {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Collaboration governance gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--now", help="ISO timestamp for deterministic tests")
    parser.add_argument("--check", action="store_true", help="Fail on unwaived block findings")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = _parse_dt(args.now) if args.now else datetime.now(timezone.utc).astimezone()
    if now is None:
        print("invalid --now timestamp")
        return 2
    findings = analyze(args.root, now)
    print(render(args.root, findings))
    if args.check and any(finding.severity == "block" and not finding.waiver_id for finding in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
