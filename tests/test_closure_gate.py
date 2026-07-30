"""Tests for closure_gate — require compound/review/retro for substantial work."""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import closure_gate  # noqa: E402
import compound_record  # noqa: E402
import stop_hook_closure_gate  # noqa: E402

NOW = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))
TODAY = "2026-06-14"


# --- pure decision logic ---

def test_decide_not_substantial_approves():
    d = closure_gate.decide(10, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=10)
    assert d["decision"] == "approve"
    assert d["reason"] == "not-substantial"


def test_decide_substantial_without_record_blocks():
    d = closure_gate.decide(200, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "block"
    assert d["missing"] == ["compound", "review", "retro"]
    assert "200" in d["message"]


@pytest.mark.parametrize("present", ["compound", "review", "retro"])
def test_decide_substantial_with_any_record_approves(present):
    records = {"compound": False, "review": False, "retro": False}
    records[present] = True
    d = closure_gate.decide(200, records, threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-record-present"


def test_decide_disabled_always_approves():
    d = closure_gate.decide(9999, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=True, now_lines=9999)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-gate-disabled"


def _scribe_evaluation(
    *,
    state="overdue",
    projection="missing",
    blocking=True,
    reasons=None,
    cleanup_status="none",
):
    closure_reasons = (
        list(reasons)
        if reasons is not None
        else (["source-debt-overdue", "projection-not-fresh"] if blocking else [])
    )
    return {
        "state": state,
        "readiness": "blocked" if blocking else "ready",
        "source_debt": {
            "status": state,
            "hot_count": 20 if state == "overdue" else 13,
            "overdue_sources": ["STATUS.md"] if state == "overdue" else [],
        },
        "projection": {
            "path": "agents/project/state/SCRIBE-PROJECTION.json",
            "status": projection,
        },
        "active_coverage": {
            "status": "complete",
            "missing_task_ids": [],
            "missing_claim_ids": [],
        },
        "cleanup_plan": {"status": "available", "candidate_count": 4},
        "cleanup_outcome": {"status": cleanup_status, "valid": cleanup_status != "invalid"},
        "overdue_sources": ["STATUS.md"] if state == "overdue" else [],
        "closure_blocking": blocking,
        "closure_reasons": closure_reasons,
    }


def test_substantial_closeout_blocks_for_overdue_missing_projection():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    result = closure_gate.apply_scribe_obligation(
        base,
        _scribe_evaluation(),
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )
    assert result["decision"] == "block"
    assert result["reason"] == "scribe-source-debt-overdue"
    assert result["missing"] == ["scribe_source_debt", "scribe_projection"]
    assert "projection is only a bounded view" in result["message"]


def test_mini_closeout_and_due_state_keep_scribe_advisory():
    for lines, evaluation in (
        (20, _scribe_evaluation()),
        (
            200,
            _scribe_evaluation(state="due", projection="missing", blocking=False),
        ),
    ):
        base = closure_gate.decide(
            lines,
            {"compound": False, "review": True, "retro": False},
            threshold=80,
            disabled=False,
            now_lines=lines,
        )
        result = closure_gate.apply_scribe_obligation(
            base,
            evaluation,
            substantial_lines=lines,
            threshold=80,
            disabled=False,
        )
        assert result["decision"] == "approve"


def test_fresh_projection_does_not_satisfy_overdue_source_debt():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    result = closure_gate.apply_scribe_obligation(
        base,
        _scribe_evaluation(
            projection="fresh",
            blocking=True,
            reasons=["source-debt-overdue"],
        ),
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )
    assert result["decision"] == "block"
    assert result["missing"] == ["scribe_source_debt"]
    assert result["scribe"]["projection"]["status"] == "fresh"


def test_verified_cleanup_or_owner_decision_satisfies_substantial_scribe_obligation():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    for evaluation in (
        _scribe_evaluation(
            state="ok",
            projection="fresh",
            blocking=False,
            cleanup_status="verified_reduction",
        ),
        _scribe_evaluation(
            projection="fresh",
            blocking=False,
            cleanup_status="owner_decision",
        ),
    ):
        result = closure_gate.apply_scribe_obligation(
            dict(base),
            evaluation,
            substantial_lines=200,
            threshold=80,
            disabled=False,
        )
        assert result["decision"] == "approve"


def test_missing_active_coverage_has_its_own_closure_obligation():
    base = closure_gate.decide(
        200,
        {"compound": False, "review": True, "retro": False},
        threshold=80,
        disabled=False,
        now_lines=200,
    )
    evaluation = _scribe_evaluation(
        state="ok",
        projection="fresh",
        blocking=True,
        reasons=["active-coverage-incomplete"],
    )
    evaluation["active_coverage"] = {
        "status": "incomplete",
        "missing_task_ids": ["TASK-ACTIVE"],
        "missing_claim_ids": ["CLAIM-ACTIVE"],
    }

    result = closure_gate.apply_scribe_obligation(
        base,
        evaluation,
        substantial_lines=200,
        threshold=80,
        disabled=False,
    )

    assert result["decision"] == "block"
    assert result["reason"] == "scribe-active-coverage-incomplete"
    assert result["missing"] == ["scribe_active_coverage"]


def test_substantial_closeout_blocks_for_configured_source_integrity(
    tmp_path,
    monkeypatch,
):
    source = tmp_path / "state" / "current.json"
    source.parent.mkdir(parents=True)
    source.write_text('{"items":[],"items":[]}\n', encoding="utf-8")
    (tmp_path / "agent_runtime.yml").write_text(
        "schema: agent-runtime-config/v2\n"
        "project: closure-fixture\n"
        "sync:\n"
        "  mode: check-diff-apply\n"
        "  allow_silent_overwrite: false\n"
        "profiles:\n"
        "  - core\n"
        "ownership:\n"
        "  host_owned:\n"
        "    - state/current.json\n"
        "host:\n"
        "  state_adapters:\n"
        "    state: state/current.json\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        closure_gate,
        "count_substantial_lines",
        lambda *args, **kwargs: 200,
    )
    monkeypatch.setattr(
        closure_gate,
        "has_closure_record",
        lambda *args, **kwargs: {
            "compound": False,
            "review": True,
            "retro": False,
        },
    )

    result = closure_gate.assess(tmp_path, threshold=80, disabled=False)

    assert result["decision"] == "block"
    assert result["reason"] == "scribe-source-integrity"
    assert result["missing"] == ["scribe_source_integrity"]
    assert "state/current.json" in result["message"]
    assert "repair" in result["message"].lower()


# --- closure record detection ---

def test_has_closure_record_detects_today(tmp_path):
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        f"## COMPOUND-{TODAY}-001: something\n", encoding="utf-8")
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / f"RETRO-{TODAY}-x.md").write_text("retro", encoding="utf-8")
    (reviews / f"REVIEW-{TODAY}-y-closeout.md").write_text("review", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": True, "review": True, "retro": True}


def test_has_closure_record_ignores_other_days(tmp_path):
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        "## COMPOUND-2026-06-10-001: old\n", encoding="utf-8")
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "RETRO-2026-06-10-x.md").write_text("old", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": False, "review": False, "retro": False}


def _write_active_unit(
    root: Path,
    *,
    review_refs: list[str] | None = None,
    compound_refs: list[str] | None = None,
    signatures: list[str] | None = None,
) -> None:
    unit_id = "UNIT-TASK-AR-645-001"
    unit_path = (
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-645"
        / f"{unit_id}.md"
    )
    unit_path.parent.mkdir(parents=True, exist_ok=True)

    def block(name: str, values: list[str] | None) -> str:
        if not values:
            return ""
        return name + ":\n" + "".join(f"  - {value}\n" for value in values)

    unit_path.write_text(
        "---\n"
        "schema_version: agent-runtime-work-item/v1\n"
        f"work_id: {unit_id}\n"
        "kind: unit\n"
        "parent_id: TASK-AR-645\n"
        f"unit_id: {unit_id}\n"
        "task_id: TASK-AR-645\n"
        + block("review_refs", review_refs)
        + block("compound_refs", compound_refs)
        + block("defect_signatures", signatures)
        + "---\n\n# Active unit\n",
        encoding="utf-8",
    )
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / "CLAIM-active.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-active",
                "status": "claimed",
                "task_id": "TASK-AR-645",
                "unit_id": unit_id,
                "unit_spec": unit_path.relative_to(root).as_posix(),
                "updated_at": "2026-06-14T11:00:00+09:00",
            }
        ),
        encoding="utf-8",
    )


