from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DETERMINISTIC_NOW = "1970-01-01T00:00:00+00:00"
LOW_CONFIDENCE = 0.55
MAX_PROPOSALS_PER_SCAN = 20
ALLOWED_TRIGGERS = {"manual", "hook", "schedule", "ui", "task-complete", "cycle-complete"}
PROPOSAL_ONLY_TRIGGERS = {"hook", "schedule", "ui"}
HIGH_RISK_ACTIONS = {
    "release_version_consistency",
    "c_mode_promotion",
}
OWNER_BOUNDARY_TERMS = (
    "release",
    "version",
    "tag",
    "push",
    "publish",
    "external",
    "dependency",
    "secret",
    "prod",
    "destructive",
    "owner-only",
    "gate",
)


def _now(value: str | None = None) -> str:
    if value:
        return value
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch and epoch.isdigit():
        return datetime.fromtimestamp(int(epoch), timezone.utc).isoformat(timespec="seconds")
    return DETERMINISTIC_NOW


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, payload: Any) -> str:
    return f"{prefix}-{_stable_hash(payload)[:12].upper()}"


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null":
        return None
    try:
        return int(value)
    except ValueError:
        return value.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}, text

    meta: dict[str, Any] = {}
    current_list: str | None = None
    for raw in lines[1:end]:
        line = raw.rstrip()
        if not line.strip():
            current_list = None
            continue
        if line.startswith("  - ") and current_list:
            meta.setdefault(current_list, []).append(_parse_scalar(line[4:]))
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value:
            meta[key] = _parse_scalar(value)
            current_list = None
        else:
            meta[key] = []
            current_list = key
    return meta, "\n".join(lines[end + 1 :]).strip()


def _source(root: Path, rel_path: str, *, required: bool, kind: str) -> dict[str, Any]:
    path = root / rel_path
    exists = path.exists()
    return {
        "path": rel_path,
        "kind": kind,
        "required": required,
        "freshness": "present" if exists else ("missing" if required else "missing_optional"),
    }


def _finding(
    *,
    category: str,
    source_path: str,
    confidence: float,
    suggested_next_action: str,
    evidence: list[dict[str, Any]],
    risk_tier: str = "medium",
    trace_id: str | None = None,
) -> dict[str, Any]:
    payload = {
        "category": category,
        "source_path": source_path,
        "evidence": evidence,
        "suggested_next_action": suggested_next_action,
        "trace_id": trace_id,
    }
    return {
        "id": _stable_id("FIND", payload),
        "category": category,
        "source_path": source_path,
        "confidence": round(float(confidence), 3),
        "suggested_next_action": suggested_next_action,
        "risk_tier": risk_tier,
        "trace_id": trace_id,
        "evidence": evidence,
        "proposal_allowed": confidence >= LOW_CONFIDENCE,
    }


def _task_records(root: Path) -> list[tuple[Path, dict[str, Any], str]]:
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    records: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(tasks_dir.glob("TASK-*.md")):
        text = _read(path)
        meta, body = parse_frontmatter(text)
        records.append((path, meta, body))
    return records


