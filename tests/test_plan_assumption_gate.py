from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import plan_assumption_gate


def _record(root: Path) -> None:
    rc = plan_assumption_gate.main(
        [
            "--root",
            str(root),
            "record",
            "--taskset",
            "TASKSET-T-DEMO",
            "--design-record",
            "reviews/REVIEW-demo.md",
            "--anchor",
            "scripts/dispatcher.py",
            "--anchor",
            "agents/project/NEW-SCHEMA.yml",
        ]
    )
    assert rc == 0


def test_record_then_check_passes(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "scripts" / "dispatcher.py").write_text("v1", encoding="utf-8")
    _record(tmp_path)

    assert plan_assumption_gate.main(["--root", str(tmp_path), "--check"]) == 0


def test_hash_drift_blocks(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "scripts" / "dispatcher.py").write_text("v1", encoding="utf-8")
    _record(tmp_path)

    (tmp_path / "scripts" / "dispatcher.py").write_text("v2-merged", encoding="utf-8")
    assert (
        plan_assumption_gate.main(
            ["--root", str(tmp_path), "--check", "--taskset", "TASKSET-T-DEMO"]
        )
        == 1
    )


def test_absent_anchor_appearing_blocks(tmp_path: Path) -> None:
    (tmp_path / "scripts").mkdir(parents=True)
    (tmp_path / "scripts" / "dispatcher.py").write_text("v1", encoding="utf-8")
    _record(tmp_path)

    schema = tmp_path / "agents" / "project" / "NEW-SCHEMA.yml"
    schema.parent.mkdir(parents=True, exist_ok=True)
    schema.write_text("schema: v1", encoding="utf-8")
    assert plan_assumption_gate.main(["--root", str(tmp_path), "--check"]) == 1


def test_unknown_taskset_fails(tmp_path: Path) -> None:
    assert (
        plan_assumption_gate.main(
            ["--root", str(tmp_path), "--check", "--taskset", "TASKSET-T-NOPE"]
        )
        == 1
    )
