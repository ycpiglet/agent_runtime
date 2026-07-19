"""End-to-end TDD for wiring scripts/role_routing.py into the live dispatchers.

role_routing.py is a standalone, flag-gated module: nothing in the live dispatch
loop called it, so its three behaviors (additive review pass, per-wave scout +
W6 council, beta activation) were inert even with the flags ON. These tests pin
the WIRING at the dispatcher seams:

  * task_claim_dispatcher.cmd_release -> route_review_pass (event=closeout)
  * wave_dispatcher.cmd_dispatch      -> dispatch_wave_hooks (wave_no, is_w6)

SAFETY CONTRACT (the load-bearing assertions):
  * flag OFF -> the dispatcher behaves EXACTLY as before; NO overlay claim is
    written and the primary (worker / lead-engineer) claim is unchanged.
  * flag ON  -> the seam creates the expected ADDITIVE overlay claim WITHOUT
    removing or mutating the primary claim.

Each dispatcher is invoked as a subprocess (the real CLI path), with the flag
injected via the child env, so the wiring is exercised exactly as it runs live.
All state is synthetic under tmp_path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAIM_DISPATCHER = REPO_ROOT / "scripts" / "task_claim_dispatcher.py"
WAVE_DISPATCHER = REPO_ROOT / "scripts" / "wave_dispatcher.py"
ROLE_ROUTING_FLAG = "AR_ROLE_ROUTING"
SCOUT_COUNCIL_FLAG = "AR_SCOUT_COUNCIL"
TASKSET = "TASKSET-AR-WIRE-TEST"


# ---------------------------------------------------------------------------
# Subprocess helpers (mirror the existing dispatcher test harnesses, but allow
# the role-routing flags to be set/cleared per call via the child env).
# ---------------------------------------------------------------------------


def _env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # Default OFF unless a test sets them, so an enabled flag in the developer's
    # shell cannot leak into the flag-OFF inertness assertions.
    env.pop(ROLE_ROUTING_FLAG, None)
    env.pop(SCOUT_COUNCIL_FLAG, None)
    env.pop("AR_BETA_ACTIVATION", None)
    env.update(overrides)
    return env


def _run_claim(root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLAIM_DISPATCHER), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env or _env(),
    )


def _run_wave(root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WAVE_DISPATCHER), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env or _env(),
    )


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _init_git_repo(root: Path) -> None:
    assert _git(root, "init", "-q").returncode == 0
    assert _git(root, "config", "user.email", "wire-test@example.com").returncode == 0
    assert _git(root, "config", "user.name", "Wire Test").returncode == 0
    (root / "README.md").write_text("role routing wiring fixture\n", encoding="utf-8")
    assert _git(root, "add", "-A").returncode == 0
    assert _git(root, "commit", "-q", "-m", "init").returncode == 0


def _claims(root: Path) -> list[dict]:
    base = root / "agents" / "runtime" / "task_claims"
    if not base.is_dir():
        return []
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(base.glob("*.json"))]


def _events(root: Path) -> list[dict]:
    log = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Claim-release fixtures (mirror tests/test_task_claim_dispatcher.py helpers).
# ---------------------------------------------------------------------------


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def _create_release_candidate(root: Path, *, task_id: str = "TASK-AR-507", suffix: str = "rr1") -> dict:
    _write_worktree(root, task_id)
    created = _run_claim(
        root,
        "create",
        "--task-id",
        task_id,
        "--task-set-id",
        TASKSET,
        "--agent-role",
        "lead-engineer",
        "--mode",
        "implement",
        "--now",
        "2026-06-22T09:00:00+09:00",
        "--suffix",
        suffix,
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def _write_evidence(root: Path, rel: str = "agents/runtime/task_claims/evidence/W4B-VERIFICATION.md") -> str:
    evidence = root / rel
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("# W4b verification\n\n- result: pass\n", encoding="utf-8")
    return rel


def _release(root: Path, claim: dict, *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    evidence_rel = _write_evidence(root)
    return _run_claim(
        root,
        "release",
        "--claim-id",
        claim["claim_id"],
        "--verified-by",
        "qa-20260622-101500-kst-w4b1",
        "--verifier-role",
        "qa-reviewer",
        "--verification-evidence",
        evidence_rel,
        "--now",
        "2026-06-22T10:15:00+09:00",
        "--json",
        env=env,
    )


# ---------------------------------------------------------------------------
# Seam 1: claim release -> route_review_pass (event=closeout)
# ---------------------------------------------------------------------------


def test_release_with_role_routing_off_creates_no_overlay_claim(tmp_path: Path) -> None:
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    released = _release(tmp_path, claim, env=_env())  # flag OFF

    assert released.returncode == 0, released.stderr or released.stdout
    claims = _claims(tmp_path)
    # Exactly the one primary claim exists; it is released. No REVIEW overlay.
    assert [c["claim_id"] for c in claims] == [claim["claim_id"]]
    assert claims[0]["status"] == "released"
    assert claims[0]["agent_role"] == "lead-engineer"
    assert not any(str(c["claim_id"]).startswith("CLAIM-REVIEW-") for c in claims)
    assert not any(e.get("event") == "review_pass_dispatched" for e in _events(tmp_path))


def test_release_with_role_routing_on_creates_additive_review_overlay(tmp_path: Path) -> None:
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))  # flag ON

    assert released.returncode == 0, released.stderr or released.stdout
    claims = _claims(tmp_path)
    by_id = {c["claim_id"]: c for c in claims}

    # Primary claim still present, released, and NOT mutated into a review role.
    assert claim["claim_id"] in by_id
    primary = by_id[claim["claim_id"]]
    assert primary["status"] == "released"
    assert primary["agent_role"] == "lead-engineer"
    assert primary["task_id"] == claim["task_id"]

    # An ADDITIVE review overlay claim now exists with a DISTINCT task id.
    overlays = [c for c in claims if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    assert overlays, f"expected a review overlay, got {[c['claim_id'] for c in claims]}"
    overlay = overlays[0]
    assert overlay["task_id"] != claim["task_id"], "review claim must be additive (distinct task id)"
    assert overlay["agent_role"] in {"skeptic", "independent-auditor"}
    assert overlay.get("parent_task_id") == claim["task_id"]
    assert (tmp_path / overlay["handoff_path"]).is_file()
    assert (tmp_path / overlay["log_path"]).is_file()
    # closeout is the wired event (release == task closeout).
    assert "review-trigger:closeout" in (overlay.get("tags") or [])
    assert any(e.get("event") == "review_pass_dispatched" for e in _events(tmp_path))


@pytest.mark.parametrize("overlay_marker", [True, "true", 1, "1"])
def test_releasing_overlay_does_not_route_nested_review_claim(
    tmp_path: Path, overlay_marker: object
) -> None:
    payload = _create_release_candidate(tmp_path)
    primary = payload["claim"]
    env = _env(**{ROLE_ROUTING_FLAG: "1"})
    released = _release(tmp_path, primary, env=env)
    assert released.returncode == 0, released.stderr or released.stdout
    overlay = next(claim for claim in _claims(tmp_path) if claim.get("overlay") is True)
    overlay["overlay"] = overlay_marker
    overlay_path = tmp_path / "agents" / "runtime" / "task_claims" / f"{overlay['claim_id']}.json"
    overlay_path.write_text(json.dumps(overlay, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    overlay_released = _release(tmp_path, overlay, env=env)

    assert overlay_released.returncode == 0, overlay_released.stderr or overlay_released.stdout
    claims = _claims(tmp_path)
    assert len(claims) == 2
    saved_overlay = next(claim for claim in claims if claim["claim_id"] == overlay["claim_id"])
    assert saved_overlay["status"] == "released"
    assert not any("REVIEW-REVIEW" in claim["claim_id"] for claim in claims)


def test_release_routing_failure_never_breaks_release(tmp_path: Path) -> None:
    """A routing fault must not fail the release (mirrors a2a_claim_emitter robustness)."""
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]
    # Make the first artifact publish fail after the JSON existence check by
    # placing a directory at the deterministic handoff path. Release must stay 0.
    slug = "".join(c if c.isalnum() else "-" for c in claim["task_id"]).strip("-")
    claim_dir = tmp_path / "agents" / "runtime" / "task_claims"
    overlay_id = f"CLAIM-REVIEW-{slug}-independent-auditor-closeout"
    collide = claim_dir / f"{overlay_id}.handoff.md"
    collide.parent.mkdir(parents=True, exist_ok=True)
    collide.mkdir()

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))

    assert released.returncode == 0, released.stderr or released.stdout
    saved = json.loads((tmp_path / payload["path"]).read_text(encoding="utf-8"))
    assert saved["status"] == "released"
    assert not (claim_dir / f"{overlay_id}.json").exists()
    assert not (claim_dir / f"{overlay_id}.log.md").exists()


# ---------------------------------------------------------------------------
# Seam 1b: high-risk closeout -> auditor + skeptic. cmd_create must carry the
# escalation signal (--escalation-trigger) onto the claim, and cmd_release must
# derive triggers from that claim so a HIGH-RISK claim auto-dispatches a skeptic
# adversarial pass on top of the default auditor pass.
# ---------------------------------------------------------------------------


def _create_high_risk_candidate(
    root: Path, *, task_id: str = "TASK-AR-592", suffix: str = "hr1", trigger: str = "high_risk",
) -> dict:
    _write_worktree(root, task_id)
    created = _run_claim(
        root,
        "create",
        "--task-id", task_id,
        "--task-set-id", TASKSET,
        "--agent-role", "lead-engineer",
        "--mode", "implement",
        "--escalation-trigger", trigger,
        "--now", "2026-06-22T09:00:00+09:00",
        "--suffix", suffix,
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def test_cmd_create_stores_escalation_trigger_on_claim(tmp_path: Path) -> None:
    payload = _create_high_risk_candidate(tmp_path)
    claim = payload["claim"]
    assert claim.get("escalation_triggers") == ["high_risk"], (
        "the create seam must carry the escalation signal that release reads"
    )


def test_high_risk_release_dispatches_auditor_and_skeptic(tmp_path: Path) -> None:
    payload = _create_high_risk_candidate(tmp_path)
    claim = payload["claim"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))  # flag ON

    assert released.returncode == 0, released.stderr or released.stdout
    claims = _claims(tmp_path)
    by_id = {c["claim_id"]: c for c in claims}

    # Lead claim untouched: released, still lead-engineer, same task id.
    assert claim["claim_id"] in by_id
    primary = by_id[claim["claim_id"]]
    assert primary["status"] == "released"
    assert primary["agent_role"] == "lead-engineer"
    assert primary["task_id"] == claim["task_id"]

    overlays = [c for c in claims if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    overlay_roles = {c["agent_role"] for c in overlays}
    # BOTH review overlays: the default auditor AND the high-risk skeptic.
    assert "independent-auditor" in overlay_roles
    assert "skeptic" in overlay_roles, f"high-risk release must dispatch a skeptic, got {overlay_roles}"
    skeptic = next(c for c in overlays if c["agent_role"] == "skeptic")
    assert skeptic["mode"] == "review"
    assert "high-risk" in (skeptic.get("tags") or [])
    assert "high_risk" in (skeptic.get("tags") or [])


def test_high_risk_release_via_tag_also_dispatches_skeptic(tmp_path: Path) -> None:
    """A risk *tag* matching an ESCALATION_TRIGGER also drives the skeptic pass."""
    _write_worktree(tmp_path, "TASK-AR-593")
    created = _run_claim(
        tmp_path,
        "create",
        "--task-id", "TASK-AR-593",
        "--task-set-id", TASKSET,
        "--agent-role", "lead-engineer",
        "--mode", "implement",
        "--tag", "security",
        "--now", "2026-06-22T09:00:00+09:00",
        "--suffix", "hr2",
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    claim = json.loads(created.stdout)["claim"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))

    assert released.returncode == 0, released.stderr or released.stdout
    overlays = [c for c in _claims(tmp_path) if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    roles = {c["agent_role"] for c in overlays}
    assert {"independent-auditor", "skeptic"} <= roles, roles


def test_non_high_risk_release_is_auditor_only(tmp_path: Path) -> None:
    """A plain claim (no escalation triggers/risk tags) gets only the auditor pass."""
    payload = _create_release_candidate(tmp_path)
    claim = payload["claim"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))

    assert released.returncode == 0, released.stderr or released.stdout
    overlays = [c for c in _claims(tmp_path) if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    roles = {c["agent_role"] for c in overlays}
    assert roles == {"independent-auditor"}, f"non-high-risk closeout must stay auditor-only, got {roles}"
    assert not any(c["agent_role"] == "skeptic" for c in _claims(tmp_path))


# ---------------------------------------------------------------------------
# Seam 1c: cmd_create AUTO-INHERITS a unit's escalation_triggers from the
# --unit-spec it is already handed, so a HIGH-RISK unit drives the skeptic pass
# at release with NO manual --escalation-trigger flag. The whole point of the
# link: high-risk work carries its risk signal automatically.
# ---------------------------------------------------------------------------


def _write_unit_spec(root: Path, *, name: str, escalation_triggers: list[str]) -> Path:
    """Write a unit definition .md whose frontmatter carries escalation_triggers."""
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    triggers = "[" + ", ".join(escalation_triggers) + "]"
    path.write_text(
        f"""---
