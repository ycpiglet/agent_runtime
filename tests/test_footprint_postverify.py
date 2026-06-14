import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import footprint_conflict_gate as fg  # noqa: E402


def _claim(tmp: Path, task_id: str, target_files: list[str]) -> None:
    claims = tmp / "agents" / "runtime" / "task_claims"
    claims.mkdir(parents=True, exist_ok=True)
    (claims / f"CLAIM-{task_id}.json").write_text(
        json.dumps(
            {
                "claim_id": f"CLAIM-{task_id}",
                "task_id": task_id,
                "status": "working",
                "target_files": target_files,
            }
        ),
        encoding="utf-8",
    )


def test_actual_subset_of_declared_is_clean(tmp_path: Path) -> None:
    _claim(tmp_path, "TASK-AR-901", ["scripts/foo.py", "tests/**"])
    rc = fg.cmd_postverify(
        tmp_path, "TASK-AR-901", base="x",
        actual_files=["scripts/foo.py", "tests/test_foo.py"], enforce=True,
    )
    assert rc == 0  # every actual file is covered by a declared entry


def test_undeclared_is_watch_by_default(tmp_path: Path) -> None:
    _claim(tmp_path, "TASK-AR-901", ["scripts/foo.py"])
    rc = fg.cmd_postverify(
        tmp_path, "TASK-AR-901", base="x",
        actual_files=["scripts/foo.py", "scripts/bar.py"], enforce=False,
    )
    assert rc == 0  # bar.py is undeclared but watch != block


def test_undeclared_blocks_when_enforced(tmp_path: Path) -> None:
    _claim(tmp_path, "TASK-AR-901", ["scripts/foo.py"])
    rc = fg.cmd_postverify(
        tmp_path, "TASK-AR-901", base="x", actual_files=["scripts/bar.py"], enforce=True,
    )
    assert rc == 1  # actual not subset of declared + enforce -> block


def test_claim_declaring_nothing_flags_all_actual(tmp_path: Path) -> None:
    _claim(tmp_path, "TASK-AR-901", [])
    rc = fg.cmd_postverify(
        tmp_path, "TASK-AR-901", base="x", actual_files=["a.py"], enforce=True,
    )
    assert rc == 1


def test_covered_prefix_and_exact_logic() -> None:
    assert fg._covered("tests/test_x.py", ["tests/**"])
    assert fg._covered("scripts/foo.py", ["scripts/foo.py"])
    assert not fg._covered("scripts/x.py", ["tests/**"])