def test_active_work_rejects_unrelated_same_day_records(tmp_path):
    unrelated_review = f"reviews/REVIEW-{TODAY}-unrelated-closeout.md"
    path = tmp_path / unrelated_review
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\nwork_id: TASK-AR-999\n---\n\n# Unrelated review\n",
        encoding="utf-8",
    )
    (path.parent / f"RETRO-{TODAY}-unrelated.md").write_text(
        "---\nwork_id: TASK-AR-999\n---\n", encoding="utf-8"
    )
    legacy = tmp_path / "agents" / "lead_engineer" / "compound_log.md"
    legacy.parent.mkdir(parents=True)
    legacy.write_text(
        f"## COMPOUND-{TODAY}-999: unrelated\n", encoding="utf-8"
    )
    _write_active_unit(tmp_path, review_refs=[unrelated_review])

    rec = closure_gate.has_closure_record(tmp_path, now=NOW)

    assert rec == {"compound": False, "review": False, "retro": False}


def test_active_work_accepts_explicit_linked_review_and_compound(tmp_path):
    review_ref = f"reviews/REVIEW-{TODAY}-task-ar-645-closeout.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\n"
        "work_id: UNIT-TASK-AR-645-001\n"
        "task_id: TASK-AR-645\n"
        "---\n\n# Linked review\n",
        encoding="utf-8",
    )
    record_path, _record = compound_record.create_record(
        tmp_path,
        work_ids=["UNIT-TASK-AR-645-001"],
        defect_signatures=["same-day unrelated closure"],
        title="Bind closure to work",
        summary="A same-day file was unrelated to the active unit.",
        cause="Closure searched only by date.",
        prevention="Require explicit references linked to the work.",
        source_refs=[review_ref],
        prevention_refs=["scripts/closure_gate.py"],
        verification_refs=["reviews/VERIFY-unit.json"],
        created_at="2026-06-14T11:30:00+09:00",
    )
    compound_ref = compound_record.record_ref(tmp_path, record_path)
    _write_active_unit(
        tmp_path,
        review_refs=[review_ref],
        compound_refs=[compound_ref],
        signatures=["same-day unrelated closure"],
    )

    rec = closure_gate.has_closure_record(tmp_path, now=NOW)

    assert rec == {"compound": True, "review": True, "retro": False}


