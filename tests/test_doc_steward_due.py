"""Tests for doc_steward_due -- advisory drift signal for Doc Steward check.

Verifies: advisory output on a tmp project, always exit 0, generic behavior
(D1 org-chart drift + D2 missing review), cycle_status guard.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "doc_steward_due.py"


def _load(root_override: Path):
    """Load doc_steward_due with ROOT patched to root_override."""
    spec = importlib.util.spec_from_file_location("doc_steward_due", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Patch module-level path constants to point at the tmp project.
    mod.ROOT = root_override
    mod.AGENTS = root_override / "agents"
    mod.CLAUDE_MD = root_override / "CLAUDE.md"
    mod.LEAD = root_override / "agents" / "lead_engineer"
    mod.REVIEWS = root_override / "agents" / "lead_engineer" / "reviews"
    return mod


def _mk_project(tmp_path: Path) -> Path:
    """Minimal project layout: one role referenced in CLAUDE.md, reviews dir."""
    agents = tmp_path / "agents"
    lead = agents / "lead_engineer"
    reviews = lead / "reviews"
    reviews.mkdir(parents=True)
    (agents / "scribe").mkdir(parents=True)
    (agents / "scribe" / "SKILL.md").write_text("# Scribe\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "# Guide\nagents/scribe/ handles compression.\n", encoding="utf-8"
    )
    return tmp_path


# ---------------------------------------------------------------------------
# exit-0 / advisory contract
# ---------------------------------------------------------------------------

def test_exit_zero_on_empty_project(tmp_path):
    """Script must always exit 0 (advisory)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0


def test_exit_zero_quiet_flag(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--quiet"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0


def test_output_contains_state_prefix(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0
    assert "[doc_steward_due]" in result.stdout


# ---------------------------------------------------------------------------
# classify / threshold
# ---------------------------------------------------------------------------

def test_classify_ok():
    mod = _load(Path("/nonexistent"))
    assert mod.classify(0) == "ok"


def test_classify_due():
    mod = _load(Path("/nonexistent"))
    assert mod.classify(1) == "due"
    assert mod.classify(2) == "due"


def test_classify_overdue():
    mod = _load(Path("/nonexistent"))
    assert mod.classify(3) == "overdue"
    assert mod.classify(99) == "overdue"


# ---------------------------------------------------------------------------
# D1 org-chart drift
# ---------------------------------------------------------------------------

def test_no_orphans_when_all_referenced(tmp_path):
    proj = _mk_project(tmp_path)
    mod = _load(proj)
    assert mod.orphan_role_docs() == []


def test_orphan_detected_when_skill_missing_from_claude_md(tmp_path):
    proj = _mk_project(tmp_path)
    # Add a second role that is NOT referenced in CLAUDE.md
    ghost = proj / "agents" / "ghost_role"
    ghost.mkdir(parents=True)
    (ghost / "SKILL.md").write_text("# Ghost\n", encoding="utf-8")
    mod = _load(proj)
    orphans = mod.orphan_role_docs()
    assert "ghost_role" in orphans


def test_lead_engineer_never_orphaned(tmp_path):
    proj = _mk_project(tmp_path)
    # Even with no CLAUDE.md mention of lead_engineer, it should not be flagged.
    lead_skill = proj / "agents" / "lead_engineer" / "SKILL.md"
    lead_skill.parent.mkdir(parents=True, exist_ok=True)
    lead_skill.write_text("# Lead\n", encoding="utf-8")
    mod = _load(proj)
    assert "lead_engineer" not in mod.orphan_role_docs()


def test_no_agents_dir_returns_empty_orphans(tmp_path):
    mod = _load(tmp_path)
    assert mod.orphan_role_docs() == []


# ---------------------------------------------------------------------------
# D2 missing review with cycle_status guard
# ---------------------------------------------------------------------------

def test_no_cycle_no_missing(tmp_path):
    proj = _mk_project(tmp_path)
    mod = _load(proj)
    assert mod.missing_review() == -1


def test_review_present_no_missing(tmp_path):
    proj = _mk_project(tmp_path)
    reviews = proj / "agents" / "lead_engineer" / "reviews"
    (reviews / "REVIEW-001.md").write_text("# Review 1\n", encoding="utf-8")
    mod = _load(proj)
    assert mod.missing_review() == -1


def test_in_progress_cycle_not_flagged(tmp_path):
    """A CYCLE without '완료' status should not trigger D2."""
    proj = _mk_project(tmp_path)
    lead = proj / "agents" / "lead_engineer"
    (lead / "CYCLE-001.md").write_text(
        "# Cycle 1\n상태: 진행중\n", encoding="utf-8"
    )
    mod = _load(proj)
    assert mod.missing_review() == -1


def test_completed_cycle_without_review_flagged(tmp_path):
    """A completed CYCLE-NNN.md without matching REVIEW-NNN.md triggers D2."""
    proj = _mk_project(tmp_path)
    lead = proj / "agents" / "lead_engineer"
    (lead / "CYCLE-001.md").write_text(
        "# Cycle 1\n상태: 완료\n", encoding="utf-8"
    )
    mod = _load(proj)
    assert mod.missing_review() == 1


def test_completed_cycle_with_review_not_flagged(tmp_path):
    proj = _mk_project(tmp_path)
    lead = proj / "agents" / "lead_engineer"
    reviews = lead / "reviews"
    (lead / "CYCLE-001.md").write_text(
        "# Cycle 1\n상태: 완료\n", encoding="utf-8"
    )
    (reviews / "REVIEW-001.md").write_text("# Review\n", encoding="utf-8")
    mod = _load(proj)
    assert mod.missing_review() == -1


def test_review_only_project_no_missing(tmp_path):
    """REVIEW-NNN canonical marker: no CYCLE file, REVIEW present -> no drift."""
    proj = _mk_project(tmp_path)
    reviews = proj / "agents" / "lead_engineer" / "reviews"
    (reviews / "REVIEW-005.md").write_text("# Review 5\n", encoding="utf-8")
    mod = _load(proj)
    assert mod.missing_review() == -1


# ---------------------------------------------------------------------------
# integration: state and quiet
# ---------------------------------------------------------------------------

def test_ok_state_on_clean_project(tmp_path):
    proj = _mk_project(tmp_path)
    mod = _load(proj)
    orphans = mod.orphan_role_docs()
    miss = mod.missing_review()
    drift = len(orphans) + (1 if miss >= 0 else 0)
    assert mod.classify(drift) == "ok"


def test_due_state_with_one_orphan(tmp_path):
    proj = _mk_project(tmp_path)
    ghost = proj / "agents" / "ghost_role"
    ghost.mkdir(parents=True)
    (ghost / "SKILL.md").write_text("# Ghost\n", encoding="utf-8")
    mod = _load(proj)
    orphans = mod.orphan_role_docs()
    miss = mod.missing_review()
    drift = len(orphans) + (1 if miss >= 0 else 0)
    assert mod.classify(drift) == "due"
