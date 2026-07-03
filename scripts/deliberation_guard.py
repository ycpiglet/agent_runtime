"""Safety guard for deliberation runs (GH #132 preconditions 2 + 3, upstream).

The deliberation devices (persona_council, agent_seminar) are pure prompt/
measurement libraries; the risk arrives with whoever schedules them. This
guard is the mandatory pass-through for that invocation layer, shipped BEFORE
any always-on mode exists so the off-switch precedes the engine:

- kill switch: env ``AGENT_RUNTIME_DELIBERATION_DISABLE`` blocks every run.
- throttle: minimum interval between runs + hard daily ceiling, enforced via
  an append-only run ledger (``agents/runtime/deliberation-runs.jsonl``).
- cost cap: per-run persona and estimated-token ceilings.
- output contract: deliberation output is advisory only — a declared output
  must carry ``mutation: none`` and none of the forbidden side-effect fields
  (apply/execute/push/tag/order/trade). Order/trade/risk surfaces stay with
  the host's human layer (R3).

Fail-closed: a missing or unreadable guardrails file blocks the run.
Boundary: watch-only tool; not wired into the owner governance chain. A
future daemon MUST call ``check_run`` before and ``record_run`` after each
deliberation; ``--check`` offers the same decision from the CLI.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import yaml

DEFAULT_POLICY = Path("agents/project/DELIBERATION-GUARDRAILS.yml")


def load_policy(root: Path) -> dict[str, Any] | None:
    path = root / DEFAULT_POLICY
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return payload if isinstance(payload, dict) else None


def _ledger_path(root: Path, policy: dict[str, Any]) -> Path:
    return root / str(policy.get("run_ledger") or "agents/runtime/deliberation-runs.jsonl")


def _load_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def check_run(
    root: Path,
    *,
    personas: int = 0,
    est_tokens: int = 0,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Decide whether a deliberation run may start. Fail-closed."""
    now = now_ts if now_ts is not None else time.time()
    reasons: list[str] = []
    policy = load_policy(root)
    if policy is None:
        return {
            "allowed": False,
            "reasons": [f"guardrails file missing or unreadable: {DEFAULT_POLICY.as_posix()} (fail closed)"],
        }

    kill_env = str(policy.get("kill_switch_env") or "AGENT_RUNTIME_DELIBERATION_DISABLE")
    if os.environ.get(kill_env, "").strip().lower() in {"1", "true", "yes"}:
        reasons.append(f"kill switch {kill_env} is enabled")

    limits = policy.get("limits") or {}
    max_personas = int(limits.get("max_personas_per_run") or 0)
    if max_personas and personas > max_personas:
        reasons.append(f"personas {personas} exceeds max_personas_per_run {max_personas}")
    max_tokens = int(limits.get("max_est_tokens_per_run") or 0)
    if max_tokens and est_tokens > max_tokens:
        reasons.append(f"est_tokens {est_tokens} exceeds max_est_tokens_per_run {max_tokens}")

    ledger = _load_ledger(_ledger_path(root, policy))
    timestamps = sorted(float(e.get("ts", 0)) for e in ledger if e.get("ts"))
    min_interval = float(limits.get("min_interval_minutes") or 0) * 60
    if timestamps and min_interval and (now - timestamps[-1]) < min_interval:
        wait = int((min_interval - (now - timestamps[-1])) // 60) + 1
        reasons.append(f"last run was {int((now - timestamps[-1]) // 60)}m ago; min interval is {int(min_interval // 60)}m (wait ~{wait}m)")
    max_daily = int(limits.get("max_runs_per_day") or 0)
    if max_daily:
        day_ago = now - 86400
        recent = sum(1 for ts in timestamps if ts >= day_ago)
        if recent >= max_daily:
            reasons.append(f"{recent} runs in the last 24h reaches max_runs_per_day {max_daily}")

    return {"allowed": not reasons, "reasons": reasons}


def validate_output(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Enforce the advisory-only output contract on a deliberation record."""
    policy = load_policy(root)
    if policy is None:
        return {"valid": False, "violations": ["guardrails file missing or unreadable (fail closed)"]}
    contract = policy.get("output_contract") or {}
    violations: list[str] = []
    required_mutation = str(contract.get("mutation") or "none")
    if str(record.get("mutation", "")).strip().lower() != required_mutation:
        violations.append(f"output must declare mutation: {required_mutation}")
    for field in contract.get("forbidden_fields") or []:
        if field in record:
            violations.append(f"forbidden side-effect field present: {field}")
    return {"valid": not violations, "violations": violations}


def record_run(root: Path, *, personas: int, est_tokens: int, topic: str = "", now_ts: float | None = None) -> Path:
    policy = load_policy(root) or {}
    path = _ledger_path(root, policy)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "schema": "agent-runtime-deliberation-run/v1",
        "ts": now_ts if now_ts is not None else time.time(),
        "personas": personas,
        "est_tokens": est_tokens,
        "topic": topic,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deliberation run guard (kill switch, throttle, cost cap, output contract)")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--personas", type=int, default=0)
    parser.add_argument("--est-tokens", type=int, default=0)
    parser.add_argument("--record", action="store_true", help="append an allowed run to the ledger")
    parser.add_argument("--topic", default="")
    parser.add_argument("--check", action="store_true", help="exit 1 when the run is blocked")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    decision = check_run(root, personas=args.personas, est_tokens=args.est_tokens)
    print(f"deliberation-guard: {'allowed' if decision['allowed'] else 'blocked'}")
    for reason in decision["reasons"]:
        print(f"- {reason}")
    if decision["allowed"] and args.record:
        ledger = record_run(root, personas=args.personas, est_tokens=args.est_tokens, topic=args.topic)
        print(f"recorded={ledger}")
    return 1 if args.check and not decision["allowed"] else 0


if __name__ == "__main__":
    sys.exit(main())
