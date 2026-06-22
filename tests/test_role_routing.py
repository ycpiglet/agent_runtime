"""TDD for scripts/role_routing.py — flag-gated dormant-role / beta routing.

SAFETY CONTRACT (the reason this module exists): other instances of this
autonomous system run LIVE in the same repo concurrently. Every behavior here
that changes *who gets work* MUST be flag-gated and DEFAULT-OFF, so that merging
the capability is INERT until the Owner enables it. These tests prove both:

  * flag OFF  -> dispatch behavior is unchanged; NO additive claim is written
                 (inertness is the load-bearing assertion);
  * flag ON   -> the additive review / scout / council / beta claims appear,
                 WITHOUT removing or mutating the original lead-engineer claim.

All state is synthetic and lives under tmp_path; nothing touches the real repo.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# role_routing imports sibling scripts (atomic_io, pane_event_log) by bare name,
# matching the established pattern for scripts run with scripts/ on the path.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load():
    spec = importlib.util.spec_from_file_location(
        "role_routing", SCRIPTS_DIR / "role_routing.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _claims_dir(root: Path) -> Path:
    return root / "agents" / "runtime" / "task_claims"


def _seed_lead_claim(root: Path, *, task_id: str = "TASK-AR-900",
                     task_set_id: str = "TASKSET-AR-900") -> dict:
    """Write a pre-existing lead-engineer claim, as the live loop would."""
    claims = _claims_dir(root)
    claims.mkdir(parents=True, exist_ok=True)
    claim = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": f"CLAIM-LEAD-{task_id}",
        "task_id": task_id,
        "task_set_id": task_set_id,
        "active_scope": task_set_id,
        "agent_role": "lead-engineer",
        "agent_instance_id": "le-seed-0001",
        "display_name": "lead_engineer@work-01",
        "status": "in_progress",
        "worktree_path": f".worktrees/{task_id}",
        "branch": f"codex/{task_id.lower()}",
    }
    (claims / f"{claim['claim_id']}.json").write_text(
        json.dumps(claim, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return claim


def _load_claims(root: Path) -> list[dict]:
    base = _claims_dir(root)
    if not base.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(base.glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def _events(root: Path) -> list[dict]:
    log = root / "agents" / "runtime" / "pane_events" / "pane-events.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Flag names are part of the public contract; pin them so a rename is caught.
# ---------------------------------------------------------------------------


def test_flag_names_are_the_documented_ones():
    mod = _load()
    assert mod.ROLE_ROUTING_FLAG == "AR_ROLE_ROUTING"
    assert mod.SCOUT_COUNCIL_FLAG == "AR_SCOUT_COUNCIL"
    assert mod.BETA_ACTIVATION_FLAG == "AR_BETA_ACTIVATION"


def test_flags_default_off(monkeypatch):
    mod = _load()
    for flag in (mod.ROLE_ROUTING_FLAG, mod.SCOUT_COUNCIL_FLAG, mod.BETA_ACTIVATION_FLAG):
        monkeypatch.delenv(flag, raising=False)
    assert mod.role_routing_enabled() is False
    assert mod.scout_council_enabled() is False
    assert mod.beta_activation_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_flag_truthy_values_enable(monkeypatch, value):
    mod = _load()
    monkeypatch.setenv(mod.ROLE_ROUTING_FLAG, value)
    assert mod.role_routing_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", ""])
def test_flag_falsy_values_stay_off(monkeypatch, value):
    mod = _load()
    monkeypatch.setenv(mod.ROLE_ROUTING_FLAG, value)
    assert mod.role_routing_enabled() is False


# ---------------------------------------------------------------------------
# 1. Review-role routing (skeptic / independent-auditor) — additive.
# ---------------------------------------------------------------------------


def test_review_routing_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_ROLE_ROUTING", raising=False)
    mod = _load()
    _seed_lead_claim(tmp_path)
    before = _load_claims(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    # INERTNESS: no new claim file, the lead claim is byte-for-byte unchanged.
    after = _load_claims(tmp_path)
    assert after == before


def test_review_routing_on_creates_additive_claim_without_touching_lead(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    lead = _seed_lead_claim(tmp_path)

    result = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert len(result["created"]) >= 1
    claims = _load_claims(tmp_path)
    roles = {c["agent_role"] for c in claims}
    # lead-engineer claim is still present and UNCHANGED (parallel, not replaced)
    assert "lead-engineer" in roles
    lead_after = next(c for c in claims if c["claim_id"] == lead["claim_id"])
    assert lead_after["status"] == "in_progress"
    assert lead_after["agent_role"] == "lead-engineer"
    # an additive review claim now exists for a review role
    review = [c for c in claims if c["agent_role"] in {"skeptic", "independent-auditor"}]
    assert review, f"expected a review-role claim, got roles={roles}"
    rc = review[0]
    assert rc["task_id"] != lead["task_id"], "review claim must be a distinct, additive task id"
    assert rc.get("mode") == "review" or "review" in (rc.get("tags") or [])
    # an event is logged so the live loop / UI can see the parallel pass
    assert any(e.get("event") == "review_pass_dispatched" for e in _events(tmp_path))


def test_review_routing_on_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_ROLE_ROUTING", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)
    first = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )
    second = mod.route_review_pass(
        tmp_path, task_id="TASK-AR-900", task_set_id="TASKSET-AR-900",
        event="merge", now="2026-06-22T10:00:00+09:00",
    )
    assert first["created"]
    assert second["created"] == [], "re-dispatch must not duplicate the review claim"


# ---------------------------------------------------------------------------
# 2. progress-scout per wave + council at W6.
# ---------------------------------------------------------------------------


def test_wave_hooks_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_SCOUT_COUNCIL", raising=False)
    mod = _load()
    _seed_lead_claim(tmp_path)
    before = _load_claims(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=2,
        is_w6=True, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before


def test_wave_hooks_on_dispatches_scout_per_wave(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_SCOUT_COUNCIL", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=2,
        is_w6=False, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    claims = _load_claims(tmp_path)
    scouts = [c for c in claims if c["agent_role"] == "progress-scout"]
    assert scouts, "a progress-scout sweep claim should be created for the wave"
    # not W6, so NO council deliberation yet
    assert not [c for c in claims if c["agent_role"] == "council"]
    assert any(e.get("event") == "progress_scout_sweep" for e in _events(tmp_path))


def test_wave_hooks_on_at_w6_adds_council(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_SCOUT_COUNCIL", "1")
    mod = _load()
    _seed_lead_claim(tmp_path)

    result = mod.dispatch_wave_hooks(
        tmp_path, task_set_id="TASKSET-AR-900", wave_no=6,
        is_w6=True, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    claims = _load_claims(tmp_path)
    assert [c for c in claims if c["agent_role"] == "progress-scout"]
    assert [c for c in claims if c["agent_role"] == "council"], "W6 boundary should add a council deliberation"
    events = {e.get("event") for e in _events(tmp_path)}
    assert "progress_scout_sweep" in events
    assert "council_deliberation" in events


# ---------------------------------------------------------------------------
# 3. beta activation when beta_tester_due reports due/overdue.
# ---------------------------------------------------------------------------


def test_beta_activation_off_is_inert(tmp_path, monkeypatch):
    monkeypatch.delenv("AR_BETA_ACTIVATION", raising=False)
    mod = _load()
    before = _load_claims(tmp_path)

    result = mod.maybe_activate_beta(
        tmp_path, due_state="overdue", cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before
    # no BTC scaffold either
    assert not list((tmp_path / "agents" / "beta_tester" / "test_cases").glob("BTC-*.md")) \
        if (tmp_path / "agents" / "beta_tester" / "test_cases").is_dir() else True


def test_beta_activation_on_but_not_due_is_inert(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    before = _load_claims(tmp_path)

    result = mod.maybe_activate_beta(
        tmp_path, due_state="ok", cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert result["due"] is False
    assert result["created"] == []
    assert _load_claims(tmp_path) == before


@pytest.mark.parametrize("due_state", ["due", "overdue"])
def test_beta_activation_on_and_due_emits_claim_and_btc_scaffold(tmp_path, monkeypatch, due_state):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()

    result = mod.maybe_activate_beta(
        tmp_path, due_state=due_state, cycle=7, now="2026-06-22T10:00:00+09:00",
    )

    assert result["enabled"] is True
    assert result["due"] is True
    assert result["created"], "a beta_tester claim should be emitted when due/overdue + flag on"
    claims = _load_claims(tmp_path)
    beta = [c for c in claims if c["agent_role"] in {"beta-tester", "beta_tester"}]
    assert beta, "expected a beta_tester claim"
    # BTC-* scaffold appears under the beta_tester test_cases dir
    btc = list((tmp_path / "agents" / "beta_tester" / "test_cases").glob("BTC-*.md"))
    assert btc, "expected a BTC-* scaffold file"
    assert any(e.get("event") == "beta_round_dispatched" for e in _events(tmp_path))


def test_beta_activation_on_and_due_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("AR_BETA_ACTIVATION", "1")
    mod = _load()
    first = mod.maybe_activate_beta(tmp_path, due_state="overdue", cycle=7,
                                    now="2026-06-22T10:00:00+09:00")
    second = mod.maybe_activate_beta(tmp_path, due_state="overdue", cycle=7,
                                     now="2026-06-22T10:00:00+09:00")
    assert first["created"]
    assert second["created"] == [], "the same cycle's beta round must not be dispatched twice"