def test_multiple_active_claims_fail_closed_without_explicit_work_id(tmp_path):
    review_ref = f"reviews/REVIEW-{TODAY}-task-ar-645-closeout.md"
    review = tmp_path / review_ref
    review.parent.mkdir(parents=True)
    review.write_text(
        "---\nwork_id: UNIT-TASK-AR-645-001\n---\n\n# Linked review\n",
        encoding="utf-8",
    )
    _write_active_unit(tmp_path, review_refs=[review_ref])
    claims = tmp_path / "agents" / "runtime" / "task_claims"
    (claims / "CLAIM-other.json").write_text(
        json.dumps(
            {
                "schema": "agent-runtime-task-claim/v1",
                "claim_id": "CLAIM-other",
                "status": "claimed",
                "task_id": "TASK-AR-999",
                "unit_id": "UNIT-TASK-AR-999-001",
                "updated_at": "2026-06-14T11:30:00+09:00",
            }
        ),
        encoding="utf-8",
    )

    inferred = closure_gate.has_closure_record(tmp_path, now=NOW)
    explicit = closure_gate.has_closure_record(
        tmp_path, now=NOW, work_id="UNIT-TASK-AR-645-001"
    )

    assert inferred == {"compound": False, "review": False, "retro": False}
    assert explicit == {"compound": False, "review": True, "retro": False}


# --- substantial line counting via git ---

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.fixture
def git_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "seed.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "seed")
    return tmp_path


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_code_churn(git_repo):
    # a sizeable code commit
    (git_repo / "src" / "feature.py").write_text("\n".join(f"line{i} = {i}" for i in range(120)) + "\n", encoding="utf-8")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "feat: big")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 120


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_uncommitted(git_repo):
    (git_repo / "scripts").mkdir()
    (git_repo / "scripts" / "wip.py").write_text("\n".join(f"a{i}=1" for i in range(90)) + "\n", encoding="utf-8")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 90


# --- stop hook wrapper ---

def test_stop_hook_blocks_substantial_without_record(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(closure_gate, "count_substantial_lines", lambda *a, **k: 300)
    monkeypatch.setattr(closure_gate, "has_closure_record",
                        lambda *a, **k: {"compound": False, "review": False, "retro": False})
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["decision"] == "block"
    assert out["systemMessage"]


def test_stop_hook_best_effort_on_error(monkeypatch, capsys):
    monkeypatch.setattr(closure_gate, "assess", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    assert capsys.readouterr().out == ""  # never block on gate error


def test_stop_hook_disabled_env_approves(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", "1")
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    assert capsys.readouterr().out == ""
