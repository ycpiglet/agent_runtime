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


def test_data_integrity_is_a_registered_high_risk_trigger():
    decision = mr.resolve_work_item_tier(
        {"worker_model_tier": "worker_low"},
        {"model_tier": "worker_low", "escalation_triggers": ["data_integrity"]},
    )

    assert decision["requested_tier"] == "worker_low"
    assert decision["selected_tier"] == "planner_high"
    assert decision["unknown_triggers"] == []


def test_subagent_roles_default_low_for_exploration_and_stronger_for_review():
    explorer = mr.resolve_subagent_tier("explorer")
    reviewer = mr.resolve_subagent_tier("reviewer")
    escalated = mr.resolve_subagent_tier(
        "reviewer", escalation_triggers=["security"]
    )

    assert explorer["selected_tier"] == "worker_low"
    assert reviewer["selected_tier"] == "reviewer_standard"
    assert escalated["selected_tier"] == "reviewer_high"


def test_scribe_research_implementation_review_and_audit_use_explicit_policy():
    expected = {
        "scribe": ("scribe", "worker_low"),
        "researcher": ("exploration", "worker_low"),
        "implementer": ("implementation", "worker_low"),
        "backend": ("implementation", "worker_low"),
        "uiux": ("implementation", "worker_low"),
        "ci-cd": ("implementation", "worker_low"),
        "timeline": ("exploration", "worker_low"),
        "qa-reviewer": ("review", "reviewer_standard"),
        "beta-tester": ("review", "reviewer_standard"),
        "independent-auditor": ("audit", "reviewer_high"),
    }

    for role, (policy_id, tier) in expected.items():
        decision = mr.resolve_subagent_tier(role)
        assert decision["role_policy_status"] == "explicit"
        assert decision["role_policy_id"] == policy_id
        assert decision["selected_tier"] == tier


def test_unregistered_high_request_is_denied_without_escalation_reason():
    denied = mr.resolve_subagent_tier(
        "scribe",
        requested_tier="planner_high",
    )
    allowed = mr.resolve_subagent_tier(
        "scribe",
        requested_tier="planner_high",
        escalation_triggers=["cross_cutting"],
    )

    assert denied["routing_status"] == "high_tier_denied"
    assert denied["selected_tier"] == "worker_low"
    assert denied["registered_escalation_reason"] is None
    assert allowed["selected_tier"] == "planner_high"
    assert allowed["high_tier_authorized"] is True
    assert allowed["registered_escalation_reason"] == "trigger:cross_cutting"


def test_lookup_only_dispatch_requires_deterministic_preflight_evidence():
    unresolved = mr.deterministic_preflight("find and list routing files")
    insufficient = mr.deterministic_preflight(
        "find and list routing files",
        status="attempted_insufficient",
        evidence=["rg found only generated references"],
    )
    sufficient = mr.deterministic_preflight(
        "find and list routing files",
        status="completed_sufficient",
        evidence=["rg result recorded"],
    )

    assert unresolved["status"] == "required_unresolved"
    assert unresolved["allow_dispatch"] is False
    assert insufficient["allow_dispatch"] is True
    assert sufficient["allow_dispatch"] is False
    assert sufficient["dispatch_required"] is False


def test_equivalent_codex_api_tiers_cannot_claim_effective_model_change(monkeypatch):
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

    assert route["resolved_model"] == "gpt-5.2-codex"
    assert route["baseline_model"] == "gpt-5.2-codex"
    assert route["model_changed"] is False
    assert route["route_status"] == "ineffective_equivalent"
    assert route["economic_claim_status"] == "ineligible_equivalent"
    assert route["observed_model"] is None
    assert route["model_observation_status"] == "unverified"


