"""Validate runtime claim attribution against agent instance records."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import agent_instance_registry


CLAIMS_DIR = Path("agents/runtime/task_claims")
ACTIVE_STATUSES = {
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "running",
    "waiting_review",
    "working",
}


@dataclass(frozen=True)
class ClaimRecord:
    path: Path
    payload: dict[str, Any]

    @property
    def claim_id(self) -> str:
        return str(self.payload.get("claim_id") or self.path.stem).strip()

    @property
    def active(self) -> bool:
        return str(self.payload.get("status") or "").strip().lower() in ACTIVE_STATUSES


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "invalid-record"
    return payload, None


def _load_claims(root: Path) -> tuple[list[ClaimRecord], list[str]]:
    claim_dir = root / CLAIMS_DIR
    if not claim_dir.is_dir():
        return [], []
    claims: list[ClaimRecord] = []
    findings: list[str] = []
    for path in sorted(claim_dir.glob("*.json"), key=lambda item: item.name.lower()):
        payload, error = _load_json(path)
        if error:
            findings.append(f"{_rel(root, path)}: agent-identity:claim-invalid-json:{error}")
            continue
        claims.append(ClaimRecord(path=path, payload=payload or {}))
    return claims, findings


def _instance_payload(root: Path, claim: ClaimRecord) -> tuple[Path, dict[str, Any] | None, str | None]:
    instance_id = str(claim.payload.get("agent_instance_id") or "").strip()
    path = agent_instance_registry.instance_path(root, instance_id)
    if not path.exists():
        return path, None, "missing"
    payload, error = _load_json(path)
    return path, payload, error


def _required_claim_fields(claim: ClaimRecord) -> list[str]:
    missing: list[str] = []
    for field in ("agent_role", "agent_instance_id", "display_name", "callsite_id"):
        if not str(claim.payload.get(field) or "").strip():
            missing.append(field)
    return missing


def _field_pairs(claim: ClaimRecord) -> dict[str, str]:
    return {
        "agent_instance_id": str(claim.payload.get("agent_instance_id") or "").strip(),
        "role": str(claim.payload.get("agent_role") or "").strip(),
        "team_id": str(claim.payload.get("team_id") or "").strip(),
        "display_name": str(claim.payload.get("display_name") or "").strip(),
        "callsite_id": str(claim.payload.get("callsite_id") or "").strip(),
        "pane_id": str(claim.payload.get("pane_id") or "").strip(),
        "worktree_path": str(claim.payload.get("worktree_path") or "").strip(),
        "model_tier": str(claim.payload.get("model_tier") or "").strip(),
    }


def _validate_claim_instance(root: Path, claim: ClaimRecord) -> list[str]:
    findings: list[str] = []
    claim_rel = _rel(root, claim.path)
    for field in _required_claim_fields(claim):
        findings.append(f"{claim_rel}: agent-identity:claim-missing:{claim.claim_id}:{field}")
    instance_id = str(claim.payload.get("agent_instance_id") or "").strip()
    if not instance_id:
        findings.append(f"{claim_rel}: agent-identity:role-only-attribution:{claim.claim_id}")
        return findings

    instance_path, payload, error = _instance_payload(root, claim)
    if error == "missing":
        findings.append(f"{claim_rel}: agent-identity:instance-missing:{claim.claim_id}:{instance_id}")
        return findings
    if error:
        findings.append(f"{_rel(root, instance_path)}: agent-identity:instance-invalid-json:{error}")
        return findings
    assert payload is not None
    if str(payload.get("schema") or "") != agent_instance_registry.SCHEMA:
        findings.append(f"{_rel(root, instance_path)}: agent-identity:instance-invalid-schema:{instance_id}")

    for field, expected in _field_pairs(claim).items():
        actual = str(payload.get(field) or "").strip()
        if actual != expected:
            findings.append(f"{_rel(root, instance_path)}: agent-identity:instance-field-mismatch:{claim.claim_id}:{field}")

    claim_refs = [str(item) for item in payload.get("claim_refs", []) if str(item).strip()]
    if claim_rel not in claim_refs:
        findings.append(f"{_rel(root, instance_path)}: agent-identity:claim-ref-missing:{claim.claim_id}:{instance_id}")
    return findings


def check_root(root: Path, *, all_claims: bool = False) -> list[str]:
    root = root.resolve()
    claims, findings = _load_claims(root)
    for claim in claims:
        if not all_claims and not claim.active:
            continue
        findings.extend(_validate_claim_instance(root, claim))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent identity attribution gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--all", action="store_true", help="Validate released/historical claims as well as active claims")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_root(args.root, all_claims=args.all)
    status = "fail" if findings else "pass"
    print(f"agent-identity-gate: {status}")
    print(f"root={args.root.resolve()}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