unit_id: {name.removesuffix(".md")}
task_id: TASK-AR-INH
task_set_id: {TASKSET}
status: worker_ready
horizon: unit
target_files:
  - scripts/inh.py
escalation_triggers: {triggers}
---

# {name}
""",
        encoding="utf-8",
    )
    return path


def _create_via_unit_spec(root: Path, *, task_id: str, unit: Path, suffix: str) -> dict:
    _write_worktree(root, task_id)
    created = _run_claim(
        root,
        "create",
        "--task-id", task_id,
        "--task-set-id", TASKSET,
        "--agent-role", "lead-engineer",
        "--mode", "implement",
        "--unit-spec", str(unit),
        "--now", "2026-06-22T09:00:00+09:00",
        "--suffix", suffix,
        "--json",
    )
    assert created.returncode == 0, created.stderr or created.stdout
    return json.loads(created.stdout)


def test_high_risk_unit_spec_release_dispatches_auditor_and_skeptic(tmp_path: Path) -> None:
    """END-TO-END: a high-risk --unit-spec, NO manual trigger -> auditor + skeptic."""
    unit = _write_unit_spec(tmp_path, name="UNIT-HR.md", escalation_triggers=["high_risk"])
    payload = _create_via_unit_spec(tmp_path, task_id="TASK-AR-INH", unit=unit, suffix="inh1")
    claim = payload["claim"]
    # The create seam auto-inherited the unit's trigger onto the claim.
    assert "high_risk" in claim["escalation_triggers"], claim["escalation_triggers"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))

    assert released.returncode == 0, released.stderr or released.stdout
    overlays = [c for c in _claims(tmp_path) if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    roles = {c["agent_role"] for c in overlays}
    assert {"independent-auditor", "skeptic"} <= roles, roles


def test_ambiguity_only_unit_spec_release_is_auditor_only(tmp_path: Path) -> None:
    """A unit whose only trigger is ``ambiguity`` (NOT high-risk) -> auditor only."""
    unit = _write_unit_spec(tmp_path, name="UNIT-AMB.md", escalation_triggers=["ambiguity"])
    payload = _create_via_unit_spec(tmp_path, task_id="TASK-AR-AMB", unit=unit, suffix="amb1")
    claim = payload["claim"]
    # The trigger is inherited verbatim (no pre-filter); release intersects it.
    assert claim["escalation_triggers"] == ["ambiguity"], claim["escalation_triggers"]

    released = _release(tmp_path, claim, env=_env(**{ROLE_ROUTING_FLAG: "1"}))

    assert released.returncode == 0, released.stderr or released.stdout
    overlays = [c for c in _claims(tmp_path) if c.get("overlay") and str(c["claim_id"]).startswith("CLAIM-REVIEW-")]
    roles = {c["agent_role"] for c in overlays}
    assert roles == {"independent-auditor"}, f"ambiguity-only must stay auditor-only, got {roles}"
    assert not any(c["agent_role"] == "skeptic" for c in _claims(tmp_path))


# ---------------------------------------------------------------------------
# Seam 2: wave dispatch -> dispatch_wave_hooks (progress-scout per wave)
# ---------------------------------------------------------------------------


def _write_task(root: Path, task_id: str, *, status: str = "planned") -> None:
    taskset_path = root / "agents" / "project" / "initiatives" / f"{TASKSET}.md"
    taskset_path.parent.mkdir(parents=True, exist_ok=True)
    taskset_path.write_text(
        f"""---
