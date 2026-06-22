"""End-to-end smoke: role_routing activates from CONFIG ALONE (no env).

The autonomous dispatch loop runs as processes that don't inherit
`.claude/settings.local.json` env, so env-only flags never reached it (measured:
0 overlay claims, lead-engineer still ~76%). These tests prove the config-driven
gate (`agents/project/role-routing.json`) creates real overlay claim files with
NO `AR_*` env set — so committed config reliably activates routing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import role_routing  # noqa: E402

_FLAGS = (role_routing.ROLE_ROUTING_FLAG, role_routing.SCOUT_COUNCIL_FLAG, role_routing.BETA_ACTIVATION_FLAG)


@pytest.fixture
def no_env(monkeypatch):
    """Guarantee NO AR_* env so only the config path can enable routing."""
    for flag in _FLAGS:
        monkeypatch.delenv(flag, raising=False)


def _write_config(root: Path, **values: bool) -> None:
    cfg = root / "agents" / "project" / "role-routing.json"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(values), encoding="utf-8")


def _claim_files(root: Path) -> list[Path]:
    d = root / "agents" / "runtime" / "task_claims"
    return sorted(d.glob("*.json")) if d.is_dir() else []


def test_review_pass_activates_from_config_only(tmp_path: Path, no_env) -> None:
    _write_config(tmp_path, role_routing=True, scout_council=True, beta_activation=True)
    assert _claim_files(tmp_path) == []

    result = role_routing.route_review_pass(tmp_path, task_id="TASK-X", task_set_id="TS-Y", event="closeout")

    assert result["enabled"] is True
    assert result["created"], "config-only should create an additive review overlay claim"
    assert _claim_files(tmp_path), "an overlay claim file must exist on disk"


def test_wave_hooks_activate_from_config_only_incl_w6(tmp_path: Path, no_env) -> None:
    _write_config(tmp_path, role_routing=True, scout_council=True, beta_activation=True)

    result = role_routing.dispatch_wave_hooks(tmp_path, task_set_id="TS-Y", wave_no=6, is_w6=True)

    assert result["enabled"] is True
    created_ids = " ".join(str(c) for c in result["created"])
    assert "SCOUT" in created_ids.upper(), "every wave gets a progress-scout sweep"
    assert "COUNCIL" in created_ids.upper(), "W6 additionally dispatches a council"
    assert _claim_files(tmp_path), "overlay claim files must exist on disk"


def test_all_false_config_is_inert(tmp_path: Path, no_env) -> None:
    _write_config(tmp_path, role_routing=False, scout_council=False, beta_activation=False)

    r1 = role_routing.route_review_pass(tmp_path, task_id="TASK-X", task_set_id="TS-Y")
    r2 = role_routing.dispatch_wave_hooks(tmp_path, task_set_id="TS-Y", wave_no=6, is_w6=True)

    assert r1["enabled"] is False and r2["enabled"] is False
    assert _claim_files(tmp_path) == [], "all-false config must create nothing"


def test_no_config_and_no_env_defaults_off(tmp_path: Path, no_env) -> None:
    # no role-routing.json written, no AR_* env -> default off
    result = role_routing.route_review_pass(tmp_path, task_id="TASK-X", task_set_id="TS-Y")

    assert result["enabled"] is False
    assert _claim_files(tmp_path) == [], "default must be off when neither config nor env enables"


def test_shipped_config_is_on() -> None:
    # the committed repo config activates routing for the live loop
    cfg = json.loads((REPO_ROOT / "agents" / "project" / "role-routing.json").read_text(encoding="utf-8"))
    assert cfg.get("role_routing") is True
    assert cfg.get("scout_council") is True
