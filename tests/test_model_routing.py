from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import model_routing as mr  # noqa: E402


def test_grade_policy_maps_default_tiers():
    assert mr.select_model("Low")["selected_tier"] == "haiku"
    assert mr.select_model("Medium")["selected_tier"] == "sonnet"
    assert mr.select_model("High")["selected_tier"] == "sonnet"
    assert mr.select_model("Critical")["selected_tier"] == "opus"


def test_simple_lookup_signal_downroutes_noncritical_to_haiku():
    decision = mr.select_model("Medium", prompt="find and list the relevant files")
    assert decision["policy_tier"] == "sonnet"
    assert decision["selected_tier"] == "haiku"
    assert "simple_lookup" in decision["signals"]


def test_pm_worker_low_stays_low_when_unit_is_precise():
    decision = mr.resolve_work_item_tier(
        {"worker_model_tier": "worker_low"},
        {"model_tier": "worker_low", "escalation_triggers": []},
    )

    assert decision["requested_tier"] == "worker_low"
    assert decision["selected_tier"] == "worker_low"
    assert decision["provider_tier"] == "haiku"


def test_pm_worker_escalates_to_planner_for_high_risk_trigger():
    decision = mr.resolve_work_item_tier(
        {"worker_model_tier": "worker_low", "escalation_triggers": ["security"]},
        {"model_tier": "worker_low"},
    )

    assert decision["requested_tier"] == "worker_low"
    assert decision["selected_tier"] == "planner_high"
    assert decision["provider_tier"] == "opus"
    assert "security" in decision["escalation_triggers"]


def test_provider_env_accepts_pm_tier(monkeypatch):
    monkeypatch.setenv("CLAUDE_AGENT_OPUS_MODEL", "claude-opus-test")
    assert mr.provider_env("claude-agent", "planner_high") == {"CLAUDE_AGENT_MODEL": "claude-opus-test"}
