import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("persona_council", ROOT / "scripts" / "persona_council.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_seven_personas_vary_substance_axes():
    mod = _load()
    assert len(mod.PERSONAS) == 7
    # each persona carries at least one substance axis beyond its stance
    for pid, p in mod.PERSONAS.items():
        axes = [k for k in p if k != "stance"]
        assert axes, pid


def test_blind_round_isolates_each_persona():
    mod = _load()
    prompts = mod.blind_round("Should we ship X?", ["skeptic", "pragmatist"])
    # each prompt mentions its own persona but NOT the other's id (Delphi isolation)
    assert "skeptic" in prompts["skeptic"] and "pragmatist" not in prompts["skeptic"]
    assert "pragmatist" in prompts["pragmatist"] and "skeptic" not in prompts["pragmatist"]
    assert "Should we ship X?" in prompts["skeptic"]


def test_diversity_score_detects_mode_collapse():
    mod = _load()
    identical = ["the plan is good", "the plan is good"]
    distinct = ["security risk in auth flow", "ship fast, validate later with users"]
    assert mod.diversity_score(identical) == 0.0
    assert mod.diversity_score(distinct) > 0.5


def test_synthesize_flags_low_diversity_and_capture():
    mod = _load()
    # low diversity: near-identical opinions -> mode-collapse warning
    collapsed = mod.synthesize([
        {"persona": "a", "opinion": "approve it", "confidence": 0.6, "verdict": "approve"},
        {"persona": "b", "opinion": "approve it", "confidence": 0.6, "verdict": "approve"},
    ])
    assert collapsed["low_diversity"] is True
    assert any("low-diversity" in w for w in collapsed["warnings"])

    # capture risk: one very-confident dissenter vs the majority
    captured = mod.synthesize([
        {"persona": "a", "opinion": "security hole in token refresh path", "confidence": 0.99, "verdict": "block"},
        {"persona": "b", "opinion": "ship it, looks fine to me", "confidence": 0.3, "verdict": "approve"},
        {"persona": "c", "opinion": "approve, ready for users", "confidence": 0.3, "verdict": "approve"},
    ])
    assert captured["majority_verdict"] == "approve"
    assert captured["capture_risk"] is True
    assert [m["persona"] for m in captured["minority_views"]] == ["a"]