schema_version: agent-runtime-work-item/v1
work_id: {TASKSET}
kind: taskset
title: Role Routing Wiring Fixture
summary: Synthetic canonical taskset for wave role-routing tests.
---
""",
        encoding="utf-8",
    )
    tasks_dir = root / "agents" / "lead_engineer" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.md").write_text(
        f"""---
id: {task_id}
status: {status}
priority: P1
difficulty: M
est_hours: 2
est_tokens: 200
task_set_id: {TASKSET}
tags: []
---

## Goal
- Wiring fixture task.
""",
        encoding="utf-8",
    )


def _write_unit(root: Path, task_id: str, index: int, *, target_files: list[str], status: str = "worker_ready") -> str:
    unit_id = f"UNIT-{task_id}-{index:03d}"
    path = root / "agents" / "lead_engineer" / "tasks" / "units" / task_id / f"{unit_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    targets = "\n".join(f"  - {entry}" for entry in target_files)
    path.write_text(
        f"""---
unit_id: {unit_id}
task_id: {task_id}
task_set_id: {TASKSET}
project_id: PROJECT-AGENT-RUNTIME-PM-OS
status: {status}
horizon: unit
model_tier: worker_standard
context: "Wiring fixture unit."
inputs:
  - agents/lead_engineer/tasks/{task_id}.md
