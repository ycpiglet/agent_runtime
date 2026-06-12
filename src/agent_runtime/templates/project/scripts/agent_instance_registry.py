"""Record live agent instance identity from task claim records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-agent-instance/v1"
INSTANCES_DIR = Path("agents/runtime/instances")


class AgentInstanceRegistryError(RuntimeError):
    def __init__(self, findings: list[str]):
        super().__init__("agent instance registry failed")
        self.findings = findings


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _safe_filename(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.@-]+", "-", value.strip())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "unknown-instance"


def instance_path(root: Path, agent_instance_id: str) -> Path:
    return root / INSTANCES_DIR / f"{_safe_filename(agent_instance_id)}.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AgentInstanceRegistryError([f"{path.as_posix()}: agent-instance:invalid-json:{exc}"]) from exc
    if not isinstance(payload, dict):
        raise AgentInstanceRegistryError([f"{path.as_posix()}: agent-instance:invalid-record"])
    return payload


def _claim_ref(root: Path, claim_path: Path | None, claim: dict[str, Any]) -> str:
    if claim_path is not None:
        return _rel(root, claim_path)
    claim_id = str(claim.get("claim_id") or "").strip()
    return (Path("agents/runtime/task_claims") / f"{claim_id}.json").as_posix() if claim_id else ""


def _skill_versions(value: Any) -> dict[str, str]:
    if isinstance(value, dict):
        return {str(key): str(item) for key, item in value.items()}
    return {}


def build_instance_record(
    root: Path,
    claim: dict[str, Any],
    *,
    claim_path: Path | None = None,
    spawned_by: str = "task_claim_dispatcher",
) -> dict[str, Any]:
    agent_instance_id = str(claim.get("agent_instance_id") or "").strip()
    if not agent_instance_id:
        raise AgentInstanceRegistryError(["agent-instance:claim-missing:agent_instance_id"])
    claimed_at = str(claim.get("claimed_at") or claim.get("updated_at") or "").strip()
    claim_ref = _claim_ref(root, claim_path, claim)
    return {
        "schema": SCHEMA,
        "agent_instance_id": agent_instance_id,
        "role": str(claim.get("agent_role") or "").strip(),
        "team_id": str(claim.get("team_id") or "").strip(),
        "callsign": str(claim.get("display_name") or "").strip(),
        "display_name": str(claim.get("display_name") or "").strip(),
        "callsite_id": str(claim.get("callsite_id") or "").strip(),
        "pane_id": str(claim.get("pane_id") or "").strip(),
        "spawned_at": claimed_at,
        "spawned_by": spawned_by,
        "session_id": str(claim.get("session_id") or "").strip(),
        "workspace": str(claim.get("workspace") or "").strip(),
        "worktree_path": str(claim.get("worktree_path") or "").strip(),
        "provider": str(claim.get("provider") or "").strip(),
        "model": str(claim.get("model") or "").strip(),
        "model_tier": str(claim.get("model_tier") or "").strip(),
        "skill_versions": _skill_versions(claim.get("skill_versions")),
        "prompt_config_hash": str(claim.get("prompt_config_hash") or "").strip(),
        "parent_instance_id": str(claim.get("parent_instance_id") or "").strip(),
        "on_behalf_of": str(claim.get("on_behalf_of") or claim.get("unit_id") or claim.get("task_id") or "").strip(),
        "decision_cycle_id": str(claim.get("decision_cycle_id") or "").strip(),
        "task_id": str(claim.get("task_id") or "").strip(),
        "task_set_id": str(claim.get("task_set_id") or "").strip(),
        "project_id": str(claim.get("project_id") or "").strip(),
        "unit_id": str(claim.get("unit_id") or "").strip(),
        "unit_spec": str(claim.get("unit_spec") or "").strip(),
        "claim_refs": [claim_ref] if claim_ref else [],
        "created_at": claimed_at,
        "updated_at": claimed_at,
    }


def _merge_existing(
    root: Path,
    path: Path,
    existing: dict[str, Any],
    fresh: dict[str, Any],
) -> dict[str, Any]:
    if str(existing.get("schema") or "") != SCHEMA:
        raise AgentInstanceRegistryError([f"{_rel(root, path)}: agent-instance:invalid-schema"])
    immutable_fields = (
        "agent_instance_id",
        "role",
        "team_id",
        "display_name",
        "callsite_id",
        "pane_id",
        "worktree_path",
    )
    findings: list[str] = []
    for field in immutable_fields:
        if str(existing.get(field) or "") != str(fresh.get(field) or ""):
            findings.append(f"{_rel(root, path)}: agent-instance:field-conflict:{field}")
    if findings:
        raise AgentInstanceRegistryError(findings)
    refs = [str(item) for item in existing.get("claim_refs", []) if str(item).strip()]
    for ref in fresh.get("claim_refs", []):
        if ref and ref not in refs:
            refs.append(ref)
    existing["claim_refs"] = refs
    existing["updated_at"] = fresh.get("updated_at") or existing.get("updated_at")
    return existing


def record_claim_instance(
    root: Path,
    claim: dict[str, Any],
    *,
    claim_path: Path | None = None,
    spawned_by: str = "task_claim_dispatcher",
) -> tuple[Path, dict[str, Any]]:
    root = root.resolve()
    fresh = build_instance_record(root, claim, claim_path=claim_path, spawned_by=spawned_by)
    path = instance_path(root, str(fresh["agent_instance_id"]))
    if path.exists():
        payload = _merge_existing(root, path, _read_json(path), fresh)
    else:
        payload = fresh
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, payload


def cmd_record(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    claim_path = args.claim if args.claim.is_absolute() else root / args.claim
    try:
        claim = _read_json(claim_path)
        path, payload = record_claim_instance(root, claim, claim_path=claim_path, spawned_by=args.spawned_by)
    except AgentInstanceRegistryError as exc:
        print("agent-instance-registry: fail", file=sys.stderr)
        print(f"findings={len(exc.findings)}", file=sys.stderr)
        for finding in exc.findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    result = {
        "status": "recorded",
        "path": _rel(root, path),
        "agent_instance_id": payload["agent_instance_id"],
        "claim_refs": payload.get("claim_refs", []),
    }
    print("agent-instance-registry: recorded")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for key, value in result.items():
            print(f"{key}={value}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record agent instance identity from claim records")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record", help="Record or update an instance record from a claim JSON file")
    record.add_argument("--claim", type=Path, required=True)
    record.add_argument("--spawned-by", default="task_claim_dispatcher")
    record.add_argument("--json", action="store_true")
    record.set_defaults(func=cmd_record)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