def _scan_required_sources(root: Path, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    required_sources = [
        ("BACKLOG.md", True, "backlog"),
        ("BACKLOG-BOARD.md", True, "generated_board"),
        ("STATUS.md", True, "status"),
        ("AGENT_RUNTIME_RSI_PLANNING_BRIEF.md", True, "brief"),
        ("docs/superpowers/plans/2026-06-10-rsi-planning-loop.md", True, "plan"),
        ("agents/project/STATE-MACHINES.yml", True, "state_machine"),
        ("agents/project/PLANNING-LOOP-CONTRACT.md", True, "contract"),
        ("schemas/planning-proposal.schema.json", True, "schema"),
        ("agents/project/PLANNING-GUARDRAILS.yml", True, "guardrail_policy"),
        ("agents/project/C-MODE-PROMOTION-CHECKLIST.md", True, "promotion_gate"),
        ("agents/project/ORG.md", True, "organization"),
        ("agents/project/TEAMS.md", True, "teams"),
        ("agents/project/evals", False, "eval_artifacts"),
        ("agents/project/corrections", False, "correction_artifacts"),
        ("agents/project/a2a", False, "a2a_artifacts"),
        ("traces", False, "trace_artifacts"),
    ]
    sources = [_source(root, rel_path, required=required, kind=kind) for rel_path, required, kind in required_sources]
    for item in sources:
        if item["required"] and item["freshness"] == "missing":
            findings.append(
                _finding(
                    category="missing-source",
                    source_path=item["path"],
                    confidence=0.95,
                    suggested_next_action="restore the required planning source or create a proposal-only doc repair task",
                    evidence=[{"summary": f"Required planning source is missing: {item['path']}", "confidence": 0.95}],
                    risk_tier="medium",
                )
            )
    return sources


def _scan_tasks(root: Path, findings: list[dict[str, Any]]) -> None:
    for path, meta, body in _task_records(root):
        rel_path = _rel(root, path)
        task_id = str(meta.get("id") or path.stem)
        status = str(meta.get("status") or "").lower()
        if status in {"blocked", "hold"} and "blocked_reason" not in meta and "## Block" not in body:
            findings.append(
                _finding(
                    category="unresolved-hold-route",
                    source_path=rel_path,
                    confidence=0.82,
                    suggested_next_action="add a blocker reason, owner route, or unblock proposal",
                    evidence=[{"summary": f"{task_id} is {status} without an explicit blocker route", "confidence": 0.82}],
                    risk_tier="medium",
                )
            )
        audit_log = meta.get("audit_log")
        if not isinstance(audit_log, list) or not audit_log:
            findings.append(
                _finding(
                    category="missing-audit-link",
                    source_path=rel_path,
                    confidence=0.78,
                    suggested_next_action="add audit_log evidence links before closing the task",
                    evidence=[{"summary": f"{task_id} has no audit_log entries", "confidence": 0.78}],
                    risk_tier="low",
                )
            )
            continue
        for ref in audit_log:
            if not isinstance(ref, str) or not ref.strip() or ref.endswith("/"):
                continue
            if ref.startswith(("http://", "https://")):
                continue
            ref_path = root / ref
            if not ref_path.exists():
                findings.append(
                    _finding(
                        category="missing-audit-link",
                        source_path=rel_path,
                        confidence=0.86,
                        suggested_next_action="restore the referenced audit artifact or mark the task audit entry as superseded",
                        evidence=[{"summary": f"{task_id} references missing audit artifact {ref}", "confidence": 0.86}],
                        risk_tier="low",
                    )
                )


def _scan_reviews(root: Path, findings: list[dict[str, Any]]) -> None:
    reviews_dir = root / "reviews"
    if not reviews_dir.is_dir():
        return
    for path in sorted(reviews_dir.glob("*.md"))[:200]:
        text = _read(path)
        meta, _ = parse_frontmatter(text)
        rel_path = _rel(root, path)
        has_task_ref = bool(re.search(r"\bTASK-[A-Z0-9-]+\b", text))
        if not has_task_ref and not meta.get("task") and not meta.get("tasks"):
            findings.append(
                _finding(
                    category="orphaned-review",
                    source_path=rel_path,
                    confidence=0.61,
                    suggested_next_action="link the review to a task, release, proposal, or mark it as general research",
                    evidence=[{"summary": f"Review {rel_path} has no task reference", "confidence": 0.61}],
                    risk_tier="low",
                )
            )


def _parse_pyproject_version(text: str) -> str | None:
    match = re.search(r"(?m)^version\s*=\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else None


def _scan_release(root: Path, findings: list[dict[str, Any]]) -> None:
    pyproject = root / "pyproject.toml"
    package_version = _parse_pyproject_version(_read(pyproject)) if pyproject.exists() else None
    release_dir = root / "agents" / "project" / "release"
    if package_version and release_dir.is_dir():
        for path in sorted(release_dir.glob("*.yml")):
            text = _read(path)
            for match in re.finditer(r"(?m)^\s*(?:version|release_version)\s*:\s*v?([0-9]+\.[0-9]+\.[0-9]+)", text):
                release_version = match.group(1)
                if release_version != package_version:
                    findings.append(
                        _finding(
                            category="release-version-mismatch",
                            source_path=_rel(root, path),
                            confidence=0.9,
                            suggested_next_action="route through the release/version consistency steward before any publish action",
                            evidence=[
                                {"summary": f"package version is {package_version}", "confidence": 0.9},
                                {"summary": f"{_rel(root, path)} declares {release_version}", "confidence": 0.9},
                            ],
                            risk_tier="high",
                        )
                    )
    steward = root / "reviews" / "RELEASE-VERSION-CONSISTENCY-STEWARD.json"
    if steward.exists():
        try:
            payload = json.loads(_read(steward))
        except json.JSONDecodeError:
            payload = {"status": "block", "warnings": ["malformed steward report"]}
        status = str(payload.get("status") or "").lower()
        if status in {"watch", "block"}:
            findings.append(
                _finding(
                    category="release-version-consistency",
                    source_path=_rel(root, steward),
                    confidence=0.88,
                    suggested_next_action="keep C-mode promotion blocked until steward findings are pass",
                    evidence=[{"summary": f"release/version steward status is {status}", "confidence": 0.88}],
                    risk_tier="high" if status == "block" else "medium",
                )
            )


def _iter_jsonish_files(path: Path) -> list[Path]:
    if not path.is_dir():
        return []
    files: list[Path] = []
    for pattern in ("*.json", "*.jsonl", "*.ndjson"):
        files.extend(sorted(path.rglob(pattern)))
    return sorted(files)[:200]


def _scan_eval_trace(root: Path, findings: list[dict[str, Any]]) -> None:
    families = [
        root / "agents" / "project" / "evals",
        root / "agents" / "project" / "corrections",
        root / "agents" / "project" / "a2a",
        root / "traces",
    ]
    for family in families:
        for path in _iter_jsonish_files(family):
            text = _read(path)
            rel_path = _rel(root, path)
            lower = text.lower()
            trace_match = re.search(r'"(?:trace_id|contextId|taskId)"\s*:\s*"([^"]+)"', text)
            trace_id = trace_match.group(1) if trace_match else None
            if any(token in lower for token in ('"status": "failed"', '"status":"failed"', "regression", '"verdict": "block"')):
                findings.append(
                    _finding(
                        category="eval-trace-regression",
                        source_path=rel_path,
                        confidence=0.84,
                        suggested_next_action="create a planning proposal that links the failed trace/grader evidence to acceptance criteria",
                        evidence=[{"summary": f"failed or regressed trace evidence found in {rel_path}", "confidence": 0.84}],
                        risk_tier="medium",
                        trace_id=trace_id,
                    )
                )


def _scan_compounds(root: Path, findings: list[dict[str, Any]]) -> None:
    path = root / "agents" / "lead_engineer" / "compound_log.md"
    text = _read(path)
    if not text:
        return
    patterns = {
        "response-contract-drift": r"(?i)(BRIEF|response contract|wrong language|status vocabulary)",
        "continuity-gap": r"(?i)(continuity|next-session|repeated request|pointer)",
        "verification-overclaim": r"(?i)(overclaim|proxy signal|verification)",
    }
    for name, pattern in patterns.items():
        count = len(re.findall(pattern, text))
        if count >= 3:
            findings.append(
                _finding(
                    category="retro-compound-pattern",
                    source_path=_rel(root, path),
                    confidence=0.76,
                    suggested_next_action="create preventive work that turns the repeated correction into a gate, API, or runtime check",
                    evidence=[{"summary": f"{name} pattern appears {count} times in compound log", "confidence": 0.76}],
                    risk_tier="medium",
                )
            )


def scan(root: Path, *, trigger: str = "manual", now: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    sources = _scan_required_sources(root, findings)
    _scan_tasks(root, findings)
    _scan_reviews(root, findings)
    _scan_release(root, findings)
    _scan_eval_trace(root, findings)
    _scan_compounds(root, findings)
    unique_findings: dict[str, dict[str, Any]] = {}
    for finding in findings:
        unique_findings.setdefault(str(finding["id"]), finding)
    findings = sorted(unique_findings.values(), key=lambda item: (item["category"], item["source_path"], item["id"]))
    return {
        "id": _stable_id("SCAN", {"root": str(root.resolve()), "trigger": trigger, "findings": findings}),
        "generated_at": _now(now),
        "mode": "B",
        "trigger": trigger,
        "status": "pass" if not any(item["risk_tier"] == "high" for item in findings) else "watch",
        "sources": sources,
        "findings": findings,
        "summary": {
            "finding_count": len(findings),
            "proposal_allowed_count": sum(1 for item in findings if item.get("proposal_allowed")),
        },
    }


def _action_type(category: str) -> str:
    if category in {"missing-audit-link", "missing-source", "orphaned-review"}:
        return "doc_repair"
    if category in {"unresolved-hold-route"}:
        return "plan_update"
    if category in {"release-version-mismatch", "release-version-consistency"}:
        return "release_version_consistency"
    if category in {"eval-trace-regression"}:
        return "eval_expansion"
    if category in {"retro-compound-pattern"}:
        return "retro_compound_follow_up"
    return "watch_only"


def _owner_boundary(action_type: str, risk_tier: str) -> str:
    if risk_tier in {"high", "owner"} or action_type in HIGH_RISK_ACTIONS:
        return "Owner approval required before canonical mutation; proposal-only output is allowed."
    return "Low-risk local proposal; canonical mutation still requires approved apply."


def _default_verifiers(action_type: str) -> list[str]:
    verifiers = [
        "python scripts/planning_loop.py gate --trigger manual --json",
        "python scripts/owner_governance_gate.py",
    ]
    if action_type == "release_version_consistency":
        verifiers.insert(0, "python scripts/release_version_consistency_steward.py --out reviews/RELEASE-VERSION-CONSISTENCY-STEWARD.json")
    if action_type == "eval_expansion":
        verifiers.insert(0, "python scripts/planning_loop.py scan --trigger manual --json")
    return verifiers


def _risk_rank(risk_tier: str) -> int:
    return {"low": 1, "medium": 2, "high": 3, "owner": 4}.get(risk_tier, 2)


def _group_findings_for_proposals(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for finding in findings:
        if not finding.get("proposal_allowed"):
            continue
        action_type = _action_type(str(finding.get("category")))
        dedupe_key = f"{action_type}:{finding.get('category')}:{finding.get('source_path')}"
        group = grouped.setdefault(
            dedupe_key,
            {
                "action_type": action_type,
                "dedupe_key": dedupe_key,
                "category": finding.get("category"),
                "source_path": finding.get("source_path"),
                "confidence": 0.0,
                "risk_tier": "low",
                "trace_id": finding.get("trace_id"),
                "suggested_next_action": finding.get("suggested_next_action"),
                "evidence": [],
                "proposal_allowed": True,
            },
        )
        group["confidence"] = max(float(group.get("confidence") or 0), float(finding.get("confidence") or 0))
        if _risk_rank(str(finding.get("risk_tier") or "medium")) > _risk_rank(str(group.get("risk_tier") or "medium")):
            group["risk_tier"] = finding.get("risk_tier")
        if finding.get("trace_id") and not group.get("trace_id"):
            group["trace_id"] = finding.get("trace_id")
        if finding.get("suggested_next_action") and not group.get("suggested_next_action"):
            group["suggested_next_action"] = finding.get("suggested_next_action")
        for evidence in finding.get("evidence", []):
            if evidence not in group["evidence"]:
                group["evidence"].append(evidence)
    return sorted(grouped.values(), key=lambda item: str(item["dedupe_key"]))


def _draft_task(proposal: dict[str, Any]) -> str:
    task_id = proposal["id"].replace("PROP-", "DRAFT-TASK-")
    evidence = "\n".join(f"- {item.get('summary', '')}" for item in proposal.get("evidence", []))
    verifiers = "\n".join(f"- `{item}`" for item in proposal.get("verifier_list", []))
    targets = "\n".join(f"- `{item}`" for item in proposal.get("target_files", []))
    return "\n".join(
        [
            "---",
            f"id: {task_id}",
            "status: draft",
            "owner: planning-coordinator",
            "priority: P1",
            "tags:",
            "  - planning-loop",
            "  - proposal-draft",
            "audit_log:",
            f"  - agents/planning/outbox/{proposal['id']}.json",
            "---",
            "",
            f"# {proposal['title']}",
            "",
            "## Goal",
            "",
            proposal["suggested_next_action"],
            "",
            "## Completion Criteria",
            "",
            "- Source evidence is linked.",
            "- Verifier list passes before canonical closure.",
            "- Risk boundary and rollback path are preserved.",
            "",
            "## Source Evidence",
            "",
            evidence or "- No evidence.",
            "",
            "## Target Files",
            "",
            targets or "- None.",
            "",
            "## Verifier List",
            "",
            verifiers,
            "",
            "## Risk Boundary",
            "",
            proposal["owner_boundary"],
            "",
        ]
    )


def _load_existing_proposals(outbox: Path) -> dict[str, dict[str, Any]]:
    proposals: dict[str, dict[str, Any]] = {}
    if not outbox.is_dir():
        return proposals
    for path in sorted(outbox.glob("PROP-*.json")):
        try:
            payload = json.loads(_read(path))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and "dedupe_key" in payload:
            proposals[str(payload["dedupe_key"])] = payload
    return proposals


def create_proposals(
    root: Path,
    scan_payload: dict[str, Any],
    *,
    outbox: Path | None = None,
    draft_dir: Path | None = None,
    now: str | None = None,
) -> dict[str, Any]:
    outbox = outbox or root / "agents" / "planning" / "outbox"
    draft_dir = draft_dir or root / "agents" / "planning" / "drafts"
    existing = _load_existing_proposals(outbox)
    created: list[dict[str, Any]] = []
    deduped: list[dict[str, Any]] = []
    grouped_findings = _group_findings_for_proposals(list(scan_payload.get("findings", [])))
    for finding in grouped_findings:
        if len(created) >= MAX_PROPOSALS_PER_SCAN:
            break
        action_type = str(finding.get("action_type") or _action_type(str(finding.get("category"))))
        dedupe_key = str(finding.get("dedupe_key"))
        evidence_hash = _stable_hash(finding.get("evidence", []))
        previous = existing.get(dedupe_key)
        if previous and previous.get("evidence_hash") == evidence_hash:
            deduped.append({"id": previous.get("id"), "dedupe_key": dedupe_key, "reason": "same evidence"})
            continue
        proposal_core = {
            "action_type": action_type,
            "category": finding.get("category"),
            "source_path": finding.get("source_path"),
            "dedupe_key": dedupe_key,
            "evidence_hash": evidence_hash,
        }
        proposal_id = _stable_id("PROP", proposal_core)
        risk_tier = str(finding.get("risk_tier") or "medium")
        target_files = [str(finding.get("source_path"))] if finding.get("source_path") else []
        proposal: dict[str, Any] = {
            "id": proposal_id,
            "mode": "B",
            "status": "proposed",
            "action_type": action_type,
            "risk_tier": risk_tier,
            "title": f"{finding.get('category')}: {finding.get('source_path')}",
            "created_at": _now(now),
            "updated_at": _now(now),
            "trace_id": finding.get("trace_id"),
            "dedupe_key": dedupe_key,
            "evidence_hash": evidence_hash,
            "source_refs": [{"path": str(finding.get("source_path")), "kind": str(finding.get("category"))}],
            "evidence": list(finding.get("evidence", [])),
            "target_files": target_files,
            "rollback_path": f"agents/planning/rollback/{proposal_id}.json",
            "verifier_list": _default_verifiers(action_type),
            "owner_boundary": _owner_boundary(action_type, risk_tier),
            "department": _department_for_action(action_type),
            "reviewer_opinions": [],
            "suggested_next_action": str(finding.get("suggested_next_action") or ""),
            "supersedes": [previous["id"]] if previous and previous.get("id") else [],
        }
        draft_path = draft_dir / f"{proposal_id}.md"
        proposal["draft_task_path"] = _rel(root, draft_path)
        _write_json(outbox / f"{proposal_id}.json", proposal)
        draft_path.parent.mkdir(parents=True, exist_ok=True)
        draft_path.write_text(_draft_task(proposal), encoding="utf-8")
        created.append(proposal)
        existing[dedupe_key] = proposal
    return {
        "status": "pass",
        "created_count": len(created),
        "deduped_count": len(deduped),
        "created": created,
        "deduped": deduped,
    }


def _department_for_action(action_type: str) -> str:
    mapping = {
        "doc_repair": "planning-office",
        "plan_update": "planning-office",
        "eval_expansion": "evaluation-office",
        "release_version_consistency": "release-integrity",
        "retro_compound_follow_up": "rsi-lab",
        "c_mode_promotion": "risk-and-safety",
    }
    return mapping.get(action_type, "planning-office")


def planning_gate(
    root: Path,
    *,
    trigger: str = "manual",
    action: str = "scan",
    proposal_count: int = 0,
    owner_approved: bool = False,
) -> dict[str, Any]:
    reasons: list[str] = []
    warnings: list[str] = []
    if os.environ.get("AGENT_RUNTIME_RSI_DISABLE") in {"1", "true", "yes"}:
        reasons.append("kill switch AGENT_RUNTIME_RSI_DISABLE is enabled")
    if trigger not in ALLOWED_TRIGGERS:
        reasons.append(f"unsupported trigger: {trigger}")
    if trigger in PROPOSAL_ONLY_TRIGGERS and action not in {"scan", "propose"}:
        reasons.append(f"{trigger} trigger cannot perform canonical mutation")
    if proposal_count > MAX_PROPOSALS_PER_SCAN:
        reasons.append(f"proposal count {proposal_count} exceeds cap {MAX_PROPOSALS_PER_SCAN}")
    if action in {"apply", "c-mode"} and not owner_approved:
        warnings.append("apply and C-mode actions require approved proposal evidence")
    status = "block" if reasons else ("watch" if warnings else "pass")
    return {
        "status": status,
        "score": 100 if status == "pass" else (70 if status == "watch" else 0),
        "trigger": trigger,
        "action": action,
        "proposal_count": proposal_count,
        "reasons": reasons,
        "warnings": warnings,
        "policy": "agents/project/PLANNING-GUARDRAILS.yml",
    }


def _load_proposal(root: Path, proposal_id: str) -> tuple[Path, dict[str, Any]]:
    path = root / "agents" / "planning" / "outbox" / f"{proposal_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"proposal not found: {proposal_id}")
    return path, json.loads(_read(path))


def _approval_allows(proposal: dict[str, Any], approval_file: Path | None) -> bool:
    if proposal.get("status") == "approved":
        return True
    if not approval_file:
        return False
    try:
        payload = json.loads(_read(approval_file))
    except json.JSONDecodeError:
        return False
    return payload.get("proposal_id") == proposal.get("id") and payload.get("approved") is True


def apply_proposal(root: Path, proposal_id: str, *, approval_file: Path | None = None, dry_run: bool = False) -> dict[str, Any]:
    path, proposal = _load_proposal(root, proposal_id)
    if not _approval_allows(proposal, approval_file):
        return {"status": "block", "reasons": ["proposal is not approved"]}
    if proposal.get("risk_tier") in {"high", "owner"} and not approval_file:
        return {"status": "block", "reasons": ["high-risk proposal requires explicit owner approval file"]}
    if not proposal.get("rollback_path") or not proposal.get("verifier_list"):
        return {"status": "block", "reasons": ["rollback path and verifier list are required"]}
    gate = planning_gate(root, trigger="manual", action="apply", proposal_count=1, owner_approved=True)
    if gate["status"] == "block":
        return gate

    changed: list[str] = []
    if proposal.get("action_type") == "new_task":
        draft_path = root / str(proposal.get("draft_task_path") or "")
        if not draft_path.exists():
            return {"status": "block", "reasons": ["draft task path is missing"]}
        target = root / "agents" / "lead_engineer" / "tasks" / draft_path.name
        if target.exists():
            return {"status": "block", "reasons": [f"target task already exists: {_rel(root, target)}"]}
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(draft_path, target)
            changed.append(_rel(root, target))
    else:
        return {
            "status": "block",
            "reasons": ["only approved new_task proposals have an implemented canonical mutator"],
        }

    audit = {
        "proposal_id": proposal_id,
        "status": "applied" if not dry_run else "dry_run",
        "changed": changed,
        "rollback_path": proposal["rollback_path"],
        "verifier_list": proposal["verifier_list"],
    }
    audit_path = root / "agents" / "planning" / "applied" / f"APPLY-{proposal_id}.json"
    if not dry_run:
        proposal["status"] = "applied"
        proposal["apply"] = audit
        _write_json(path, proposal)
        _write_json(audit_path, audit)
    return {"status": audit["status"], "changed": changed, "audit_path": _rel(root, audit_path)}


def retro_report(root: Path, *, now: str | None = None) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    _scan_compounds(root, findings)
    return {
        "id": _stable_id("RETRO", findings),
        "generated_at": _now(now),
        "status": "watch" if findings else "pass",
        "findings": findings,
        "minority_concerns_preserved": True,
        "proposal_route": "retro_compound_follow_up",
    }


def c_mode_gate(root: Path) -> dict[str, Any]:
    cycles_dir = root / "agents" / "planning" / "cycles"
    pass_cycles = 0
    if cycles_dir.is_dir():
        for path in sorted(cycles_dir.glob("*.json")):
            try:
                payload = json.loads(_read(path))
            except json.JSONDecodeError:
                continue
            if payload.get("mode") == "B" and payload.get("status") == "pass":
                pass_cycles += 1
    steward = root / "reviews" / "RELEASE-VERSION-CONSISTENCY-STEWARD.json"
    steward_status = "missing"
    if steward.exists():
        try:
            steward_status = str(json.loads(_read(steward)).get("status") or "missing")
        except json.JSONDecodeError:
            steward_status = "block"
    reasons: list[str] = []
    if pass_cycles < 3:
        reasons.append("at least three passing B-mode cycles are required")
    if steward_status != "pass":
        reasons.append(f"release/version steward status must be pass, got {steward_status}")
    status = "pass" if not reasons else "block"
    return {
        "status": status,
        "score": 100 if status == "pass" else 0,
        "pass_cycles": pass_cycles,
        "steward_status": steward_status,
        "reasons": reasons,
        "checklist": "agents/project/C-MODE-PROMOTION-CHECKLIST.md",
    }


def dedupe_outbox(root: Path, *, apply: bool = False, now: str | None = None) -> dict[str, Any]:
    outbox = root / "agents" / "planning" / "outbox"
    if not outbox.is_dir():
        return {"status": "pass", "dedupe_groups": [], "changed": [], "mode": "dry_run" if not apply else "apply"}
    groups: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path in sorted(outbox.glob("PROP-*.json")):
        try:
            payload = json.loads(_read(path))
        except json.JSONDecodeError:
            continue
        dedupe_key = str(payload.get("dedupe_key") or "")
        if dedupe_key:
            groups.setdefault(dedupe_key, []).append((path, payload))

    changed: list[str] = []
    dedupe_groups: list[dict[str, Any]] = []
    for dedupe_key, records in sorted(groups.items()):
        if len(records) < 2:
            continue
        superseded_ids = {
            str(item)
            for _, payload in records
            for item in payload.get("supersedes", [])
            if item
        }
        live = [payload for _, payload in records if payload.get("id") not in superseded_ids]
        keep_id = str((live[-1] if live else records[-1][1]).get("id"))
        group_changed: list[str] = []
        for path, payload in records:
            if payload.get("id") == keep_id:
                continue
            if payload.get("status") == "superseded" and payload.get("superseded_by") == keep_id:
                continue
            payload["status"] = "superseded"
            payload["superseded_by"] = keep_id
            payload["updated_at"] = _now(now)
            group_changed.append(_rel(root, path))
            if apply:
                _write_json(path, payload)
        if group_changed:
            changed.extend(group_changed)
            dedupe_groups.append({"dedupe_key": dedupe_key, "keep": keep_id, "superseded": group_changed})
    return {
        "status": "pass",
        "mode": "apply" if apply else "dry_run",
        "dedupe_groups": dedupe_groups,
        "changed": changed,
    }


def _load_scan(root: Path, scan_path: Path | None, trigger: str, now: str | None) -> dict[str, Any]:
    if scan_path:
        return json.loads(_read(scan_path))
    return scan(root, trigger=trigger, now=now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded RSI planning loop")
    parser.add_argument("--root", default=str(ROOT))
    sub = parser.add_subparsers(dest="command", required=True)

    scan_p = sub.add_parser("scan")
    scan_p.add_argument("--trigger", default="manual")
    scan_p.add_argument("--out")
    scan_p.add_argument("--now")
    scan_p.add_argument("--json", action="store_true")

    propose_p = sub.add_parser("propose")
    propose_p.add_argument("--scan")
    propose_p.add_argument("--trigger", default="manual")
    propose_p.add_argument("--outbox")
    propose_p.add_argument("--draft-dir")
    propose_p.add_argument("--now")
    propose_p.add_argument("--json", action="store_true")

    gate_p = sub.add_parser("gate")
    gate_p.add_argument("--trigger", default="manual")
    gate_p.add_argument("--action", default="scan")
    gate_p.add_argument("--proposal-count", type=int, default=0)
    gate_p.add_argument("--owner-approved", action="store_true")
    gate_p.add_argument("--json", action="store_true")

    apply_p = sub.add_parser("apply")
    apply_p.add_argument("--proposal-id", required=True)
    apply_p.add_argument("--approval-file")
    apply_p.add_argument("--dry-run", action="store_true")
    apply_p.add_argument("--json", action="store_true")

    retro_p = sub.add_parser("retro")
    retro_p.add_argument("--out")
    retro_p.add_argument("--now")
    retro_p.add_argument("--json", action="store_true")

    cmode_p = sub.add_parser("c-mode-gate")
    cmode_p.add_argument("--json", action="store_true")

    dedupe_p = sub.add_parser("dedupe-outbox")
    dedupe_p.add_argument("--apply", action="store_true")
    dedupe_p.add_argument("--now")
    dedupe_p.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    if args.command == "scan":
        payload = scan(root, trigger=args.trigger, now=args.now)
        if args.out:
            _write_json(root / args.out, payload)
    elif args.command == "propose":
        scan_payload = _load_scan(root, (root / args.scan) if args.scan else None, args.trigger, args.now)
        payload = create_proposals(
            root,
            scan_payload,
            outbox=Path(args.outbox) if args.outbox else None,
            draft_dir=Path(args.draft_dir) if args.draft_dir else None,
            now=args.now,
        )
    elif args.command == "gate":
        payload = planning_gate(
            root,
            trigger=args.trigger,
            action=args.action,
            proposal_count=args.proposal_count,
            owner_approved=args.owner_approved,
        )
    elif args.command == "apply":
        payload = apply_proposal(
            root,
            args.proposal_id,
            approval_file=Path(args.approval_file) if args.approval_file else None,
            dry_run=args.dry_run,
        )
    elif args.command == "retro":
        payload = retro_report(root, now=args.now)
        if args.out:
            _write_json(root / args.out, payload)
    elif args.command == "c-mode-gate":
        payload = c_mode_gate(root)
    else:
        payload = dedupe_outbox(root, apply=args.apply, now=args.now)

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"status={payload.get('status', 'pass')}")
    return 0 if payload.get("status") != "block" else 1


if __name__ == "__main__":
    raise SystemExit(main())
