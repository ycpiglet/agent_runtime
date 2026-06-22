"""TDD for cmd_create auto-inheriting a unit's ``escalation_triggers``.

Today the claim only carries escalation_triggers from the explicit
``--escalation-trigger`` arg (PR #207). This pins the missing automatic link:
``cmd_create`` reads the unit definition it is already handed via
``--unit-spec`` and inherits that unit's frontmatter ``escalation_triggers``
onto the claim, UNIONed with any explicit args (explicit-first, deduped).

Downstream the ``cmd_release`` -> ``route_review_pass`` seam reads
``claim["escalation_triggers"]`` and auto-attaches the adversarial skeptic
pass for high-risk units, so this link is what makes high-risk work carry its
risk signal without anyone passing ``--escalation-trigger`` by hand.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import task_claim_dispatcher as tcd  # noqa: E402

CLAIM_DISPATCHER = ROOT / "scripts" / "task_claim_dispatcher.py"


def _write_unit(tmp_path: Path, frontmatter: str, *, name: str = "UNIT.md") -> Path:
    """Write a minimal unit definition whose frontmatter is ``frontmatter``."""
    path = tmp_path / "units" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n# unit\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _unit_spec_escalation_triggers — mirrors _unit_spec_target_files
# ---------------------------------------------------------------------------


def test_helper_reads_list_form(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: [high_risk, security]")
    assert tcd._unit_spec_escalation_triggers(tmp_path, str(unit)) == ["high_risk", "security"]


def test_helper_reads_comma_string_form(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: high_risk, security")
    assert tcd._unit_spec_escalation_triggers(tmp_path, str(unit)) == ["high_risk", "security"]


def test_helper_strips_and_drops_empty(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: ['  high_risk  ', '', security]")
    assert tcd._unit_spec_escalation_triggers(tmp_path, str(unit)) == ["high_risk", "security"]


def test_helper_missing_field_returns_empty(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "target_files: [scripts/a.py]")
    assert tcd._unit_spec_escalation_triggers(tmp_path, str(unit)) == []


def test_helper_missing_file_returns_empty(tmp_path: Path) -> None:
    assert tcd._unit_spec_escalation_triggers(tmp_path, str(tmp_path / "nope.md")) == []


def test_helper_empty_spec_returns_empty(tmp_path: Path) -> None:
    assert tcd._unit_spec_escalation_triggers(tmp_path, "") == []
    assert tcd._unit_spec_escalation_triggers(tmp_path, None) == []  # type: ignore[arg-type]


def test_helper_resolves_relative_to_root(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: [high_risk]")
    rel = unit.relative_to(tmp_path).as_posix()
    assert tcd._unit_spec_escalation_triggers(tmp_path, rel) == ["high_risk"]


# ---------------------------------------------------------------------------
# cmd_create integration (real CLI subprocess) — the auto-inherit link
# ---------------------------------------------------------------------------


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def _write_worktree(root: Path, task_id: str) -> None:
    worktree = root / ".worktrees" / task_id
    worktree.mkdir(parents=True, exist_ok=True)
    (worktree / ".git").write_text("gitdir: ../../.git/worktrees/test\n", encoding="utf-8")


def _run_create(root: Path, unit: Path | None, *extra: str) -> dict:
    _write_worktree(root, "TASK-AR-ESC")
    args = [
        sys.executable, str(CLAIM_DISPATCHER), "--root", str(root), "create",
        "--task-id", "TASK-AR-ESC",
        "--task-set-id", "TASKSET-AR-ESC",
        "--agent-role", "lead-engineer",
        "--mode", "implement",
        "--now", "2026-06-22T09:00:00+09:00",
        "--suffix", "esc",
        "--json",
    ]
    if unit is not None:
        args += ["--unit-spec", str(unit)]
    args += list(extra)
    proc = subprocess.run(
        args, cwd=ROOT, check=False, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=_env(),
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout)["claim"]


def test_create_auto_inherits_unit_escalation_triggers(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: [high_risk]")
    claim = _run_create(tmp_path, unit)  # NO --escalation-trigger
    assert "high_risk" in claim["escalation_triggers"]


def test_create_union_explicit_and_inherited_dedupes(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: [high_risk]")
    claim = _run_create(tmp_path, unit, "--escalation-trigger", "cross_cutting")
    assert set(claim["escalation_triggers"]) == {"cross_cutting", "high_risk"}
    # No dupes, explicit-first order preserved.
    assert claim["escalation_triggers"] == ["cross_cutting", "high_risk"]


def test_create_identical_explicit_and_inherited_dedupe(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "escalation_triggers: [high_risk]")
    claim = _run_create(tmp_path, unit, "--escalation-trigger", "high_risk")
    assert claim["escalation_triggers"] == ["high_risk"]


def test_create_back_compat_no_unit_no_trigger(tmp_path: Path) -> None:
    claim = _run_create(tmp_path, None)  # no --unit-spec, no --escalation-trigger
    assert claim["escalation_triggers"] == []


def test_create_unit_without_triggers_stays_empty(tmp_path: Path) -> None:
    unit = _write_unit(tmp_path, "target_files: [scripts/a.py]")
    claim = _run_create(tmp_path, unit)
    assert claim["escalation_triggers"] == []
