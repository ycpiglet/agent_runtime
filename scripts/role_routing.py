"""Flag-gated routing of work to dormant review/council/scout roles + beta activation.

WHY THIS EXISTS (2026-06-22 audit): the live dispatch loop centralizes on
lead-engineer (~76% of claims) and never exercises the council / skeptic /
progress-scout review paths; the beta_tester role is dormant (BTC output 0).
This module builds the capability to operationalize those dormant roles.

SAFETY CONTRACT (CRITICAL): other instances of this autonomous system run LIVE
in the same repo concurrently. Every behavior here that changes *who gets work*
is FLAG-GATED and DEFAULT-OFF, so merging this module is INERT until the Owner
flips a flag. The flags are independent kill-switches:

  * AR_ROLE_ROUTING    -> route_review_pass(): on a high-risk event (merge/
                          closeout), CREATE an ADDITIVE review claim for a review
                          role (skeptic / independent-auditor) as a PARALLEL
                          pass. It never removes or mutates the lead-engineer
                          claim — the review runs alongside it.
  * AR_SCOUT_COUNCIL   -> dispatch_wave_hooks(): per wave, dispatch a
                          progress-scout sweep; at the W6 boundary, additionally
                          dispatch a council deliberation.
  * AR_BETA_ACTIVATION -> maybe_activate_beta(): when beta_tester_due reports
                          due/overdue, emit a beta_tester claim + a BTC-*
                          scaffold so the dormant beta role actually runs.

Additive claims are written DIRECTLY here (not through task_claim_dispatcher),
because they are orchestration-overlay claims: they carry no worktree, must not
collide with the worker's task_id, and must not trip the dispatcher's
"one active claim per task_id/task_set" refusal against the live lead claim.
Each additive claim uses a deterministic claim_id so re-dispatch is idempotent.

With every flag OFF the public functions create NOTHING and return
``{"enabled": False, "created": []}`` — proven inert by tests/test_role_routing.py.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import atomic_io
from pane_event_log import append_event


SCHEMA = "agent-runtime-task-claim/v1"

ROLE_ROUTING_FLAG = "AR_ROLE_ROUTING"
SCOUT_COUNCIL_FLAG = "AR_SCOUT_COUNCIL"
BETA_ACTIVATION_FLAG = "AR_BETA_ACTIVATION"

# Routing labels for the additive overlay claims. These are intentionally the
# audit's role names (skeptic / progress-scout / council / beta-tester); they
# are written verbatim onto the claim's agent_role so dashboards can attribute
# the parallel pass. They do not need to resolve through ORG-MODEL because these
# claims are orchestration overlays, not gated worker claims.
DEFAULT_REVIEW_ROLE = "independent-auditor"
SKEPTIC_ROLE = "skeptic"
SCOUT_ROLE = "progress-scout"
COUNCIL_ROLE = "council"
BETA_ROLE = "beta-tester"


def _truthy(value: str | None, default: bool) -> bool:
    """House-style flag reader (matches scripts/claim_reaper_hook.py)."""
    if value is None or value == "":
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def role_routing_enabled() -> bool:
    return _truthy(os.environ.get(ROLE_ROUTING_FLAG), False)


def scout_council_enabled() -> bool:
    return _truthy(os.environ.get(SCOUT_COUNCIL_FLAG), False)


def beta_activation_enabled() -> bool:
    return _truthy(os.environ.get(BETA_ACTIVATION_FLAG), False)


ROUTING_CONFIG = "agents/project/role-routing.json"


def _config_enabled(root: Path, key: str) -> bool | None:
    """Config-driven gate: read ``agents/project/role-routing.json`` and return
    the bool for ``key``. Returns None (file missing / bad JSON / key absent /
    non-bool) so the caller falls back to the env flag. This lets the autonomous
    dispatch loop activate routing from committed config without depending on the
    process env reaching it (the env path stays as an override/fallback)."""
    try:
        data = json.loads((root / ROUTING_CONFIG).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = data.get(key) if isinstance(data, dict) else None
    return value if isinstance(value, bool) else None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _now_iso(now: str | None) -> str:
    if now:
        return now
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _claim_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _claim_path(root: Path, claim_id: str) -> Path:
    return _claim_dir(root) / f"{claim_id}.json"


def _write_overlay_claim(
    root: Path,
    *,
    claim_id: str,
    task_id: str,
    agent_role: str,
    mode: str,
    status_text: str,
    now: str,
    task_set_id: str = "",
    tags: list[str] | None = None,
    parent_task_id: str = "",
    parent_task_set_id: str = "",
    event_name: str = "",
) -> dict[str, Any] | None:
    """Write one additive overlay claim, idempotently.

    Returns the claim dict if newly created, or ``None`` if a claim with this
    deterministic ``claim_id`` already exists (re-dispatch is a no-op). The
    claim carries NO worktree_path on purpose: it is an orchestration overlay,
    not a worker checkout, so it never trips worktree-readiness gates and never
    competes with the live worker claim for a worktree.
    """
    path = _claim_path(root, claim_id)
    if path.exists():
        return None
    claim: dict[str, Any] = {
        "schema": SCHEMA,
        "claim_id": claim_id,
        "task_id": task_id,
        "task_set_id": task_set_id,
        "active_scope": task_set_id,
        "agent_role": agent_role,
        "team_id": "agent-runtime-core",
        "agent_instance_id": f"{agent_role}-{claim_id}",
        "display_name": f"{agent_role}@{mode}",
        "mode": mode,
        "status": "claimed",
        "status_text": status_text,
        "claimed_at": now,
        "last_heartbeat": now,
        "updated_at": now,
        "tags": list(tags or []),
        "overlay": True,            # additive orchestration overlay marker
        "parent_task_id": parent_task_id,
        "parent_task_set_id": parent_task_set_id,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_io.write_json_atomic(path, claim)
    if event_name:
        append_event(
            root,
            {
                "event": event_name,
                "actor": claim["agent_instance_id"],
                "actor_role": agent_role,
                "agent_instance_id": claim["agent_instance_id"],
                "display_name": claim["display_name"],
                "task_id": parent_task_id or task_id,
                "task_set_id": parent_task_set_id or task_set_id,
                "claim_id": claim_id,
                "message": status_text,
                "ts": now,
            },
        )
    return claim


def _slug(value: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in str(value)).strip("-") or "item"


# ---------------------------------------------------------------------------
# 1. Review-role routing (additive parallel review pass)
# ---------------------------------------------------------------------------


def route_review_pass(
    root: Path,
    *,
    task_id: str,
    task_set_id: str = "",
    event: str = "merge",
    review_role: str = DEFAULT_REVIEW_ROLE,
    now: str | None = None,
) -> dict[str, Any]:
    """On a high-risk event (merge/closeout) create an ADDITIVE review claim.

    Default-off behind ``AR_ROLE_ROUTING``. When off, nothing is created and the
    live lead-engineer claim is left untouched (inert). When on, a parallel
    review pass is dispatched for ``review_role`` against a DISTINCT, additive
    task id (``REVIEW-<task>-<role>``) so it never collides with or removes the
    worker's claim — the lead keeps working while the reviewer runs in parallel.
    """
    root = root.resolve()
    enabled = _config_enabled(root, "role_routing")
    if enabled is None:
        enabled = role_routing_enabled()
    if not enabled:
        return {"enabled": False, "created": []}

    now = _now_iso(now)
    review_task = f"REVIEW-{task_id}-{_slug(review_role)}"
    claim_id = f"CLAIM-REVIEW-{_slug(task_id)}-{_slug(review_role)}-{_slug(event)}"
    claim = _write_overlay_claim(
        root,
        claim_id=claim_id,
        task_id=review_task,
        agent_role=review_role,
        mode="review",
        status_text=f"Additive {review_role} review pass for {task_id} ({event})",
        now=now,
        task_set_id=task_set_id,
        tags=["review", "additive", f"review-trigger:{event}"],
        parent_task_id=task_id,
        parent_task_set_id=task_set_id,
        event_name="review_pass_dispatched",
    )
    return {"enabled": True, "created": [claim] if claim else []}


# ---------------------------------------------------------------------------
# 2. progress-scout per wave + council at W6
# ---------------------------------------------------------------------------


def dispatch_wave_hooks(
    root: Path,
    *,
    task_set_id: str,
    wave_no: int,
    is_w6: bool = False,
    now: str | None = None,
) -> dict[str, Any]:
    """Per-wave progress-scout sweep + W6-boundary council deliberation.

    Default-off behind ``AR_SCOUT_COUNCIL``. When off, nothing is created. When
    on: every wave gets a progress-scout sweep claim; only at the W6 boundary
    (``is_w6=True``) is a council deliberation additionally dispatched.
    """
    root = root.resolve()
    enabled = _config_enabled(root, "scout_council")
    if enabled is None:
        enabled = scout_council_enabled()
    if not enabled:
        return {"enabled": False, "created": []}

    now = _now_iso(now)
    created: list[dict[str, Any]] = []

    scout = _write_overlay_claim(
        root,
        claim_id=f"CLAIM-SCOUT-{_slug(task_set_id)}-W{wave_no}",
        task_id=f"SCOUT-{task_set_id}-W{wave_no}",
        agent_role=SCOUT_ROLE,
        mode="scout-sweep",
        status_text=f"Progress-scout sweep for {task_set_id} wave {wave_no}",
        now=now,
        task_set_id=task_set_id,
        tags=["scout", "sweep", f"wave:{wave_no}"],
        parent_task_set_id=task_set_id,
        event_name="progress_scout_sweep",
    )
    if scout:
        created.append(scout)

    if is_w6:
        council = _write_overlay_claim(
            root,
            claim_id=f"CLAIM-COUNCIL-{_slug(task_set_id)}-W6",
            task_id=f"COUNCIL-{task_set_id}-W6",
            agent_role=COUNCIL_ROLE,
            mode="deliberation",
            status_text=f"Council deliberation at W6 boundary for {task_set_id}",
            now=now,
            task_set_id=task_set_id,
            tags=["council", "deliberation", "w6"],
            parent_task_set_id=task_set_id,
            event_name="council_deliberation",
        )
        if council:
            created.append(council)

    return {"enabled": True, "created": created}


# ---------------------------------------------------------------------------
# 3. beta activation
# ---------------------------------------------------------------------------


def _btc_dir(root: Path) -> Path:
    return root / "agents" / "beta_tester" / "test_cases"


def maybe_activate_beta(
    root: Path,
    *,
    due_state: str,
    cycle: int,
    now: str | None = None,
) -> dict[str, Any]:
    """Emit a beta exploration round when due/overdue AND the flag is on.

    Default-off behind ``AR_BETA_ACTIVATION``. ``due_state`` is the verdict from
    scripts/beta_tester_due.py ("ok" | "due" | "overdue"); only "due"/"overdue"
    trigger a round. When triggered: a beta_tester claim is emitted and a BTC-*
    scaffold is written under agents/beta_tester/test_cases/. Idempotent per
    cycle (the BTC scaffold + claim_id are keyed on the cycle number).
    """
    root = root.resolve()
    due = str(due_state or "").strip().lower() in {"due", "overdue"}
    enabled = _config_enabled(root, "beta_activation")
    if enabled is None:
        enabled = beta_activation_enabled()
    if not enabled:
        return {"enabled": False, "due": due, "created": []}
    if not due:
        return {"enabled": True, "due": False, "created": []}

    now = _now_iso(now)
    cycle_tag = f"CYCLE-{int(cycle):03d}"
    claim = _write_overlay_claim(
        root,
        claim_id=f"CLAIM-BETA-{cycle_tag}",
        task_id=f"BETA-ROUND-{cycle_tag}",
        agent_role=BETA_ROLE,
        mode="beta-round",
        status_text=f"Beta exploration round for {cycle_tag} ({due_state})",
        now=now,
        tags=["beta", "exploration", cycle_tag.lower()],
        event_name="beta_round_dispatched",
    )

    btc_path = _btc_dir(root) / f"BTC-{cycle_tag}-001.md"
    if not btc_path.exists():
        btc_path.parent.mkdir(parents=True, exist_ok=True)
        btc_path.write_text(
            "\n".join(
                [
                    f"# BTC-{cycle_tag}-001",
                    "",
                    f"- 라운드: {cycle_tag}",
                    f"- dispatched_at: {now}",
                    f"- due_state: {due_state}",
                    "- status: open",
                    "",
                    "## 탐색 시나리오",
                    "- (작성: agents/beta_tester/SKILL.md §탐색 시나리오)",
                    "",
                    "## 발견 케이스",
                    "- (발견 시 QA가 BUG 리포트로 변환: CLAUDE.md §Beta->QA 흐름)",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return {"enabled": True, "due": True, "created": [claim] if claim else []}


# ---------------------------------------------------------------------------
# CLI (advisory / manual trigger; still flag-gated)
# ---------------------------------------------------------------------------


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"role-routing: enabled={payload.get('enabled')} created={len(payload.get('created') or [])}")
    for claim in payload.get("created") or []:
        print(f"- {claim['agent_role']} claim {claim['claim_id']} ({claim['mode']})")


def cmd_review(args: argparse.Namespace) -> int:
    payload = route_review_pass(
        args.root, task_id=args.task_id, task_set_id=args.task_set_id,
        event=args.event, review_role=args.review_role, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 0


def cmd_wave(args: argparse.Namespace) -> int:
    payload = dispatch_wave_hooks(
        args.root, task_set_id=args.task_set_id, wave_no=args.wave_no,
        is_w6=args.w6, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 0


def cmd_beta(args: argparse.Namespace) -> int:
    payload = maybe_activate_beta(
        args.root, due_state=args.due_state, cycle=args.cycle, now=args.now,
    )
    _emit(payload, as_json=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Flag-gated routing to dormant review/council/scout roles + beta "
            "activation. All subcommands are DEFAULT-OFF: set AR_ROLE_ROUTING / "
            "AR_SCOUT_COUNCIL / AR_BETA_ACTIVATION to enable."
        )
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)

    review = sub.add_parser("review", help="Additive review pass (AR_ROLE_ROUTING)")
    review.add_argument("--task-id", required=True)
    review.add_argument("--task-set-id", default="")
    review.add_argument("--event", default="merge")
    review.add_argument("--review-role", default=DEFAULT_REVIEW_ROLE)
    review.add_argument("--now")
    review.add_argument("--json", action="store_true")
    review.set_defaults(func=cmd_review)

    wave = sub.add_parser("wave", help="Per-wave scout + W6 council (AR_SCOUT_COUNCIL)")
    wave.add_argument("--task-set-id", required=True)
    wave.add_argument("--wave-no", type=int, required=True)
    wave.add_argument("--w6", action="store_true", help="This wave is the W6 boundary")
    wave.add_argument("--now")
    wave.add_argument("--json", action="store_true")
    wave.set_defaults(func=cmd_wave)

    beta = sub.add_parser("beta", help="Beta activation when due (AR_BETA_ACTIVATION)")
    beta.add_argument("--due-state", default="ok", choices=("ok", "due", "overdue"))
    beta.add_argument("--cycle", type=int, required=True)
    beta.add_argument("--now")
    beta.add_argument("--json", action="store_true")
    beta.set_defaults(func=cmd_beta)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
