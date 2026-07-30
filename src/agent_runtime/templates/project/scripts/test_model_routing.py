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


def test_data_integrity_escalates_worker_pm_tier():
    decision = mr.resolve_work_item_tier(
        {"worker_model_tier": "worker_low"},
        {"model_tier": "worker_low", "escalation_triggers": ["data_integrity"]},
    )
    assert decision["selected_tier"] == "planner_high"
    assert decision["unknown_triggers"] == []


def test_explorer_defaults_to_worker_low():
    decision = mr.resolve_subagent_tier("explorer")
    assert decision["requested_tier"] == "worker_low"
    assert decision["selected_tier"] == "worker_low"


def test_runtime_role_families_have_explicit_economic_policy():
    expected = {
        "scribe": ("scribe", "worker_low"),
        "research": ("exploration", "worker_low"),
        "implementation": ("implementation", "worker_low"),
        "reviewer": ("review", "reviewer_standard"),
        "auditor": ("audit", "reviewer_high"),
    }
    for role, (policy_id, tier) in expected.items():
        decision = mr.resolve_subagent_tier(role)
        assert decision["role_policy_status"] == "explicit"
        assert decision["role_policy_id"] == policy_id
        assert decision["selected_tier"] == tier


def test_high_tier_needs_role_policy_or_registered_trigger():
    denied = mr.resolve_subagent_tier(
        "explorer",
        requested_tier="planner_high",
    )
    escalated = mr.resolve_subagent_tier(
        "explorer",
        requested_tier="planner_high",
        escalation_triggers=["security"],
    )
    audit = mr.resolve_subagent_tier("auditor")

    assert denied["routing_status"] == "high_tier_denied"
    assert denied["selected_tier"] == "worker_low"
    assert escalated["registered_escalation_reason"] == "trigger:security"
    assert audit["registered_escalation_reason"] == "role_policy:audit"


def test_lookup_preflight_blocks_without_bounded_evidence():
    blocked = mr.deterministic_preflight("find and list provider files")
    allowed = mr.deterministic_preflight(
        "find and list provider files",
        status="attempted_insufficient",
        evidence=["rg returned only compatibility aliases"],
    )
    complete = mr.deterministic_preflight(
        "find and list provider files",
        status="completed_sufficient",
    )
    assert blocked["allow_dispatch"] is False
    assert blocked["status"] == "required_unresolved"
    assert allowed["allow_dispatch"] is True
    assert complete["dispatch_required"] is False


def test_codex_equivalent_tiers_are_economically_ineligible(monkeypatch):
    for name in (
        "CODEX_AGENT_HAIKU_MODEL",
        "CODEX_AGENT_SONNET_MODEL",
        "CODEX_AGENT_OPUS_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)
    route = mr.resolve_provider_route(
        "codex-agent",
        "planner_high",
        requested_tier="worker_low",
    )
    assert route["model_changed"] is False
    assert route["route_status"] == "ineffective_equivalent"
    assert route["economic_claim_status"] == "ineligible_equivalent"
    assert route["observed_model"] is None


def test_native_codex_route_carries_exact_model_and_reasoning(monkeypatch):
    monkeypatch.delenv("CODEX_NATIVE_WORKER_LOW_MODEL", raising=False)
    monkeypatch.delenv("CODEX_NATIVE_WORKER_LOW_REASONING", raising=False)
    route = mr.resolve_provider_route("native-codex", "worker_low")
    assert route["execution_surface"] == "native_subagent_spawn"
    assert route["resolved_model"] == "gpt-5.6-terra"
    assert route["reasoning_effort"] == "low"
    assert route["application_status"] == "configured_unverified"
    assert route["model_observation_status"] == "unverified"


def test_native_equivalence_uses_model_and_reasoning(monkeypatch):
    for name in (
        "CODEX_NATIVE_WORKER_LOW_MODEL",
        "CODEX_NATIVE_WORKER_STANDARD_MODEL",
        "CODEX_NATIVE_WORKER_LOW_REASONING",
        "CODEX_NATIVE_WORKER_STANDARD_REASONING",
    ):
        monkeypatch.delenv(name, raising=False)

    matrix = mr.provider_routing_matrix("native-codex")
    rows = {row["pm_tier"]: row for row in matrix["rows"]}
    route = mr.resolve_provider_route(
        "native-codex",
        "worker_low",
        baseline_tier="worker_standard",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
    )

    assert rows["worker_low"]["equivalence_status"] == "distinct"
    assert rows["worker_standard"]["equivalence_status"] == "distinct"
    assert route["model_changed"] is False
    assert route["route_changed"] is True
    assert route["application_status"] == "applied"
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
