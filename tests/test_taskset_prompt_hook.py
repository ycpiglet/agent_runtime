from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "taskset_prompt_hook.py"


def test_taskset_prompt_hook_injects_dispatcher_instruction_for_korean_prompt() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "taskset-quality-loop 진행해줘"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "taskset" in context.lower()
    assert "scripts/taskset_dispatcher.py" in context.replace("\\", "/")
    assert "quality-loop" in context
    assert "worktree" in context.lower()


def test_taskset_prompt_hook_injects_finish_instruction_for_korean_closeout() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "마무리해줘"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "finish trigger" in context
    assert "commit + PR + merge" in context
    assert "clean working tree" in context
    assert "Ask for approval only for critical boundaries" in context


def test_taskset_prompt_hook_combines_taskset_and_finish_guidance() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "taskset-release-steward 진행하고 정리해줘"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "taskset trigger" in context
    assert "release-steward" in context
    assert "finish trigger" in context
    assert "commit + PR + merge" in context


def test_taskset_prompt_hook_routes_hierarchy_numbering_to_work_taxonomist() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "initiative-taskset-task-unit 번호 분류 작업 진행해줘"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    context = payload["hookSpecificOutput"]["additionalContext"]
    assert "work-hierarchy-conflict-closure" in context
    assert "Detected taskset alias: task-unit" not in context
    assert "planning discussion trigger" in context
    assert "work_item_classifier.py --write" in context
