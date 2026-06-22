"""TASK-239 — adaptive model routing policy tests."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
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


def test_deep_reasoning_signal_routes_to_opus():
    decision = mr.select_model("High", prompt="investigate why the design failed")
    assert decision["policy_tier"] == "sonnet"
    assert decision["selected_tier"] == "opus"
    assert "deep_reasoning" in decision["signals"]


def test_deep_reasoning_wins_over_lookup_signal():
    decision = mr.select_model("Medium", prompt="find why the design regressed")
    assert decision["selected_tier"] == "opus"
    assert "simple_lookup" in decision["signals"]
    assert "deep_reasoning" in decision["signals"]


def test_large_surface_signal_routes_to_opus():
    files = [f"scripts/f{i}.py" for i in range(8)]
    decision = mr.select_model("Medium", changed_files=files, diff_lines=120)
    assert decision["selected_tier"] == "opus"
    assert "large_file_count" in decision["signals"]


def test_critical_is_not_downrouted_by_simple_lookup():
    decision = mr.select_model("Critical", prompt="read and list the schema files")
    assert decision["policy_tier"] == "opus"
    assert decision["selected_tier"] == "opus"
    assert "simple_lookup" in decision["signals"]


def test_critical_manual_override_cannot_downroute_below_policy():
    decision = mr.resolve_model("haiku", grade="Critical")
    assert decision["policy_tier"] == "opus"
    assert decision["selected_tier"] == "opus"
    assert "critical_floor" in decision["signals"]


def test_resolve_model_accepts_raw_provider_model_names():
    decision = mr.resolve_model("claude-opus-4-7", grade="High")
    assert decision["policy_tier"] == "sonnet"
    assert decision["selected_tier"] == "claude-opus-4-7"
    assert "manual_override" in decision["signals"]


def test_critical_raw_provider_model_name_respects_floor():
    decision = mr.resolve_model("claude-haiku-4-5", grade="Critical")
    assert decision["policy_tier"] == "opus"
    assert decision["selected_tier"] == "opus"
    assert "critical_floor" in decision["signals"]


def test_provider_env_resolves_claude_agent_tier(monkeypatch):
    monkeypatch.setenv("CLAUDE_AGENT_SONNET_MODEL", "claude-sonnet-test")
    env = mr.provider_env("claude-agent", "sonnet")
    assert env == {"CLAUDE_AGENT_MODEL": "claude-sonnet-test"}


def test_provider_env_claude_agent_default_models(monkeypatch):
    monkeypatch.delenv("CLAUDE_AGENT_OPUS_MODEL", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_SONNET_MODEL", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_HAIKU_MODEL", raising=False)
    assert mr.provider_env("claude-agent", "opus") == {"CLAUDE_AGENT_MODEL": "claude-opus-4-8"}
    assert mr.provider_env("claude-agent", "sonnet") == {"CLAUDE_AGENT_MODEL": "claude-sonnet-4-6"}
    assert mr.provider_env("claude-agent", "haiku") == {"CLAUDE_AGENT_MODEL": "claude-haiku-4-5"}


def test_provider_env_routes_codex_agent_default(monkeypatch):
    monkeypatch.delenv("CODEX_AGENT_SONNET_MODEL", raising=False)
    assert mr.provider_env("codex-agent", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-5.2-codex"}


def test_provider_env_routes_codex_default(monkeypatch):
    monkeypatch.delenv("CODEX_AGENT_SONNET_MODEL", raising=False)
    assert mr.provider_env("codex", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-5.2-codex"}


def test_provider_env_codex_agent_respects_env_override(monkeypatch):
    monkeypatch.setenv("CODEX_AGENT_SONNET_MODEL", "gpt-custom-codex")
    assert mr.provider_env("codex-agent", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-custom-codex"}


def test_provider_env_codex_accepts_pm_tier(monkeypatch):
    monkeypatch.setenv("CODEX_AGENT_OPUS_MODEL", "gpt-codex-opus")
    assert mr.provider_env("codex-agent", "planner_high") == {"CODEX_PROVIDER_MODEL": "gpt-codex-opus"}


def test_provider_env_codex_passthrough_raw_model():
    assert mr.provider_env("codex-agent", "gpt-raw") == {"CODEX_PROVIDER_MODEL": "gpt-raw"}


def test_provider_env_ignores_non_claude_agent():
    assert mr.provider_env("dummy", "haiku") == {}
    assert mr.provider_env("claude", "sonnet") == {}
