"""Persona-diversity deliberation layer (org-delegation Unit 561, TASK-AR-561).

Extends blind-Delphi deliberation with persona archetypes that vary *substance* axes
(risk tolerance, time-horizon, values, domain lens, epistemic style) — research shows
diversity helps only when it is real and only in deliberation/review, never routine
execution. This module structures the flow and MEASURES diversity; the actual persona
opinions are generated at the assistant level (like agent_seminar.py).

Guards (from the research): blind isolation (each persona drafts before seeing peers),
diversity measurement (catch mode-collapse), and confidence-weighting + capture detection
(a confident wrong agent must not hijack consensus).

Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (step 5).
Personas are functional/epistemic (never demographic) to avoid encoding bias.
"""
from __future__ import annotations

import re

# Substance axes (not tone): risk_tolerance, time_horizon, values, domain_lens, epistemic.
PERSONAS: dict[str, dict] = {
    "skeptic": {"risk_tolerance": "low", "epistemic": "disconfirming",
                "domain_lens": "failure-modes", "values": "correctness",
                "stance": "Hunt hidden failure modes and weak evidence; default to refuted if unsure."},
    "pragmatist": {"risk_tolerance": "medium", "time_horizon": "short",
                   "values": "ship-speed", "domain_lens": "delivery",
                   "stance": "Optimize for shipping value now; challenge over-engineering."},
    "systems-thinker": {"time_horizon": "long", "domain_lens": "second-order",
                        "values": "maintainability",
                        "stance": "Trace feedback loops, coupling, and second-order effects."},
    "user-advocate": {"values": "user-trust", "domain_lens": "experience",
                      "stance": "Defend user trust and experience over internal convenience."},
    "empiricist": {"epistemic": "measurement", "values": "evidence",
                   "stance": "Demand baselines, measurement, and evidence; distrust intuition."},
    "first-principles": {"risk_tolerance": "high", "epistemic": "reframe",
                         "stance": "Reframe the problem and generate novel options."},
    "steward": {"domain_lens": "cost-risk-security", "values": "operational-reality",
                "stance": "Weigh budget, security, compliance, and operational burden."},
}


def persona_prompt(persona_id: str) -> str:
    p = PERSONAS[persona_id]
    axes = ", ".join(f"{k}={v}" for k, v in p.items() if k != "stance")
    return f"You are the '{persona_id}' persona ({axes}). {p['stance']}"


def blind_round(topic: str, persona_ids: list[str]) -> dict[str, str]:
    """Delphi round 1: each persona sees ONLY the topic + its own persona — never the
    others — so opinions form independently (no echo chamber / 85% conformity)."""
    out = {}
    for pid in persona_ids:
        out[pid] = (f"{persona_prompt(pid)}\n\nTopic:\n  {topic}\n\n"
                    "Submit your INDEPENDENT opinion + a confidence in [0,1]. "
                    "You cannot see any other participant's view in this round.")
    return out


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def diversity_score(texts: list[str]) -> float:
    """Average pairwise Jaccard distance of opinion token sets. 0 = identical (mode
    collapse), 1 = fully distinct. Real diversity, not just distinct labels."""
    sets = [_tokens(t) for t in texts if t.strip()]
    if len(sets) < 2:
        return 0.0
    dists, pairs = 0.0, 0
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            inter = sets[i] & sets[j]
            dists += 1.0 - (len(inter) / len(union) if union else 1.0)
            pairs += 1
    return round(dists / pairs, 3) if pairs else 0.0


def synthesize(submissions: list[dict], *, diversity_floor: float = 0.3) -> dict:
    """Confidence-weighted aggregation with diversity + capture guards.

    submissions: [{"persona", "opinion", "confidence" (0..1), "verdict"}]
    Returns structured inputs for an assistant-level Chairman synthesis — never adopts
    unanimity-as-truth.
    """
    texts = [s.get("opinion", "") for s in submissions]
    confs = [float(s.get("confidence", 0.5)) for s in submissions]
    diversity = diversity_score(texts)
    low_diversity = diversity < diversity_floor

    verdicts = [s.get("verdict") for s in submissions if s.get("verdict") is not None]
    majority = max(set(verdicts), key=verdicts.count) if verdicts else None
    minority = [s for s in submissions
                if s.get("verdict") is not None and s.get("verdict") != majority]

    # capture risk: one submission far more confident than the rest AND dissenting.
    capture_risk = False
    if len(confs) >= 2:
        top = max(confs)
        rest = sorted(confs)[:-1]
        median_rest = rest[len(rest) // 2]
        top_sub = submissions[confs.index(top)]
        if top > 2 * median_rest and top_sub.get("verdict") not in (None, majority):
            capture_risk = True

    ranked = sorted(submissions, key=lambda s: float(s.get("confidence", 0.5)), reverse=True)
    return {
        "diversity": diversity,
        "low_diversity": low_diversity,          # mode-collapse warning
        "majority_verdict": majority,
        "minority_views": minority,
        "capture_risk": capture_risk,            # confident-dissenter guard
        "ranked": ranked,
        "warnings": [w for w in (
            "low-diversity: possible mode collapse — re-prompt for distinct substance" if low_diversity else None,
            "capture-risk: a confident dissenter may hijack consensus — weight by track record" if capture_risk else None,
        ) if w],
    }
