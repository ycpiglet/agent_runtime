#!/usr/bin/env python3
"""Tests for cycle_gate.py (TASK-204, CYCLE-072)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cycle_gate as cg


def test_sql_is_critical_with_auditor():
    r = cg.evaluate(["Managed database/functions/create-user/index.ts"])
    assert r["grade"] == "Critical"
    assert "auditor" in r["required_subagents"]


def test_frontend_is_high_and_requires_beta():
    r = cg.evaluate(["public/app.js"])
    assert r["grade"] == "High"
    assert r["touches_frontend"] is True
    assert "beta-tester" in r["required_worker_roles"]
    assert "beta" not in r["required_subagents"]
    assert any("ROUNDS.md" in a for a in r["required_artifacts"])
    assert any("smoke" in a for a in r["required_artifacts"])


def test_gate_or_hook_change_is_high_with_skeptic():
    r = cg.evaluate(["scripts/check_agent_docs.py", "scripts/session_start_hook.py", ".claude/settings.json"])
    assert r["grade"] == "High"
    assert "skeptic" in r["required_subagents"]
    assert "doc-steward" in r["required_worker_roles"]


def test_docs_only_is_low_no_subagents():
    r = cg.evaluate(["agents/lead_engineer/reviews/REVIEW-072.md"])
    assert r["grade"] == "Low"
    assert r["required_subagents"] == []


def test_grade_is_max_across_files():
    r = cg.evaluate(["agents/x/notes/n.md", "public/app.js", "Managed database/x.sql"])
    assert r["grade"] == "Critical"  # sql dominates


def test_critical_requires_collab_evidence_artifact():
    r = cg.evaluate(["schema.sql"])
    assert any("협업 evidence" in a for a in r["required_artifacts"])


def test_windows_paths_are_normalized():
    r = cg.evaluate([r"public\app.js", r"Managed database\functions\x\index.ts"])
    assert r["grade"] == "Critical"
    assert r["touches_frontend"] is True
    assert "backend" in r["required_worker_roles"]
    assert "beta-tester" in r["required_worker_roles"]


def test_worker_roles_are_separate_from_subagents():
    r = cg.evaluate(["public/app.js"])
    assert set(r["required_subagents"]) == {"reviewer", "skeptic"}
    assert "uiux" in r["required_worker_roles"]


def test_evaluate_includes_routing_policy_model():
    r = cg.evaluate(["scripts/check_agent_docs.py"])
    assert cg.GRADE_POLICY["High"]["model"] == "sonnet"
    assert r["routing"]["policy_tier"] == "sonnet"
    assert r["routing"]["selected_tier"] == "sonnet"


def test_large_single_file_diff_routes_to_opus():
    r = cg.evaluate(["scripts/check_agent_docs.py"], diff_lines=700)
    assert r["grade"] == "High"
    assert r["routing"]["selected_tier"] == "opus"
    assert "large_diff" in r["routing"]["signals"]


def test_human_output_recommends_auto_model_routing(capsys):
    r = cg.evaluate(["scripts/check_agent_docs.py"])
    cg._print_human(r)
    out = capsys.readouterr().out
    assert "--model auto" in out
    assert "--grade High" in out


def test_human_output_explains_beta_round_evidence(capsys):
    r = cg.evaluate(["public/app.js"])
    cg._print_human(r)
    out = capsys.readouterr().out
    assert "ROUNDS.md clean/fail entry" in out
    assert "smoke/DOM-only evidence" in out


if __name__ == "__main__":
    import inspect

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = skipped = 0
    for fn in fns:
        # Tests taking pytest fixtures (capsys, tmp_path, ...) cannot run in
        # this plain runner; run the full file with `pytest` to include them.
        if inspect.signature(fn).parameters:
            skipped += 1
            print(f"SKIP {fn.__name__} (pytest fixtures; run via pytest)")
            continue
        fn()
        passed += 1
        print(f"PASS {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed, {skipped} pytest-only skipped")
