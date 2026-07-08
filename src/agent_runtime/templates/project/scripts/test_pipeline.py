"""Pipeline transition + verdict-parsing tests (TASK-111 track B).

Regression guard for the raw-string double-escape bug: `_VERDICT_RE` shipped as
`r"...\\s...\\w..."`, which matches a literal backslash and made parse_verdict
always return None — so every gate silently fell back to `needs-changes`. These
tests would have caught that at release time.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("_pipeline", ROOT / "scripts" / "pipeline.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


pl = _load()


# ---- parse_verdict (the shipped-bug regression) ----

def test_parse_verdict_basic():
    assert pl.parse_verdict("VERDICT: pass") == "pass"


def test_parse_verdict_is_case_insensitive_token_and_keyword():
    assert pl.parse_verdict("verdict: PASS") == "pass"
    assert pl.parse_verdict("VERDICT: Needs-Changes") == "needs-changes"


def test_parse_verdict_hyphenated_token():
    assert pl.parse_verdict("VERDICT: needs-changes") == "needs-changes"


def test_parse_verdict_at_end_of_multiline_reply():
    reply = "did the work\nran tests, all green\n\nVERDICT: done\n"
    assert pl.parse_verdict(reply) == "done"


def test_parse_verdict_returns_last_when_multiple():
    reply = "VERDICT: needs-changes\n...second pass...\nVERDICT: pass\n"
    assert pl.parse_verdict(reply) == "pass"


def test_parse_verdict_tolerates_surrounding_whitespace():
    assert pl.parse_verdict("   VERDICT:   pass   ") == "pass"


def test_parse_verdict_none_when_absent():
    assert pl.parse_verdict("no verdict line here") is None
    assert pl.parse_verdict("") is None
    assert pl.parse_verdict(None) is None


def test_parse_verdict_ignores_inline_mentions():
    # Must be at line start; a mid-sentence mention is not a verdict.
    assert pl.parse_verdict("the reviewer will emit VERDICT: pass later") is None


# ---- decide(): gate uses the parsed verdict ----

def test_gate_pass_advances_to_commit():
    d = pl.decide("build", "review", "pass", loopbacks=0)
    assert d.action == "advance" and d.target.name == "commit"


def test_gate_needs_changes_loops_back_to_first_stage():
    d = pl.decide("build", "review", "needs-changes", loopbacks=0)
    assert d.action == "loopback" and d.target.name == "implement" and d.loopbacks == 1


def test_gate_missing_verdict_defaults_conservative():
    # None verdict at a gate must behave as needs-changes, not silently pass.
    d = pl.decide("build", "review", None, loopbacks=0)
    assert d.action == "loopback"


def test_gate_halts_when_loop_cap_exceeded():
    d = pl.decide("build", "review", "needs-changes", loopbacks=pl.DEFAULT_LOOP_CAP)
    assert d.action == "halt"


def test_work_stage_advances():
    d = pl.decide("build", "implement", None, loopbacks=0)
    assert d.action == "advance" and d.target.name == "review"


def test_last_work_stage_completes():
    d = pl.decide("build", "commit", None, loopbacks=0)
    assert d.action == "complete" and d.target is None


# ---- compute_next(): verdict flows end-to-end ----

def test_compute_next_gate_pass_routes_to_commit():
    meta = {"pipeline": "build", "stage": "review", "loopbacks": 0, "task_id": "T-1"}
    nxt = pl.compute_next(meta, "looks correct\nVERDICT: pass", [])
    assert nxt is not None and nxt.stage == "commit" and nxt.kind == "request"


def test_compute_next_no_pipeline_returns_none():
    assert pl.compute_next({}, "VERDICT: pass", []) is None
