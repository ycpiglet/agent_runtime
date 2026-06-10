import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_identity.py"
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def _write_task(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _task_text(task_id: str, *, status: str = "planned", uid: str = "") -> str:
    uid_line = f"task_uid: {uid}\n" if uid else ""
    return f"""---
id: {task_id}
{uid_line}status: {status}
priority: P0
difficulty: M
est_hours: 1
est_tokens: 100
task_set_id: TASKSET-AR-QUALITY-LOOP
tags: []
---

## Goal
- Test task identity.
"""


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


def _frontmatter(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == "---" and meta:
            break
        if ":" not in line or line.strip() == "---":
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip("\"'")
    return meta


def test_task_identity_gate_blocks_duplicate_ids_and_missing_uids(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    _write_task(tasks / "TASK-AR-901-a.md", _task_text("TASK-AR-901"))
    _write_task(tasks / "TASK-AR-901-b.md", _task_text("TASK-AR-901"))

    result = _run(tmp_path, "check", "--check")

    assert result.returncode == 1
    assert "task-identity:duplicate-id:TASK-AR-901" in result.stdout
    assert "task-identity:missing-task-uid:TASK-AR-901" in result.stdout


def test_task_identity_backfill_adds_uuid_and_lifecycle_metadata(tmp_path: Path) -> None:
    tasks = tmp_path / "agents" / "lead_engineer" / "tasks"
    active = tasks / "TASK-AR-901.md"
    done = tasks / "TASK-AR-902.md"
    _write_task(active, _task_text("TASK-AR-901", status="in_progress"))
    _write_task(done, _task_text("TASK-AR-902", status="completed"))

    result = _run(tmp_path, "backfill", "--now", "2026-06-10T12:00:00+09:00")

    assert result.returncode == 0
    active_meta = _frontmatter(active)
    done_meta = _frontmatter(done)
    assert UUID_RE.match(active_meta["task_uid"])
    assert UUID_RE.match(done_meta["task_uid"])
    assert active_meta["task_uid"] != done_meta["task_uid"]
    assert active_meta["registered_at"] == "2026-06-10T12:00:00+09:00"
    assert active_meta["started_at"] == "2026-06-10T12:00:00+09:00"
    assert active_meta["updated_at"] == "2026-06-10T12:00:00+09:00"
    assert "completed_at" not in active_meta
    assert done_meta["completed_at"] == "2026-06-10T12:00:00+09:00"


def test_task_identity_create_uses_uuid_backed_task_id_and_metadata(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        "create",
        "--task-set-id",
        "TASKSET-AR-QUALITY-LOOP",
        "--title",
        "Collision proof task",
        "--goal",
        "Create task through allocator.",
        "--now",
        "2026-06-10T12:00:00+09:00",
    )

    assert result.returncode == 0
    path_line = next(line for line in result.stdout.splitlines() if line.startswith("path="))
    task_path = tmp_path / path_line.split("=", 1)[1]
    meta = _frontmatter(task_path)
    assert meta["id"].startswith("TASK-AR-20260610-120000-")
    assert UUID_RE.match(meta["task_uid"])
    assert meta["registered_at"] == "2026-06-10T12:00:00+09:00"
    assert meta["updated_at"] == "2026-06-10T12:00:00+09:00"