target_files:
{targets}
scope: "Only this fixture unit."
acceptance:
  - "It passes."
verification:
  - "python -m pytest -q"
handoff: "Report the result."
stop_condition: "stop_after:{unit_id}:no_adjacent_taskset"
---

# {unit_id}
""",
        encoding="utf-8",
    )
    return unit_id


def test_wave_dispatch_with_scout_council_off_creates_no_overlay_claim(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    _write_task(tmp_path, "TASK-AR-901")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])

    result = _run_wave(
        tmp_path, "--taskset", TASKSET, "--dispatch", "--mode", "cascade",
        "--now", "2026-06-22T10:00:00+09:00", "--suffix", "wv1", "--json",
        env=_env(),  # flag OFF
    )

    assert result.returncode == 0, result.stderr or result.stdout
    issued = json.loads(result.stdout)["issued"]
    assert [e["unit_id"] for e in issued] == [u1]
    claims = _claims(tmp_path)
    # Only the worker claim — no scout/council overlay.
    assert not any(c.get("overlay") for c in claims)
    assert not any(str(c["claim_id"]).startswith("CLAIM-SCOUT-") for c in claims)
    assert not any(e.get("event") == "progress_scout_sweep" for e in _events(tmp_path))


def test_wave_dispatch_with_scout_council_on_creates_scout_overlay(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    _write_task(tmp_path, "TASK-AR-901")
    u1 = _write_unit(tmp_path, "TASK-AR-901", 1, target_files=["scripts/a.py"])

    result = _run_wave(
        tmp_path, "--taskset", TASKSET, "--dispatch", "--mode", "cascade",
        "--now", "2026-06-22T10:00:00+09:00", "--suffix", "wv1", "--json",
        env=_env(**{SCOUT_COUNCIL_FLAG: "1"}),  # flag ON
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["wave"] == 1
    assert [e["unit_id"] for e in payload["issued"]] == [u1]

    claims = _claims(tmp_path)
    # Worker claim is present and unchanged in role.
    worker = [c for c in claims if c.get("unit_id") == u1]
    assert worker and worker[0]["agent_role"] == "lead-engineer"
    # An additive progress-scout overlay for THIS wave now exists.
    scouts = [c for c in claims if c.get("overlay") and c["agent_role"] == "progress-scout"]
    assert scouts, f"expected a scout overlay, got {[c['claim_id'] for c in claims]}"
    assert scouts[0]["claim_id"].endswith("-W1")
    # wave 1 is not W6, so NO council overlay.
    assert not any(c["agent_role"] == "council" for c in claims)
    events = {e.get("event") for e in _events(tmp_path)}
    assert "progress_scout_sweep" in events
    assert "council_deliberation" not in events
