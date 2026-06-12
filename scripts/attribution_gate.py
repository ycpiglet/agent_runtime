"""Instance-level attribution gate across claims, pane events, A2A, and evidence.

The agent identity contract (agents/project/AGENT-IDENTITY-CONTRACT.md, merged
2026-06-12) makes ``agent_instance_id`` the canonical runtime actor. This gate
verifies stored artifacts:

- Claims (``agents/runtime/task_claims/*.json``) must carry
  ``agent_instance_id``. Role-only claims newer than the contract cutoff date
  block; older ones are watch-level.
- Pane events (``agents/runtime/pane_events/*.jsonl``) must carry
  ``agent_instance_id`` (or an actor that resolves to an instance record).
  Events newer than the cutoff without instance attribution block; historical
  ones are watch-level.
- A2A messages (``agents/runtime/a2a/*.jsonl`` and
  ``agents/project/a2a/*.jsonl``): ``sender``/``receiver`` checked the same
  way; role-only attribution newer than the cutoff blocks.
- Evidence records (``agents/project/evidence/**/*.json`` and
  ``reviews/VERIFY-*.json``): ``verified_by``/``actor``/``actor_role`` fields.
  Role-valued attribution newer than the cutoff blocks; non-role tool labels
  (for example ``codex`` or ``work.py verify``) stay watch-level so existing
  automation does not break while migration completes.
- Causal links are validated when present: ``parent_instance_id`` must refer
  to an existing instance record and ``on_behalf_of`` must resolve to a known
  claim, task, or unit.

Cutoff policy: an artifact dated on or before ``CONTRACT_CUTOFF_DATE`` is
historical and at most watch-level. Artifacts dated after the cutoff are
enforced (block). Artifacts without a recoverable date are treated as
historical so the gate stays green on legacy data.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable


CONTRACT_CUTOFF_DATE = "2026-06-12"

CLAIMS_DIR = Path("agents/runtime/task_claims")
PANE_EVENTS_DIR = Path("agents/runtime/pane_events")
A2A_DIRS = (Path("agents/runtime/a2a"), Path("agents/project/a2a"))
EVIDENCE_DIR = Path("agents/project/evidence")
REVIEWS_DIR = Path("reviews")
INSTANCES_DIR = Path("agents/runtime/instances")
GOVERNANCE_CONFIG = Path("agents/project/COLLABORATION-GOVERNANCE.json")

INSTANCE_FIELD_NAMES = (
    "agent_instance_id",
    "actor_instance_uid",
    "actor_instance_id",
    "instance_uid",
    "instance_id",
)

ACTOR_FIELD_NAMES = ("actor", "actor_role", "verified_by", "recorded_by", "performed_by")

BUILTIN_ROLES = frozenset(
    {
        "architect",
        "beta-tester",
        "council",
        "diversity-council",
        "doc-steward",
        "evaluation-office",
        "independent-auditor",
        "lead-engineer",
        "orchestrator",
        "owner",
        "planning-coordinator",
        "progress-scout",
        "qa",
        "release-manager",
        "release-steward",
        "reviewer",
        "rsi-lab",
        "scribe",
        "secretary",
        "skeptic",
    }
)

DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
COMPACT_DATE_RE = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_role(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _date_of(*candidates: Any) -> str | None:
    """Extract the first ISO date (``YYYY-MM-DD``) from the candidate values."""
    for candidate in candidates:
        text = str(candidate or "").strip()
        if not text:
            continue
        match = DATE_RE.search(text)
        if match:
            return match.group(1)
        compact = COMPACT_DATE_RE.search(text)
        if compact:
            return "-".join(compact.groups())
    return None


def _severity(date_text: str | None, cutoff: str) -> str:
    if date_text and date_text > cutoff:
        return "block"
    return "watch"


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(exc)
    if not isinstance(payload, dict):
        return None, "invalid-record"
    return payload, None


def _load_jsonl(path: Path) -> tuple[list[tuple[int, dict[str, Any]]], list[str]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [], [str(exc)]
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_number}: {exc.msg}")
            continue
        if isinstance(payload, dict):
            rows.append((line_number, payload))
        else:
            errors.append(f"line {line_number}: not an object")
    return rows, errors


def _instance_field(record: dict[str, Any]) -> str:
    for name in INSTANCE_FIELD_NAMES:
        value = str(record.get(name) or "").strip()
        if value:
            return value
    return ""


class AttributionChecker:
    def __init__(self, root: Path, *, cutoff: str = CONTRACT_CUTOFF_DATE):
        self.root = root.resolve()
        self.cutoff = cutoff
        self.findings: list[tuple[str, str]] = []
        self.claims = self._load_claims()
        self.instances = self._load_instances()
        self.instance_ids = self._collect_instance_ids()
        self.known_roles = self._collect_roles()
        self.resolvable_ids = self._collect_resolvable_ids()

    # -- loading -----------------------------------------------------------

    def _load_claims(self) -> list[tuple[Path, dict[str, Any]]]:
        claims_dir = self.root / CLAIMS_DIR
        claims: list[tuple[Path, dict[str, Any]]] = []
        if not claims_dir.is_dir():
            return claims
        for path in sorted(claims_dir.glob("*.json"), key=lambda item: item.name.lower()):
            payload, error = _load_json(path)
            if error:
                self._add("watch", f"{_rel(self.root, path)}: attribution:claim-invalid-json:{error}")
                continue
            claims.append((path, payload or {}))
        return claims

    def _load_instances(self) -> list[tuple[Path, dict[str, Any]]]:
        instances_dir = self.root / INSTANCES_DIR
        instances: list[tuple[Path, dict[str, Any]]] = []
        if not instances_dir.is_dir():
            return instances
        for path in sorted(instances_dir.glob("*.json"), key=lambda item: item.name.lower()):
            payload, error = _load_json(path)
            if error:
                self._add("watch", f"{_rel(self.root, path)}: attribution:instance-invalid-json:{error}")
                continue
            instances.append((path, payload or {}))
        return instances

    def _collect_instance_ids(self) -> set[str]:
        ids: set[str] = set()
        for path, payload in self.instances:
            ids.add(path.stem)
            value = str(payload.get("agent_instance_id") or "").strip()
            if value:
                ids.add(value)
        return ids

    def _collect_roles(self) -> set[str]:
        roles = {_normalize_role(role) for role in BUILTIN_ROLES}
        config_path = self.root / GOVERNANCE_CONFIG
        if config_path.is_file():
            payload, error = _load_json(config_path)
            if payload and not error:
                minimum = payload.get("minimum_claim_roles")
                if isinstance(minimum, dict):
                    roles.update(_normalize_role(str(role)) for role in minimum)
                monitored = payload.get("monitored_roles")
                if isinstance(monitored, list):
                    roles.update(_normalize_role(str(role)) for role in monitored)
        for _, claim in self.claims:
            role = _normalize_role(str(claim.get("agent_role") or ""))
            if role:
                roles.add(role)
        roles.discard("")
        return roles

    def _collect_resolvable_ids(self) -> set[str]:
        ids: set[str] = set()
        for _, claim in self.claims:
            for field in ("claim_id", "task_id", "task_set_id", "unit_id"):
                value = str(claim.get(field) or "").strip()
                if value:
                    ids.add(value)
        for _, instance in self.instances:
            for field in ("task_id", "task_set_id", "unit_id"):
                value = str(instance.get(field) or "").strip()
                if value:
                    ids.add(value)
        ids.discard("")
        return ids

    # -- helpers -----------------------------------------------------------

    def _add(self, severity: str, message: str) -> None:
        self.findings.append((severity, message))

    def _is_instance(self, value: str) -> bool:
        return bool(value) and value in self.instance_ids

    def _is_role(self, value: str) -> bool:
        return _normalize_role(value) in self.known_roles

    def _resolves(self, value: str) -> bool:
        if value in self.resolvable_ids or value in self.instance_ids:
            return True
        for pattern in (
            f"agents/*/tasks/{value}.md",
            f"agents/*/tasks/units/*/{value}.md",
        ):
            if any(self.root.glob(pattern)):
                return True
        return False

    def _check_causal_links(self, rel: str, record: dict[str, Any], date_text: str | None, label: str) -> None:
        parent = str(record.get("parent_instance_id") or "").strip()
        if parent and not self._is_instance(parent):
            self._add(
                _severity(date_text, self.cutoff),
                f"{rel}: attribution:{label}-parent-instance-missing:{parent}",
            )
        on_behalf_of = str(record.get("on_behalf_of") or "").strip()
        if on_behalf_of and not self._resolves(on_behalf_of):
            self._add(
                _severity(date_text, self.cutoff),
                f"{rel}: attribution:{label}-on-behalf-of-unresolved:{on_behalf_of}",
            )

    # -- checks ------------------------------------------------------------

    def check_claims(self) -> None:
        for path, claim in self.claims:
            rel = _rel(self.root, path)
            claim_id = str(claim.get("claim_id") or path.stem).strip()
            date_text = _date_of(
                claim.get("claimed_at"),
                claim.get("created_at"),
                claim.get("updated_at"),
                claim_id,
            )
            if not _instance_field(claim):
                self._add(
                    _severity(date_text, self.cutoff),
                    f"{rel}: attribution:claim-role-only:{claim_id}",
                )
            self._check_causal_links(rel, claim, date_text, "claim")

    def check_instance_records(self) -> None:
        for path, instance in self.instances:
            rel = _rel(self.root, path)
            date_text = _date_of(instance.get("spawned_at"), instance.get("created_at"), instance.get("updated_at"))
            self._check_causal_links(rel, instance, date_text, "instance")

    def check_pane_events(self) -> None:
        events_dir = self.root / PANE_EVENTS_DIR
        if not events_dir.is_dir():
            return
        for path in sorted(events_dir.glob("*.jsonl"), key=lambda item: item.name.lower()):
            rel = _rel(self.root, path)
            rows, errors = _load_jsonl(path)
            for error in errors:
                self._add("watch", f"{rel}: attribution:pane-event-invalid-json:{error}")
            for line_number, event in rows:
                if _instance_field(event):
                    continue
                actor = str(event.get("actor") or "").strip()
                if self._is_instance(actor):
                    continue
                date_text = _date_of(event.get("ts"))
                severity = _severity(date_text, self.cutoff)
                where = f"{rel}:{line_number}"
                if self._is_role(actor):
                    self._add(severity, f"{where}: attribution:pane-event-role-only:{actor}")
                else:
                    self._add(severity, f"{where}: attribution:pane-event-unattributed:{actor or 'missing-actor'}")

    def _check_party(
        self,
        *,
        where: str,
        record: dict[str, Any],
        party: str,
        date_text: str | None,
        label: str,
    ) -> None:
        value = str(record.get(party) or "").strip()
        if not value:
            return
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        instance_value = str(
            record.get(f"{party}_instance_id")
            or record.get(f"{party}_instance_uid")
            or metadata.get(f"{party}_instance_id")
            or metadata.get(f"{party}_instance_uid")
            or ""
        ).strip()
        if instance_value or self._is_instance(value):
            return
        if self._is_role(value):
            self._add(
                _severity(date_text, self.cutoff),
                f"{where}: attribution:{label}-role-only:{party}:{value}",
            )
        else:
            self._add("watch", f"{where}: attribution:{label}-actor-unresolved:{party}:{value}")

    def check_a2a_messages(self) -> None:
        for a2a_dir in A2A_DIRS:
            directory = self.root / a2a_dir
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.jsonl"), key=lambda item: item.name.lower()):
                rel = _rel(self.root, path)
                rows, errors = _load_jsonl(path)
                for error in errors:
                    self._add("watch", f"{rel}: attribution:a2a-invalid-json:{error}")
                for line_number, row in rows:
                    date_text = _date_of(row.get("timestamp"), row.get("ts"), path.name)
                    where = f"{rel}:{line_number}"
                    for party in ("sender", "receiver"):
                        self._check_party(
                            where=where,
                            record=row,
                            party=party,
                            date_text=date_text,
                            label="a2a",
                        )

    def _check_evidence_actor(self, where: str, record: dict[str, Any], date_text: str | None) -> None:
        if _instance_field(record):
            return
        for field in ACTOR_FIELD_NAMES:
            value = str(record.get(field) or "").strip()
            if not value:
                continue
            if self._is_instance(value):
                return
            if self._is_role(value):
                self._add(
                    _severity(date_text, self.cutoff),
                    f"{where}: attribution:evidence-role-only:{field}:{value}",
                )
            else:
                self._add("watch", f"{where}: attribution:evidence-actor-unresolved:{field}:{value}")
            return

    def _evidence_paths(self) -> Iterable[Path]:
        evidence_dir = self.root / EVIDENCE_DIR
        if evidence_dir.is_dir():
            yield from sorted(evidence_dir.rglob("*.json"), key=lambda item: item.as_posix().lower())
        reviews_dir = self.root / REVIEWS_DIR
        if reviews_dir.is_dir():
            yield from sorted(reviews_dir.glob("VERIFY-*.json"), key=lambda item: item.name.lower())

    def check_evidence(self) -> None:
        for path in self._evidence_paths():
            rel = _rel(self.root, path)
            payload, error = _load_json(path)
            if error or payload is None:
                self._add("watch", f"{rel}: attribution:evidence-invalid-json:{error}")
                continue
            date_text = _date_of(
                payload.get("verified_at"),
                payload.get("generated_at"),
                payload.get("recorded_at"),
                payload.get("created_at"),
                payload.get("updated_at"),
                payload.get("timestamp"),
                path.name,
            )
            self._check_evidence_actor(rel, payload, date_text)
            events = payload.get("events")
            if isinstance(events, list):
                for index, event in enumerate(events):
                    if not isinstance(event, dict):
                        continue
                    event_date = _date_of(event.get("ts"), event.get("timestamp")) or date_text
                    self._check_evidence_actor(f"{rel}#events[{index}]", event, event_date)

    def run(self) -> list[tuple[str, str]]:
        self.check_claims()
        self.check_instance_records()
        self.check_pane_events()
        self.check_a2a_messages()
        self.check_evidence()
        return self.findings


def check_root(root: Path, *, cutoff: str = CONTRACT_CUTOFF_DATE) -> list[tuple[str, str]]:
    return AttributionChecker(root, cutoff=cutoff).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Instance attribution gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--cutoff", default=CONTRACT_CUTOFF_DATE, help="Identity contract cutoff date (YYYY-MM-DD)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_root(args.root, cutoff=args.cutoff)
    block = [message for severity, message in findings if severity == "block"]
    watch = [message for severity, message in findings if severity == "watch"]
    status = "fail" if block else "pass"
    print(f"attribution-gate: {status}")
    print(f"root={args.root.resolve()}")
    print(f"cutoff={args.cutoff}")
    print(f"findings={len(findings)}")
    print(f"block={len(block)}")
    print(f"watch={len(watch)}")
    for message in block:
        print(f"- block {message}")
    for message in watch:
        print(f"- watch {message}")
    return 1 if args.check and block else 0


if __name__ == "__main__":
    raise SystemExit(main())
