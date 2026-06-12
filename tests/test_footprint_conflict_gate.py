import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import footprint_conflict_gate


def _write_claim(root: Path, claim_id: str, task_id: str, status: str, target_files):
    claims = root / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "agent-runtime-task-claim/v1",
        "claim_id": claim_id,
        "task_id": task_id,
        "status": status,
        "target_files": target_files,
    }
    (claims / f"{claim_id}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def test_disjoint_active_claims_pass(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", ["scripts/a.py"])
    _write_claim(tmp_path, "CLAIM-B", "TASK-2", "working", ["scripts/b.py"])
    assert footprint_conflict_gate.main(["--root", str(tmp_path), "--check"]) == 0


def test_exact_overlap_fails(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", ["scripts/a.py"])
    _write_claim(tmp_path, "CLAIM-B", "TASK-2", "claimed", ["scripts/a.py"])
    assert footprint_conflict_gate.main(["--root", str(tmp_path), "--check"]) == 1


def test_glob_prefix_overlap_fails(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", ["scripts/**"])
    _write_claim(tmp_path, "CLAIM-B", "TASK-2", "in_progress", ["scripts/sub/b.py"])
    assert footprint_conflict_gate.main(["--root", str(tmp_path), "--check"]) == 1


def test_released_claims_ignored(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "released", ["scripts/a.py"])
    _write_claim(tmp_path, "CLAIM-B", "TASK-2", "claimed", ["scripts/a.py"])
    assert footprint_conflict_gate.main(["--root", str(tmp_path), "--check"]) == 0


def test_undeclared_footprint_is_watch_not_fail(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", [])
    _write_claim(tmp_path, "CLAIM-B", "TASK-2", "claimed", ["scripts/a.py"])
    assert footprint_conflict_gate.main(["--root", str(tmp_path), "--check"]) == 0


def test_probe_conflict_blocks(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", ["scripts/shared.py"])
    rc = footprint_conflict_gate.main(
        [
            "--root", str(tmp_path), "--probe",
            "--task-id", "TASK-2",
            "--file", "scripts/shared.py",
            "--file", "docs/new.md",
        ]
    )
    assert rc == 1


def test_probe_disjoint_passes_and_ignores_own_task(tmp_path: Path) -> None:
    _write_claim(tmp_path, "CLAIM-A", "TASK-1", "claimed", ["scripts/shared.py"])
    _write_claim(tmp_path, "CLAIM-SELF", "TASK-2", "claimed", ["docs/new.md"])
    rc = footprint_conflict_gate.main(
        [
            "--root", str(tmp_path), "--probe",
            "--task-id", "TASK-2",
            "--file", "docs/new.md",
        ]
    )
    assert rc == 0


def test_entry_overlap_semantics() -> None:
    overlap = footprint_conflict_gate.entries_overlap
    assert overlap("scripts/a.py", "scripts/a.py")
    assert overlap("scripts/**", "scripts/a.py")
    assert overlap("scripts/sub/**", "scripts/**")
    assert overlap("tests/*.py", "tests/test_x.py")
    assert not overlap("scripts/a.py", "scripts/b.py")
    assert not overlap("scripts/**", "docs/a.md")
    assert not overlap("", "scripts/a.py")


def test_dotfile_paths_not_corrupted() -> None:
    # regression: lstrip("./") was a character-set strip and corrupted
    # dotfile paths (reviewer finding, 2026-06-12)
    overlap = footprint_conflict_gate.entries_overlap
    normalize = footprint_conflict_gate._normalize
    assert normalize(".github/workflows/ci.yml") == ".github/workflows/ci.yml"
    assert normalize("./scripts/a.py") == "scripts/a.py"
    assert not overlap(".gitignore", "gitignore")
    assert overlap(".github/**", ".github/workflows/ci.yml")
    assert overlap("./scripts/a.py", "scripts/a.py")
