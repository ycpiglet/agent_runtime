#!/usr/bin/env python3
"""Provider-aware model routing and deterministic-first dispatch policy.

PM tiers are the stable repository contract.  Haiku/sonnet/opus are retained
as compatibility aliases for older Claude-facing records; they are not treated
as proof that another provider changed models.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterable, Mapping
from typing import Any


GRADE_POLICY = {
    "Low": "haiku",
    "Medium": "sonnet",
    "High": "sonnet",
    "Critical": "opus",
}

TIER_ORDER = {"haiku": 1, "sonnet": 2, "opus": 3}

CLAUDE_AGENT_MODEL_ENV = {
    "haiku": ("CLAUDE_AGENT_HAIKU_MODEL", "claude-haiku-4-5"),
    "sonnet": ("CLAUDE_AGENT_SONNET_MODEL", "claude-sonnet-4-6"),
    "opus": ("CLAUDE_AGENT_OPUS_MODEL", "claude-opus-4-8"),
}

# Codex (OpenAI Responses) routing. gpt-5.2-codex is the only codex model defined
# in this repo, so every tier defaults to it; the env-override names let the Owner
# pin tier-specific codex models later without code changes. This plumbing lets
# difficulty->model routing reach the codex/codex-agent providers (was a no-op).
CODEX_AGENT_MODEL_ENV = {
    "haiku": ("CODEX_AGENT_HAIKU_MODEL", "gpt-5.2-codex"),
    "sonnet": ("CODEX_AGENT_SONNET_MODEL", "gpt-5.2-codex"),
    "opus": ("CODEX_AGENT_OPUS_MODEL", "gpt-5.2-codex"),
}

NATIVE_CODEX_MODEL_ENV = {
    "worker_low": (
        "CODEX_NATIVE_WORKER_LOW_MODEL",
        "gpt-5.6-terra",
        "CODEX_NATIVE_WORKER_LOW_REASONING",
        "low",
    ),
    "worker_standard": (
        "CODEX_NATIVE_WORKER_STANDARD_MODEL",
        "gpt-5.6-terra",
        "CODEX_NATIVE_WORKER_STANDARD_REASONING",
        "medium",
    ),
    "planner_high": (
        "CODEX_NATIVE_STRONG_MODEL",
        "gpt-5.6-sol",
        "CODEX_NATIVE_PLANNER_HIGH_REASONING",
        "high",
    ),
    "reviewer_standard": (
        "CODEX_NATIVE_STRONG_MODEL",
        "gpt-5.6-sol",
        "CODEX_NATIVE_REVIEWER_STANDARD_REASONING",
        "high",
    ),
    "reviewer_high": (
        "CODEX_NATIVE_STRONG_MODEL",
        "gpt-5.6-sol",
        "CODEX_NATIVE_REVIEWER_HIGH_REASONING",
        "xhigh",
    ),
}

# provider name -> (provider env var carrying the resolved model, tier->model map).
# Any provider absent from this table (incl. bare "claude") gets no routed model.
PROVIDER_MODEL_ENV = {
    "claude-agent": ("CLAUDE_AGENT_MODEL", CLAUDE_AGENT_MODEL_ENV),
    "codex-agent": ("CODEX_PROVIDER_MODEL", CODEX_AGENT_MODEL_ENV),
    "codex": ("CODEX_PROVIDER_MODEL", CODEX_AGENT_MODEL_ENV),
}

PM_TIER_TO_PROVIDER_TIER = {
    "worker_low": "haiku",
    "worker_standard": "sonnet",
    "planner_high": "opus",
    "reviewer_standard": "sonnet",
    "reviewer_high": "opus",
}

ALLOWED_PM_TIERS = set(PM_TIER_TO_PROVIDER_TIER)
ESCALATION_TRIGGERS = {
    "ambiguity",
    "data_integrity",
    "high_risk",
    "security",
    "cross_cutting",
    "external_effect",
    "repeated_failure",
}
HIGH_TIER_TRIGGERS = {
    "ambiguity",
    "data_integrity",
    "high_risk",
    "security",
    "cross_cutting",
    "external_effect",
    "repeated_failure",
}

HIGH_PM_TIERS = {"planner_high", "reviewer_high"}

# Explicit economic policy for every role family used by the Runtime.  Aliases
# intentionally live here instead of falling through to ``worker_standard`` so
# a Scribe or research call cannot silently become a generic, more expensive
# worker.  A high default is itself a registered policy reason; a low/standard
# role may reach a high tier only through a registered escalation trigger.
ROLE_TIER_POLICIES = {
    "scribe": {
        "tier": "worker_low",
        "aliases": (
            "scribe",
            "archivist",
            "documentation",
            "doc-steward",
            "doc_steward",
        ),
        "reason": "bounded documentation and state projection policy",
    },
    "exploration": {
        "tier": "worker_low",
        "aliases": (
            "explorer",
            "exploration",
            "research",
            "researcher",
            "scout",
            "timeline",
            "timeline-agent",
            "progress-scout",
            "progress_scout",
        ),
        "reason": "read-only exploration and deterministic-first research policy",
    },
    "implementation": {
        "tier": "worker_low",
        "aliases": (
            "implementer",
            "implementation",
            "backend",
            "ci-cd",
            "cicd",
            "frontend",
            "uiux",
        ),
        "reason": "bounded implementation unit policy",
    },
    "review": {
        "tier": "reviewer_standard",
        "aliases": (
            "reviewer",
            "review",
            "qa",
            "qa-reviewer",
            "qa_reviewer",
            "beta-tester",
        ),
        "reason": "independent review policy",
    },
    "audit": {
        "tier": "reviewer_high",
        "aliases": (
            "auditor",
            "audit",
            "independent-auditor",
            "independent_auditor",
            "skeptic",
        ),
        "reason": "registered adversarial audit policy",
    },
    "planning": {
        "tier": "planner_high",
        "aliases": (
            "strategist",
            "planner",
            "architect",
        ),
        "reason": "registered architecture and planning policy",
    },
}


def _role_key(value: str) -> str:
    return str(value or "").strip().lower().replace("_", "-")


ROLE_POLICY_BY_ALIAS = {
    _role_key(alias): {
        "policy_id": policy_id,
        "canonical_role": policy_id,
        "tier": str(policy["tier"]),
        "reason": str(policy["reason"]),
    }
    for policy_id, policy in ROLE_TIER_POLICIES.items()
    for alias in policy["aliases"]
}

# Compatibility surface used by older callers/tests.
SUBAGENT_ROLE_PM_TIER = {
    alias: str(policy["tier"]) for alias, policy in ROLE_POLICY_BY_ALIAS.items()
}

PREFLIGHT_STATUSES = {
    "not_required",
    "attempted_insufficient",
    "completed_sufficient",
}

SIMPLE_LOOKUP_RE = re.compile(
    r"\b(find|list|read|search|locate|show|grep|rg|status|lookup)\b",
    re.I,
)
DEEP_REASONING_RE = re.compile(
    r"\b(why|investigate|design|architecture|root[- ]?cause|deep|"
    r"threat|security|migration|row-level policy|complex)\b",
    re.I,
)

LARGE_FILE_COUNT = 8
LARGE_DIFF_LINES = 600


def normalize_grade(grade: str | None) -> str:
    if grade in GRADE_POLICY:
        return str(grade)
    return "Medium"


def normalize_tier(tier: str | None) -> str:
    value = str(tier or "").strip().lower()
    if value not in TIER_ORDER:
        raise ValueError(f"unknown model tier '{tier}'. expected one of {sorted(TIER_ORDER)}")
    return value


def normalize_pm_tier(tier: str | None, *, default: str = "worker_standard") -> str:
    value = str(tier or default).strip()
    if value not in ALLOWED_PM_TIERS:
        raise ValueError(f"unknown PM model tier '{tier}'. expected one of {sorted(ALLOWED_PM_TIERS)}")
    return value


def infer_tier(model_or_tier: str | None) -> str | None:
    """Infer haiku/sonnet/opus from a tier or provider model name."""
    value = str(model_or_tier or "").strip().lower()
    if value in TIER_ORDER:
        return value
    for tier in TIER_ORDER:
        if tier in value:
            return tier
    return None


def _signals(
    prompt: str = "",
    changed_files: Iterable[str] | None = None,
    diff_lines: int = 0,
) -> list[str]:
    signals: list[str] = []
    text = prompt or ""
    if SIMPLE_LOOKUP_RE.search(text):
        signals.append("simple_lookup")
    if DEEP_REASONING_RE.search(text):
        signals.append("deep_reasoning")
    files = list(changed_files or [])
    if len(files) >= LARGE_FILE_COUNT:
        signals.append("large_file_count")
    if int(diff_lines or 0) >= LARGE_DIFF_LINES:
        signals.append("large_diff")
    return signals


def select_model(
    grade: str | None,
    *,
    prompt: str = "",
    changed_files: Iterable[str] | None = None,
    diff_lines: int = 0,
) -> dict[str, Any]:
    """Return a routing decision dict for a task grade and prompt/surface signals."""
    normalized_grade = normalize_grade(grade)
    policy_tier = GRADE_POLICY[normalized_grade]
    signals = _signals(prompt, changed_files, diff_lines)

    selected_tier = policy_tier
    if any(s in signals for s in ("deep_reasoning", "large_file_count", "large_diff")):
        selected_tier = "opus"
    elif "simple_lookup" in signals and normalized_grade != "Critical":
        selected_tier = "haiku"

    return {
        "grade": normalized_grade,
        "policy_tier": policy_tier,
        "selected_tier": selected_tier,
        "signals": signals,
        "reason": _reason(policy_tier, selected_tier, signals),
    }


def resolve_model(
    model: str | None,
    *,
    grade: str | None = None,
    prompt: str = "",
    changed_files: Iterable[str] | None = None,
    diff_lines: int = 0,
) -> dict[str, Any]:
    """Resolve `auto` or an explicit tier into the common decision shape."""
    value = str(model or "auto").strip().lower()
    if value in {"", "auto"}:
        return select_model(
            grade,
            prompt=prompt,
            changed_files=changed_files,
            diff_lines=diff_lines,
        )
    normalized_grade = normalize_grade(grade)
    policy_tier = GRADE_POLICY[normalized_grade]
    inferred_tier = infer_tier(value)
    if inferred_tier is None:
        selected_tier = value
        signals = ["manual_override", "raw_provider_model"]
        if normalized_grade == "Critical":
            selected_tier = policy_tier
            signals.append("critical_floor")
        return {
            "grade": normalized_grade,
            "policy_tier": policy_tier,
            "selected_tier": selected_tier,
            "signals": signals,
            "reason": (
                f"manual override to {value}; Critical floor kept {policy_tier}"
                if selected_tier != value
                else f"manual override to provider model {value}"
            ),
        }
    tier = inferred_tier
    signals = ["manual_override"]
    selected_tier = tier if value == tier else value
    if normalized_grade == "Critical" and TIER_ORDER[tier] < TIER_ORDER[policy_tier]:
        selected_tier = policy_tier
        signals.append("critical_floor")
    return {
        "grade": normalized_grade,
        "policy_tier": policy_tier,
        "selected_tier": selected_tier,
        "signals": signals,
        "reason": (
            f"manual override to {tier}; Critical floor kept {policy_tier}"
            if selected_tier != tier
            else f"manual override to {tier}"
        ),
    }


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [part.strip() for part in str(value).split(",") if part.strip()]


def resolve_work_item_tier(
    task_meta: Mapping[str, Any] | None = None,
    unit_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve planner/worker/reviewer PM tiers for a task or unit record.

    Unit metadata wins over task metadata. Escalation triggers intentionally
    move low-tier worker assignments to `planner_high`; this prevents a worker
    from silently expanding ambiguous or high-risk scope.
    """
    task = dict(task_meta or {})
    unit = dict(unit_meta or {})
    requested = unit.get("model_tier") or unit.get("worker_model_tier") or task.get("worker_model_tier")
    requested_tier = normalize_pm_tier(str(requested or "worker_standard"))
    triggers = sorted(set(_as_list(task.get("escalation_triggers")) + _as_list(unit.get("escalation_triggers"))))
    unknown_triggers = [trigger for trigger in triggers if trigger not in ESCALATION_TRIGGERS]
    registered_triggers = sorted(set(triggers) & HIGH_TIER_TRIGGERS)
    selected_tier = requested_tier
    escalated = bool(registered_triggers)
    if escalated and requested_tier.startswith("worker_"):
        selected_tier = "planner_high"
    provider_tier = PM_TIER_TO_PROVIDER_TIER[selected_tier]
    registered_reason = None
    if selected_tier in HIGH_PM_TIERS:
        registered_reason = (
            "trigger:" + ",".join(registered_triggers)
            if selected_tier != requested_tier
            else f"task_unit_declared_tier:{requested_tier}"
        )
    return {
        "routing_policy_id": "task-unit-tier-policy",
        "routing_policy_reason": (
            "unit tier overrides task tier; registered high-risk triggers gate "
            "worker escalation"
        ),
        "requested_tier": requested_tier,
        "selected_tier": selected_tier,
        "provider_tier": provider_tier,
        "escalation_triggers": triggers,
        "registered_escalation_triggers": registered_triggers,
        "unknown_triggers": unknown_triggers,
        "high_tier_requested": requested_tier in HIGH_PM_TIERS,
        "high_tier_authorized": (
            selected_tier not in HIGH_PM_TIERS or registered_reason is not None
        ),
        "registered_escalation_reason": registered_reason,
        "reason": (
            "escalated to planner_high by task/unit trigger"
            if selected_tier != requested_tier
            else "task/unit tier policy"
        ),
    }


