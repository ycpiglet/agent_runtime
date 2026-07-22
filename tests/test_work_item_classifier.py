from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "work_item_classifier.py"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _payload(root: Path) -> dict[str, object]:
    return json.loads(
        (root / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json").read_text(
            encoding="utf-8"
        )
    )


def _seed(root: Path) -> None:
    _write(
        root / "agents" / "project" / "initiatives" / "INIT-TEST.md",
        """---
type: initiative
id: INIT-TEST
status: planned
created_at: 2026-06-12T00:00:00+09:00
---

# Test Initiative
""",
    )
    for index in (1, 2):
        _write(
            root / "agents" / "lead_engineer" / "tasks" / f"TASK-AR-90{index}.md",
            f"""---
id: TASK-AR-90{index}
display_id: TASK-AR-90{index}
task_uid: 11111111-1111-4111-8111-00000000000{index}
registered_at: 2026-06-12T00:00:0{index}+09:00
created_at: 2026-06-12T00:00:0{index}+09:00
updated_at: 2026-06-12T00:00:0{index}+09:00
status: planned
priority: P1
difficulty: M
est_hours: 1
est_tokens: 100
initiative_id: INIT-TEST
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
tags: []
---

## Goal
- Task {index}.
""",
        )
    _write(
        root
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "TASK-AR-901"
        / "UNIT-TASK-AR-901-001.md",
        """---
unit_id: UNIT-TASK-AR-901-001
task_id: TASK-AR-901
task_set_id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
initiative_id: INIT-TEST
status: worker_ready
---

# Unit One
""",
    )


def test_work_item_classifier_writes_hierarchy_numbers(tmp_path: Path) -> None:
    _seed(tmp_path)

    result = _run(tmp_path, "--write", "--check")

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(
        (tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json").read_text(
            encoding="utf-8"
        )
    )
    numbers = {row["id"]: row["number"] for row in payload["records"]}
    assert numbers["INIT-TEST"] == "1"
    assert numbers["TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE"] == "1.1"
    assert numbers["TASK-AR-901"] == "1.1.1"
    assert numbers["TASK-AR-902"] == "1.1.2"
    assert numbers["UNIT-TASK-AR-901-001"] == "1.1.1.1"


def test_work_item_classifier_filters_mixed_initiative_directory_by_kind(tmp_path: Path) -> None:
    _seed(tmp_path)
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "TASKSET-DUPLICATE.md",
        """---
kind: taskset
type: initiative
id: TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE
work_id: TASKSET-IGNORED
status: active
---

# Must Not Be An Initiative
""",
    )
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "WORK-ID-FILENAME.md",
        """---
kind: initiative
work_id: INIT-WORK-ID
status: planned
created_at: 2026-06-11T00:00:00+09:00
---

# Work ID Initiative
""",
    )
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "ID-WINS.md",
        """---
kind: initiative
id: INIT-ID-WINS
work_id: INIT-WORK-ID-IGNORED
status: planned
created_at: 2026-06-10T00:00:00+09:00
---

# Canonical ID Initiative
""",
    )
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "INIT-LEGACY.md",
        """---
status: active
created_at: 2026-06-09T00:00:00+09:00
---

# Legacy Initiative
""",
    )
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "INIT-TYPE-TASKSET.md",
        """---
kind: "   "
type: taskset
id: INIT-TYPE-TASKSET
status: planned
---

# Type Alias Taskset
""",
    )
    _write(
        tmp_path / "agents" / "project" / "initiatives" / "SPACE-ID.md",
        """---
kind: initiative
id: "   "
work_id: INIT-WORK-SPACE-ID
status: planned
---

# Normalized Work ID Initiative
""",
    )

    result = _run(tmp_path, "--write", "--check")

    assert result.returncode == 0, result.stderr or result.stdout
    records = _payload(tmp_path)["records"]
    initiative_ids = [row["id"] for row in records if row["level"] == "initiative"]
    all_ids = [row["id"] for row in records]
    assert "TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE" not in initiative_ids
    assert all_ids.count("TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE") == 1
    assert "INIT-WORK-ID" in initiative_ids
    assert "WORK-ID-FILENAME" not in initiative_ids
    assert "INIT-ID-WINS" in initiative_ids
    assert "INIT-WORK-ID-IGNORED" not in initiative_ids
    assert "INIT-LEGACY" in initiative_ids
    assert "INIT-TYPE-TASKSET" not in initiative_ids
    assert "INIT-WORK-SPACE-ID" in initiative_ids
    assert "SPACE-ID" not in initiative_ids


def test_work_item_classifier_check_fails_when_generated_json_is_stale(tmp_path: Path) -> None:
    _seed(tmp_path)
    stale = tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.json"
    _write(stale, '{"schema": "agent-runtime-work-item-classification/v1", "records": []}\n')
    _write(tmp_path / "agents" / "project" / "work-items" / "WORK-ITEM-CLASSIFICATION.md", "## Bottom Line\n## Action Board\n")

    result = _run(tmp_path, "--check")

    assert result.returncode == 1
    assert "WORK-ITEM-CLASSIFICATION.json: stale" in result.stdout


def test_work_item_classifier_allows_empty_bootstrap_without_generated_files(tmp_path: Path) -> None:
    result = _run(tmp_path, "--check")

    assert result.returncode == 0
    assert "work-item-classifier: pass" in result.stdout