def test_distinct_claude_route_is_effective_but_not_observed(monkeypatch):
    monkeypatch.delenv("CLAUDE_AGENT_HAIKU_MODEL", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_OPUS_MODEL", raising=False)

    route = mr.resolve_provider_route(
        "claude-agent",
        "planner_high",
        requested_tier="worker_low",
    )

    assert route["baseline_model"] == "claude-haiku-4-5"
    assert route["resolved_model"] == "claude-opus-4-8"
    assert route["model_changed"] is True
    assert route["route_status"] == "effective"
    assert route["application_status"] == "configured_unverified"


def test_native_codex_matrix_is_configured_but_unverified(monkeypatch):
    for name in (
        "CODEX_NATIVE_WORKER_LOW_MODEL",
        "CODEX_NATIVE_WORKER_STANDARD_MODEL",
        "CODEX_NATIVE_STRONG_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    matrix = mr.provider_routing_matrix("native-codex")
    rows = {row["pm_tier"]: row for row in matrix["rows"]}

    assert matrix["status"] == "configured_unverified"
    assert rows["worker_low"]["resolved_model"] == "gpt-5.6-terra"
    assert rows["worker_low"]["reasoning_effort"] == "low"
    assert rows["worker_standard"]["reasoning_effort"] == "medium"
    assert rows["planner_high"]["resolved_model"] == "gpt-5.6-sol"
    assert rows["planner_high"]["reasoning_effort"] == "high"
    assert rows["worker_low"]["equivalence_status"] == "distinct"
    assert rows["worker_standard"]["equivalence_status"] == "distinct"
    assert rows["planner_high"]["equivalence_status"] == "equivalent"
    assert set(rows["planner_high"]["equivalent_tiers"]) == {
        "planner_high",
        "reviewer_standard",
    }


def test_provider_reasoning_capability_comes_from_canonical_mapping():
    assert mr.provider_reasoning_capability("native-codex") == "required"
    assert mr.provider_reasoning_capability("codex-session") == "required"
    assert mr.provider_reasoning_capability("codex-agent") == "unsupported"
    assert mr.provider_reasoning_capability("codex") == "unsupported"
    assert mr.provider_reasoning_capability("claude-agent") == "unsupported"
    assert mr.provider_reasoning_capability("unknown-provider") == "unknown"


def test_native_route_change_compares_model_and_reasoning(monkeypatch):
    for name in (
        "CODEX_NATIVE_WORKER_LOW_MODEL",
        "CODEX_NATIVE_WORKER_STANDARD_MODEL",
        "CODEX_NATIVE_WORKER_LOW_REASONING",
        "CODEX_NATIVE_WORKER_STANDARD_REASONING",
    ):
        monkeypatch.delenv(name, raising=False)

    planned = mr.resolve_provider_route(
        "native-codex",
        "worker_low",
        baseline_tier="worker_standard",
    )
    partial = mr.resolve_provider_route(
        "native-codex",
        "worker_low",
        baseline_tier="worker_standard",
        observed_model="gpt-5.6-terra",
    )
    observed = mr.resolve_provider_route(
        "native-codex",
        "worker_low",
        baseline_tier="worker_standard",
        observed_model="gpt-5.6-terra",
        observed_reasoning_effort="low",
    )

    assert planned["model_changed"] is False
    assert planned["route_changed"] is True
    assert planned["route_status"] == "effective"
    assert partial["application_status"] == "configured_unverified"
    assert partial["route_observation_status"] == "partial"
    assert observed["application_status"] == "applied"


def test_provider_env_accepts_pm_tier(monkeypatch):
    monkeypatch.setenv("CLAUDE_AGENT_OPUS_MODEL", "claude-opus-test")
    assert mr.provider_env("claude-agent", "planner_high") == {"CLAUDE_AGENT_MODEL": "claude-opus-test"}


def test_provider_env_claude_agent_latest_defaults(monkeypatch):
    monkeypatch.delenv("CLAUDE_AGENT_OPUS_MODEL", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_SONNET_MODEL", raising=False)
    assert mr.provider_env("claude-agent", "opus") == {"CLAUDE_AGENT_MODEL": "claude-opus-4-8"}
    assert mr.provider_env("claude-agent", "sonnet") == {"CLAUDE_AGENT_MODEL": "claude-sonnet-4-6"}


def test_provider_env_routes_codex_providers(monkeypatch):
    monkeypatch.delenv("CODEX_AGENT_SONNET_MODEL", raising=False)
    assert mr.provider_env("codex-agent", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-5.2-codex"}
    assert mr.provider_env("codex", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-5.2-codex"}


def test_provider_env_codex_env_override(monkeypatch):
    monkeypatch.setenv("CODEX_AGENT_SONNET_MODEL", "gpt-custom-codex")
    assert mr.provider_env("codex-agent", "sonnet") == {"CODEX_PROVIDER_MODEL": "gpt-custom-codex"}


def test_provider_env_unknown_provider_and_bare_claude():
    assert mr.provider_env("dummy", "sonnet") == {}
    assert mr.provider_env("claude", "sonnet") == {}