def resolve_subagent_tier(
    role_id: str,
    *,
    requested_tier: str | None = None,
    escalation_triggers: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Resolve a subagent role into a PM tier without naming a provider model."""
    role = _role_key(role_id)
    policy = ROLE_POLICY_BY_ALIAS.get(
        role,
        {
            "policy_id": "generic-worker",
            "canonical_role": "generic-worker",
            "tier": "worker_standard",
            "reason": "generic worker fallback",
        },
    )
    default = str(policy["tier"])
    raw_requested = str(requested_tier or "").strip().lower()
    if raw_requested in {"", "auto"}:
        requested = default
    else:
        compatible = _tier_from_compatibility(raw_requested)
        if compatible is None:
            raise ValueError(
                "role-bound dispatch requires a PM tier or "
                "haiku/sonnet/opus compatibility tier"
            )
        if compatible == "planner_high" and default.startswith("reviewer_"):
            compatible = "reviewer_high"
        requested = normalize_pm_tier(compatible, default=default)
    triggers = sorted(set(_as_list(escalation_triggers)))
    unknown = [trigger for trigger in triggers if trigger not in ESCALATION_TRIGGERS]
    matched = sorted(set(triggers) & HIGH_TIER_TRIGGERS)
    selected = requested
    high_request_denied = False
    if (
        requested in HIGH_PM_TIERS
        and default not in HIGH_PM_TIERS
        and not matched
    ):
        selected = default
        high_request_denied = True
    if matched:
        if requested.startswith("worker_"):
            selected = "planner_high"
        elif requested == "reviewer_standard":
            selected = "reviewer_high"
    registered_reason = None
    if selected in HIGH_PM_TIERS:
        if default in HIGH_PM_TIERS:
            registered_reason = f"role_policy:{policy['policy_id']}"
        elif matched:
            registered_reason = "trigger:" + ",".join(matched)
    routing_status = (
        "unverified"
        if unknown
        else "high_tier_denied"
        if high_request_denied
        else "escalated"
        if selected != requested
        else "selected"
    )
    return {
        "role": role,
        "canonical_role": policy["canonical_role"],
        "role_policy_id": policy["policy_id"],
        "role_policy_status": (
            "explicit" if role in ROLE_POLICY_BY_ALIAS else "generic_fallback"
        ),
        "role_policy_reason": policy["reason"],
        "grade": "RolePolicy",
        "policy_tier": default,
        "signals": triggers,
        "default_tier": default,
        "requested_tier": requested,
        "selected_tier": selected,
        "provider_tier": PM_TIER_TO_PROVIDER_TIER[selected],
        "escalation_triggers": triggers,
        "registered_escalation_triggers": matched,
        "unknown_triggers": unknown,
        "routing_status": routing_status,
        "high_tier_requested": requested in HIGH_PM_TIERS,
        "high_tier_authorized": (
            selected not in HIGH_PM_TIERS or registered_reason is not None
        ),
        "registered_escalation_reason": registered_reason,
        "denied_requested_tier": requested if high_request_denied else None,
        "reason": (
            "unknown escalation trigger requires review"
            if unknown
            else "high tier denied without a registered role policy or escalation trigger"
            if high_request_denied
            else "escalated by registered high-risk trigger"
            if selected != requested
            else str(policy["reason"])
        ),
    }


def deterministic_preflight(
    prompt: str,
    *,
    status: str | None = None,
    evidence: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Return the deterministic-first gate for a possible model dispatch.

    Lookup-only work must either finish without a model call or carry bounded
    evidence that deterministic tools were attempted and were insufficient.
    This function records policy only; it never executes a tool.
    """
    signals = _signals(prompt)
    required = "simple_lookup" in signals and "deep_reasoning" not in signals
    supplied = str(status or "").strip().lower()
    items = _as_list(evidence)
    if not required:
        effective = supplied if supplied in PREFLIGHT_STATUSES else "not_required"
        allow = effective != "completed_sufficient"
        return {
            "required": False,
            "status": effective,
            "evidence": items,
            "allow_dispatch": allow,
            "dispatch_required": allow,
            "reason": (
                "deterministic work completed; no model dispatch"
                if not allow
                else "deterministic preflight not required"
            ),
        }
    if supplied == "completed_sufficient":
        return {
            "required": True,
            "status": supplied,
            "evidence": items,
            "allow_dispatch": False,
            "dispatch_required": False,
            "reason": "deterministic work completed sufficiently; no model dispatch",
        }
    if supplied == "attempted_insufficient" and items:
        return {
            "required": True,
            "status": supplied,
            "evidence": items,
            "allow_dispatch": True,
            "dispatch_required": True,
            "reason": "bounded deterministic attempt was insufficient",
        }
    return {
        "required": True,
        "status": "required_unresolved",
        "evidence": items,
        "allow_dispatch": False,
        "dispatch_required": False,
        "reason": (
            "attempted_insufficient requires bounded evidence"
            if supplied == "attempted_insufficient"
            else "lookup-only dispatch requires deterministic preflight"
        ),
    }


def _provider_mapping(
    provider_name: str,
    pm_tier: str,
) -> dict[str, Any] | None:
    provider = str(provider_name or "").strip().lower()
    if provider in {"native-codex", "codex-session", "codex-native"}:
        model_env, default_model, reasoning_env, default_reasoning = NATIVE_CODEX_MODEL_ENV[pm_tier]
        model_is_override = model_env in os.environ
        reasoning_is_override = reasoning_env in os.environ
        return {
            "provider": "native-codex",
            "execution_surface": "native_subagent_spawn",
            "resolved_model": os.environ.get(model_env, default_model),
            "model_source": (
                f"environment:{model_env}"
                if model_is_override
                else f"adapter_default:{model_env}"
            ),
            "reasoning_effort": os.environ.get(reasoning_env, default_reasoning),
            "reasoning_source": (
                f"environment:{reasoning_env}"
                if reasoning_is_override
                else f"adapter_default:{reasoning_env}"
            ),
        }
    mapping = PROVIDER_MODEL_ENV.get(provider)
    if mapping is None:
        return None
    env_var_name, tier_map = mapping
    provider_tier = PM_TIER_TO_PROVIDER_TIER[pm_tier]
    env_name, default_model = tier_map[provider_tier]
    return {
        "provider": provider,
        "execution_surface": "provider_worker",
        "resolved_model": os.environ.get(env_name, default_model),
        "model_source": (
            f"environment:{env_name}"
            if env_name in os.environ
            else f"adapter_default:{env_name}"
        ),
        "reasoning_effort": None,
        "reasoning_source": "unsupported",
        "provider_env_name": env_var_name,
    }


def _tier_from_compatibility(value: str | None) -> str | None:
    text = str(value or "").strip().lower()
    if text in ALLOWED_PM_TIERS:
        return text
    return {
        "haiku": "worker_low",
        "sonnet": "worker_standard",
        "opus": "planner_high",
    }.get(text)


def provider_routing_matrix(provider_name: str) -> dict[str, Any]:
    """Describe configured tier mappings without making a provider call."""
    rows: list[dict[str, Any]] = []
    groups: dict[tuple[str, str | None], list[str]] = {}
    for tier in PM_TIER_TO_PROVIDER_TIER:
        resolved = _provider_mapping(provider_name, tier)
        if resolved is None:
            continue
        identity = (
            str(resolved["resolved_model"]),
            (
                str(resolved["reasoning_effort"])
                if resolved.get("reasoning_effort") is not None
                else None
            ),
        )
        groups.setdefault(identity, []).append(tier)
        rows.append(
            {
                "pm_tier": tier,
                "provider_tier": PM_TIER_TO_PROVIDER_TIER[tier],
                **resolved,
                "resolved_route_identity": {
                    "model": identity[0],
                    "reasoning_effort": identity[1],
                },
                "availability_status": "configured_unverified",
            }
        )
    for row in rows:
        identity = (
            str(row["resolved_model"]),
            (
                str(row["reasoning_effort"])
                if row.get("reasoning_effort") is not None
                else None
            ),
        )
        equivalent = groups[identity]
        row["equivalent_tiers"] = list(equivalent)
        row["equivalence_status"] = (
            "equivalent" if len(equivalent) > 1 else "distinct"
        )
        row["route_status"] = (
            "ineffective_equivalent" if len(equivalent) > 1 else "unverified"
        )
        row["economic_claim_status"] = (
            "ineligible_equivalent" if len(equivalent) > 1 else "unverified"
        )
    return {
        "provider": (
            "native-codex"
            if str(provider_name).lower() in {"native-codex", "codex-session", "codex-native"}
            else str(provider_name)
        ),
        "status": "configured_unverified" if rows else "unsupported",
        "rows": rows,
        "equivalence_groups": [
            {
                "resolved_model": identity[0],
                "reasoning_effort": identity[1],
                "route_identity": {
                    "model": identity[0],
                    "reasoning_effort": identity[1],
                },
                "tiers": tiers,
            }
            for identity, tiers in sorted(
                groups.items(), key=lambda item: (item[0][0], item[0][1] or "")
            )
            if len(tiers) > 1
        ],
    }


def resolve_provider_route(
    provider_name: str,
    selected_tier: str,
    *,
    requested_tier: str | None = None,
    baseline_tier: str | None = None,
    baseline_model: str | None = None,
    baseline_reasoning_effort: str | None = None,
    observed_model: str | None = None,
    observed_reasoning_effort: str | None = None,
) -> dict[str, Any]:
    """Resolve configured provider/native intent and optional observations.

    ``resolved_model`` is configuration intent.  ``observed_model`` is only
    populated from an explicit completion observation supplied by the caller.
    The latter is never inferred from a tier, callsign, or request environment.
    """
    selected_pm = _tier_from_compatibility(selected_tier)
    requested_pm = _tier_from_compatibility(requested_tier) or selected_pm
    if selected_pm is None:
        mapping = PROVIDER_MODEL_ENV.get(str(provider_name or "").strip().lower())
        if mapping is None:
            return {
                "provider": str(provider_name or ""),
                "execution_surface": "unsupported",
                "requested_tier": str(requested_tier or selected_tier),
                "selected_tier": str(selected_tier),
                "provider_tier": None,
                "resolved_model": None,
                "model_source": "unsupported",
                "reasoning_effort": None,
                "reasoning_source": "unsupported",
                "availability_status": "unsupported",
                "route_status": "unsupported",
                "application_status": "not_applied",
                "economic_claim_status": "ineligible_unsupported",
                "observed_model": observed_model,
                "observed_reasoning_effort": observed_reasoning_effort,
                "model_observation_status": (
                    "observed" if observed_model else "unverified"
                ),
                "model_changed": None,
                "route_changed": None,
                "resolved_route_identity": None,
                "baseline_route_identity": None,
                "observed_route_identity": None,
                "route_observation_status": "unverified",
            }
        env_var_name, _tier_map = mapping
        raw_model = str(selected_tier).strip()
        return {
            "provider": str(provider_name),
            "execution_surface": "provider_worker",
            "requested_tier": str(requested_tier or selected_tier),
            "selected_tier": str(selected_tier),
            "provider_tier": None,
            "resolved_model": raw_model,
            "model_source": "explicit_model",
            "provider_env": {env_var_name: raw_model},
            "reasoning_effort": None,
            "reasoning_source": "unsupported",
            "availability_status": "configured_unverified",
            "route_status": "unverified",
            "application_status": (
                "applied" if observed_model == raw_model else
                "not_applied" if observed_model else "configured_unverified"
            ),
            "economic_claim_status": "unverified",
            "observed_model": observed_model,
            "observed_reasoning_effort": observed_reasoning_effort,
            "model_observation_status": "observed" if observed_model else "unverified",
            "model_changed": None,
            "route_changed": None,
            "resolved_route_identity": {
                "model": raw_model,
                "reasoning_effort": None,
            },
            "baseline_route_identity": None,
            "observed_route_identity": (
                {
                    "model": observed_model,
                    "reasoning_effort": observed_reasoning_effort,
                }
                if observed_model
                else None
            ),
            "route_observation_status": (
                "observed" if observed_model else "unverified"
            ),
        }

    resolved = _provider_mapping(provider_name, selected_pm)
    if resolved is None:
        return resolve_provider_route(
            provider_name,
            "__unsupported__",
            requested_tier=requested_tier,
            baseline_reasoning_effort=baseline_reasoning_effort,
            observed_model=observed_model,
            observed_reasoning_effort=observed_reasoning_effort,
        )
    matrix = provider_routing_matrix(provider_name)
    row = next(item for item in matrix["rows"] if item["pm_tier"] == selected_pm)
    comparison_model = str(baseline_model or "").strip() or None
    comparison_reasoning = (
        str(baseline_reasoning_effort or "").strip() or None
    )
    comparison_source = "explicit_baseline_model" if comparison_model else None
    if comparison_model is None and baseline_tier:
        baseline_pm = _tier_from_compatibility(baseline_tier)
        baseline = _provider_mapping(provider_name, baseline_pm) if baseline_pm else None
        if baseline:
            comparison_model = str(baseline["resolved_model"])
            comparison_reasoning = (
                str(baseline["reasoning_effort"])
                if baseline.get("reasoning_effort") is not None
                else None
            )
            comparison_source = f"baseline_tier:{baseline_pm}"
    if comparison_model is None and requested_pm and requested_pm != selected_pm:
        requested = _provider_mapping(provider_name, requested_pm)
        if requested:
            comparison_model = str(requested["resolved_model"])
            comparison_reasoning = (
                str(requested["reasoning_effort"])
                if requested.get("reasoning_effort") is not None
                else None
            )
            comparison_source = f"requested_tier:{requested_pm}"
    reasoning_required = resolved.get("reasoning_source") != "unsupported"
    resolved_identity = {
        "model": str(resolved["resolved_model"]),
        "reasoning_effort": (
            str(resolved["reasoning_effort"])
            if resolved.get("reasoning_effort") is not None
            else None
        ),
    }
    baseline_identity = (
        {
            "model": comparison_model,
            "reasoning_effort": comparison_reasoning,
        }
        if comparison_model is not None
        else None
    )
    baseline_complete = bool(comparison_model) and (
        not reasoning_required or comparison_reasoning is not None
    )
    observed_identity = (
        {
            "model": str(observed_model),
            "reasoning_effort": (
                str(observed_reasoning_effort)
                if observed_reasoning_effort is not None
                else None
            ),
        }
        if observed_model
        else None
    )
    observation_complete = bool(observed_model) and (
        not reasoning_required or observed_reasoning_effort is not None
    )
    model_changed = (
        None
        if comparison_model is None
        else comparison_model != str(resolved["resolved_model"])
    )
    route_changed = (
        None
        if not baseline_complete
        else baseline_identity != resolved_identity
    )
    if route_changed is True:
        route_status = "effective"
    elif route_changed is False or row["equivalence_status"] == "equivalent":
        route_status = "ineffective_equivalent"
    else:
        route_status = "unverified"
    application_status = "configured_unverified"
    if observation_complete:
        application_status = (
            "applied"
            if observed_identity == resolved_identity
            else "not_applied"
        )
    economic_status = "unverified"
    if route_changed is False or row["equivalence_status"] == "equivalent":
        economic_status = "ineligible_equivalent"
    elif application_status == "applied" and route_changed is True:
        economic_status = "needs_usage_evidence"
    elif application_status == "not_applied":
        economic_status = "ineligible_not_applied"
    provider_env_value: dict[str, str] = {}
    if resolved.get("provider_env_name"):
        provider_env_value[str(resolved["provider_env_name"])] = str(
            resolved["resolved_model"]
        )
    return {
        "provider": resolved["provider"],
        "execution_surface": resolved["execution_surface"],
        "requested_tier": requested_pm or str(requested_tier or selected_tier),
        "selected_tier": selected_pm,
        "provider_tier": PM_TIER_TO_PROVIDER_TIER[selected_pm],
        "resolved_model": resolved["resolved_model"],
        "model_source": resolved["model_source"],
        "provider_env": provider_env_value,
        "reasoning_effort": resolved["reasoning_effort"],
        "reasoning_source": resolved["reasoning_source"],
        "baseline_model": comparison_model,
        "baseline_reasoning_effort": comparison_reasoning,
        "baseline_model_source": comparison_source,
        "resolved_route_identity": resolved_identity,
        "baseline_route_identity": baseline_identity,
        "observed_route_identity": observed_identity,
        "equivalent_tiers": row["equivalent_tiers"],
        "equivalence_status": row["equivalence_status"],
        "model_changed": model_changed,
        "route_changed": route_changed,
        "availability_status": "configured_unverified",
        "route_status": route_status,
        "application_status": application_status,
        "economic_claim_status": economic_status,
        "observed_model": observed_model,
        "observed_reasoning_effort": observed_reasoning_effort,
        "model_observation_status": "observed" if observed_model else "unverified",
        "route_observation_status": (
            "observed"
            if observation_complete
            else "partial"
            if observed_model
            else "unverified"
        ),
    }


def provider_env(provider_name: str, tier_or_model: str) -> dict[str, str]:
    """Return environment variables needed for a provider to use a routed tier.

    Each routed provider (claude-agent, codex, codex-agent) carries its resolved
    model in a single env var (PROVIDER_MODEL_ENV). Resolution order per provider:
    tier name in its tier_map -> env-overridable model; else PM tier mapped to a
    tier -> tier_map model; else a raw model passthrough; else {}. Providers not
    in the table (incl. bare "claude") get no routed model.
    """
    mapping = PROVIDER_MODEL_ENV.get(provider_name)
    if mapping is None:
        return {}
    env_var_name, tier_map = mapping
    value = str(tier_or_model or "").strip()
    lower = value.lower()
    if lower in tier_map:
        env_name, default_model = tier_map[lower]
        return {env_var_name: os.environ.get(env_name, default_model)}
    if lower in PM_TIER_TO_PROVIDER_TIER:
        env_name, default_model = tier_map[PM_TIER_TO_PROVIDER_TIER[lower]]
        return {env_var_name: os.environ.get(env_name, default_model)}
    if value:
        return {env_var_name: value}
    return {}


def _reason(policy_tier: str, selected_tier: str, signals: list[str]) -> str:
    if selected_tier == policy_tier and not signals:
        return "grade policy"
    if selected_tier == policy_tier:
        return "grade policy retained despite signals"
    if selected_tier == "opus":
        return "escalated by prompt/surface signal"
    if selected_tier == "haiku":
        return "downrouted by simple lookup signal"
    return "routed by policy"
