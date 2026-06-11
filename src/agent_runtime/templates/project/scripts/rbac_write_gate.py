"""Validate role-based write boundaries for local multi-agent sessions."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


EVENT_LOG = Path("agents/runtime/pane_events/pane-events.jsonl")
CLAIMS_DIR = Path("agents/runtime/task_claims")
POINTER_PATH = Path("agents/project/NEXT-SESSION-POINTER.yml")

ACTIVE_STATUSES = {
    "active",
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "running",
    "waiting_review",
    "working",
}

WRITE_EVENTS = {
    "role_write_attempted",
    "write_attempted",
    "ssot_write_attempted",
}

PANE_LIFECYCLE_EVENTS = {
    "claim_created",
    "pane_started",
    "pane_heartbeat",
    "claim_heartbeat",
    "started",
    "claimed",
    "heartbeat",
}

PROTECTED_WRITE_RULES = [
    {
        "id": "release-docs",
        "prefixes": [
            "agents/project/release/",
            "reviews/RELEASE-",
        ],
        "paths": [
            "RELEASE-GATE-TEMPLATE.yml",
            "agents/project/release/RELEASE-DECISION-v0.1.8.yml",
        ],
        "allowed_roles": {"owner", "release-steward", "release-orchestrator"},
    },
    {
        "id": "owner-docs",
        "prefixes": [],
        "paths": ["owner-docs.yml"],
        "allowed_roles": {"owner", "orchestrator", "release-orchestrator", "lead-engineer"},
    },
]


@dataclass(frozen=True)
class ClaimRecord:
    path: Path
    payload: dict[str, Any]

    @property
    def claim_id(self) -> str:
        return str(self.payload.get("claim_id") or "").strip()

    @property
    def role(self) -> str:
        return str(self.payload.get("agent_role") or "").strip()

    @property
    def status(self) -> str:
        return str(self.payload.get("status") or "").strip().lower()

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_path(value: object) -> str:
    return str(value or "").strip().replace("\\", "/").lstrip("./")


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists():
        return [], []
    rows: list[dict[str, Any]] = []
    findings: list[str] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            findings.append(f"{_rel(path.parent.parent.parent, path)}:{line_number}: rbac-write:invalid-json: {exc}")
            continue
        if not isinstance(value, dict):
            findings.append(f"{path.as_posix()}:{line_number}: rbac-write:invalid-event-record")
            continue
        rows.append(value)
    return rows, findings


def _load_claims(root: Path) -> tuple[list[ClaimRecord], list[str]]:
    claim_dir = root / CLAIMS_DIR
    if not claim_dir.is_dir():
        return [], []
    records: list[ClaimRecord] = []
    findings: list[str] = []
    for path in sorted(claim_dir.glob("*.json"), key=lambda item: item.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            findings.append(f"{_rel(root, path)}: rbac-write:claim-invalid-json: {exc}")
            continue
        if not isinstance(payload, dict):
            findings.append(f"{_rel(root, path)}: rbac-write:claim-invalid-record")
            continue
        records.append(ClaimRecord(path=path, payload=payload))
    return records, findings


def _parse_key_value(target: dict[str, str], raw: str) -> None:
    key, sep, value = raw.partition(":")
    if not sep:
        return
    target[key.strip()] = _unquote(value.strip())


def _load_current_agents(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    path = root / POINTER_PATH
    if not path.exists():
        return [], []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "current_agents: []":
            return [], []
        if stripped != "current_agents:":
            continue
        base_indent = len(line) - len(line.lstrip())
        agents: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        for raw in lines[index + 1 :]:
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip())
            if indent <= base_indent:
                break
            item = raw.strip()
            if item.startswith("- "):
                if current is not None:
                    agents.append(current)
                current = {}
                rest = item[2:].strip()
                if rest:
                    _parse_key_value(current, rest)
                continue
            if current is not None:
                _parse_key_value(current, item)
        if current is not None:
            agents.append(current)
        return agents, []
    return [], [f"{POINTER_PATH.as_posix()}: rbac-current-agents:missing-field"]


def _protected_rule(path_text: str) -> dict[str, Any] | None:
    normalized = _normalize_path(path_text)
    for rule in PROTECTED_WRITE_RULES:
        if normalized in rule["paths"]:
            return rule
        if any(normalized.startswith(prefix) for prefix in rule["prefixes"]):
            return rule
    return None


def _claims_by_id(claims: list[ClaimRecord]) -> dict[str, ClaimRecord]:
    return {claim.claim_id: claim for claim in claims if claim.claim_id}


def _event_role(event: dict[str, Any], claims: dict[str, ClaimRecord]) -> tuple[str, list[str]]:
    findings: list[str] = []
    claim_id = str(event.get("claim_id") or "").strip()
    event_role = str(event.get("actor_role") or event.get("agent_role") or event.get("actor") or "").strip()
    if claim_id and claim_id in claims:
        claim_role = claims[claim_id].role
        if event_role and event_role != claim_role:
            findings.append(f"rbac-write:claim-role-mismatch:{claim_id}:{event_role}!={claim_role}")
        return claim_role, findings
    return event_role, findings


def _validate_write_events(events: list[dict[str, Any]], claims: dict[str, ClaimRecord]) -> list[str]:
    findings: list[str] = []
    for event in events:
        event_name = str(event.get("event") or "").strip()
        if event_name not in WRITE_EVENTS:
            continue
        target_path = _normalize_path(
            event.get("target_path")
            or event.get("path")
            or event.get("ssot_path")
        )
        role, role_findings = _event_role(event, claims)
        findings.extend(role_findings)
        if not target_path:
            findings.append("rbac-write:missing-target-path")
            continue
        rule = _protected_rule(target_path)
        if rule is None:
            continue
        if role not in rule["allowed_roles"]:
            findings.append(
                f"rbac-write:role-not-allowed:{role or 'unknown'}:{target_path}:"
                f" rule={rule['id']} allowed={','.join(sorted(rule['allowed_roles']))}"
            )
    return findings


def _validate_current_agents(
    *,
    root: Path,
    active_claims: list[ClaimRecord],
    current_agents: list[dict[str, str]],
    events: list[dict[str, Any]],
) -> list[str]:
    findings: list[str] = []
    active_by_claim = _claims_by_id(active_claims)
    agents_by_claim = {agent.get("claim_id", ""): agent for agent in current_agents if agent.get("claim_id")}
    lifecycle_claims = {
        str(event.get("claim_id") or "").strip()
        for event in events
        if str(event.get("event") or "").strip() in PANE_LIFECYCLE_EVENTS
    }

    for claim in active_claims:
        if claim.claim_id not in agents_by_claim:
            findings.append(f"rbac-current-agents:missing-active-claim:{claim.claim_id}")
            continue
        agent = agents_by_claim[claim.claim_id]
        expected_fields = {
            "agent_role": claim.role,
            "agent_instance_id": str(claim.payload.get("agent_instance_id") or "").strip(),
            "display_name": str(claim.payload.get("display_name") or "").strip(),
            "callsite_id": str(claim.payload.get("callsite_id") or "").strip(),
        }
        for field, expected in expected_fields.items():
            if str(agent.get(field) or "").strip() != expected:
                findings.append(f"rbac-current-agents:field-mismatch:{claim.claim_id}:{field}")
        if claim.claim_id not in lifecycle_claims:
            findings.append(f"rbac-current-agents:missing-pane-event:{claim.claim_id}")

    for claim_id in agents_by_claim:
        if claim_id not in active_by_claim:
            findings.append(f"rbac-current-agents:stale-claim:{claim_id}")

    for field in ("agent_instance_id", "display_name", "callsite_id"):
        values = [str(claim.payload.get(field) or "").strip() for claim in active_claims]
        values = [value for value in values if value]
        if len(values) != len(set(values)):
            findings.append(f"rbac-current-agents:duplicate-{field.replace('_', '-')}")

    if active_claims and not (root / POINTER_PATH).exists():
        findings.append(f"{POINTER_PATH.as_posix()}: rbac-current-agents:pointer-missing")

    return findings


def check_root(root: Path) -> list[str]:
    root = root.resolve()
    claims, findings = _load_claims(root)
    events, event_findings = _load_jsonl(root / EVENT_LOG)
    current_agents, pointer_findings = _load_current_agents(root)
    findings.extend(event_findings)
    findings.extend(pointer_findings)
    findings.extend(_validate_write_events(events, _claims_by_id(claims)))
    active_claims = [claim for claim in claims if claim.active]
    findings.extend(
        _validate_current_agents(
            root=root,
            active_claims=active_claims,
            current_agents=current_agents,
            events=events,
        )
    )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Role-based write boundary gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_root(args.root)
    status = "fail" if findings else "pass"
    print(f"rbac-write-gate: {status}")
    print(f"root={args.root.resolve()}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
