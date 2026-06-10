# Session Closeout Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a durable closeout automation layer that prevents repeated dirty-work, stash, branch, worktree, archive-ref, issue, and Owner-gate drift at session boundaries.

**Architecture:** Add a small baseline snapshot command, a dirty-intake classifier, a closeout skill, and narrow hook wiring. The default path is read-only classification; archive/push/issue actions run only through explicit policy and leave recovery pointers.

**Tech Stack:** Python standard library, Git CLI, existing `scripts/owner_governance_gate.py`, `.codex/hooks.json`, GitHub connector/CLI fallback, markdown task files.

---

## File Structure

- Create: `scripts/session_baseline.py`
  - Captures `HEAD`, branch, dirty fingerprint, stash count, worktree list, active `codex/*` branches, and timestamp into `agents/runtime/session_baselines/`.
- Create: `scripts/dirty_intake.py`
  - Compares the current checkout against a baseline and classifies changes as in-scope, late-dirty, log-only, archive-required, approval-required, or blocker.
- Create: `skills/session-closeout/SKILL.md`
  - Defines the Owner meaning of "마무리/정리": commit, PR, merge, branch cleanup, worktree cleanup, stash cleanup, archive/issue handoff, and clean final state.
- Modify: `.codex/hooks.json`
  - Adds SessionStart baseline capture and Stop dirty-intake checks after the scripts have tests.
- Modify: `scripts/owner_governance_gate.py`
  - Adds optional closeout automation gate only after the read-only classifier is stable.
- Create: `tests/test_session_baseline.py`
  - Covers snapshot JSON fields and stable dirty fingerprinting.
- Create: `tests/test_dirty_intake.py`
  - Covers status classification, stash detection, branch residue, worktree residue, and side-effect policy.
- Create: `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md`
  - Owner-facing closeout report after the task set is implemented and verified.

## Task Set

Canonical task set: `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION`

Registered tasks:

- `TASK-AR-292` - Define session closeout contract and baseline schema
- `TASK-AR-293` - Implement session baseline snapshot command
- `TASK-AR-294` - Implement dirty intake classifier and safe archive plan
- `TASK-AR-295` - Wire SessionStart, Stop, and Owner-doc preflight hooks
- `TASK-AR-296` - Package session-closeout skill and verification closeout gate

### Task 1: Define session closeout contract and baseline schema

**Files:**
- Create: `agents/project/SESSION-CLOSEOUT-CONTRACT.md`
- Create: `schemas/session-baseline.schema.json`
- Modify: `agents/project/STATE-MACHINES.yml`
- Test: `tests/test_session_baseline.py`

- [ ] **Step 1: Write schema validation test**

```python
import json
from pathlib import Path


def test_session_baseline_schema_has_required_fields():
    schema = json.loads(Path("schemas/session-baseline.schema.json").read_text(encoding="utf-8"))
    required = set(schema["required"])
    assert {
        "schema",
        "captured_at",
        "cwd",
        "head",
        "branch",
        "status_fingerprint",
        "stash_count",
        "worktrees",
        "active_codex_branches",
    } <= required
```

- [ ] **Step 2: Run test to verify it fails before the schema exists**

Run: `pytest tests/test_session_baseline.py::test_session_baseline_schema_has_required_fields -q`

Expected: `FAILED` with `FileNotFoundError` for `schemas/session-baseline.schema.json`.

- [ ] **Step 3: Add baseline schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Agent Runtime Session Baseline",
  "type": "object",
  "required": [
    "schema",
    "captured_at",
    "cwd",
    "head",
    "branch",
    "status_fingerprint",
    "stash_count",
    "worktrees",
    "active_codex_branches"
  ],
  "properties": {
    "schema": {"const": "agent-runtime-session-baseline/v1"},
    "captured_at": {"type": "string"},
    "cwd": {"type": "string"},
    "head": {"type": "string"},
    "branch": {"type": "string"},
    "status_fingerprint": {"type": "string"},
    "stash_count": {"type": "integer", "minimum": 0},
    "worktrees": {"type": "array", "items": {"type": "object"}},
    "active_codex_branches": {"type": "array", "items": {"type": "string"}}
  },
  "additionalProperties": false
}
```

- [ ] **Step 4: Add contract document**

`agents/project/SESSION-CLOSEOUT-CONTRACT.md` must state:

```markdown
# Session Closeout Contract

## Purpose

Session closeout prevents false "clean" claims by separating baseline state, current dirty work, preserved archives, active branches, worktrees, stashes, and issue handoff records.

## Rules

- Record a baseline at SessionStart before task work.
- Treat `main` checkout as orchestrator-owned during parallel work.
- Classify dirty work before mutating it.
- Preserve unknown or late dirty work before dropping local state.
- Do not auto-push, create issues, merge, delete branches, or drop stashes unless policy allows that specific side effect.
- Final completion claims require fresh `git status -sb`, `git stash list`, `git worktree list --porcelain`, active branch scan, and Owner governance evidence when applicable.
```

- [ ] **Step 5: Run schema test**

Run: `pytest tests/test_session_baseline.py::test_session_baseline_schema_has_required_fields -q`

Expected: `1 passed`.

- [ ] **Step 6: Commit**

```bash
git add agents/project/SESSION-CLOSEOUT-CONTRACT.md schemas/session-baseline.schema.json tests/test_session_baseline.py
git commit -m "docs: define session closeout contract"
```

### Task 2: Implement session baseline snapshot command

**Files:**
- Create: `scripts/session_baseline.py`
- Test: `tests/test_session_baseline.py`
- Create directory at runtime: `agents/runtime/session_baselines/`

- [ ] **Step 1: Add command test with monkeypatched git runner**

```python
from scripts import session_baseline


def test_capture_baseline_uses_git_state(tmp_path, monkeypatch):
    outputs = {
        ("git", "rev-parse", "--short", "HEAD"): "abc1234\n",
        ("git", "branch", "--show-current"): "main\n",
        ("git", "status", "--porcelain=v1"): " M BACKLOG.md\n",
        ("git", "stash", "list", "--format=%H"): "111\n222\n",
        ("git", "worktree", "list", "--porcelain"): "worktree C:/repo\nbranch refs/heads/main\n",
        ("git", "branch", "--list", "codex/*"): "  codex/task\n",
    }

    def fake_run(args, cwd):
        return outputs[tuple(args)]

    monkeypatch.setattr(session_baseline, "run_git", fake_run)
    data = session_baseline.capture(tmp_path)
    assert data["head"] == "abc1234"
    assert data["branch"] == "main"
    assert data["stash_count"] == 2
    assert data["active_codex_branches"] == ["codex/task"]
    assert data["status_fingerprint"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_session_baseline.py::test_capture_baseline_uses_git_state -q`

Expected: `FAILED` with import or attribute error for `session_baseline`.

- [ ] **Step 3: Implement minimal command**

```python
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout


def status_fingerprint(status: str) -> str:
    normalized = "\n".join(sorted(line.rstrip() for line in status.splitlines() if line.strip()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def capture(root: Path) -> dict[str, object]:
    status = run_git(["git", "status", "--porcelain=v1"], root)
    stashes = [line for line in run_git(["git", "stash", "list", "--format=%H"], root).splitlines() if line.strip()]
    branches = [
        line.strip().lstrip("* ").strip()
        for line in run_git(["git", "branch", "--list", "codex/*"], root).splitlines()
        if line.strip()
    ]
    return {
        "schema": "agent-runtime-session-baseline/v1",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cwd": str(root),
        "head": run_git(["git", "rev-parse", "--short", "HEAD"], root).strip(),
        "branch": run_git(["git", "branch", "--show-current"], root).strip(),
        "status_fingerprint": status_fingerprint(status),
        "stash_count": len(stashes),
        "worktrees": [{"raw": run_git(["git", "worktree", "list", "--porcelain"], root)}],
        "active_codex_branches": branches,
    }


def write_baseline(root: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = capture(root)
    stamp = data["captured_at"].replace(":", "").replace("+", "Z")
    path = output_dir / f"session-baseline-{stamp}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output-dir", default="agents/runtime/session_baselines")
    args = parser.parse_args()
    path = write_baseline(Path(args.root).resolve(), Path(args.output_dir))
    print(f"baseline={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run focused tests**

Run: `pytest tests/test_session_baseline.py -q`

Expected: all session baseline tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/session_baseline.py tests/test_session_baseline.py
git commit -m "feat: capture session baseline"
```

### Task 3: Implement dirty intake classifier and safe archive plan

**Files:**
- Create: `scripts/dirty_intake.py`
- Test: `tests/test_dirty_intake.py`

- [ ] **Step 1: Add classifier tests**

```python
from scripts.dirty_intake import classify_status


def test_log_only_changes_are_archive_optional():
    result = classify_status(["?? agents/runtime/hook-logs/stop-owner-governance-1.json"])
    assert result.route == "log_only"
    assert result.side_effect == "drop_allowed_after_owner_policy"


def test_owner_docs_are_in_scope_when_declared():
    result = classify_status([" M BACKLOG.md"], declared_paths={"BACKLOG.md"})
    assert result.route == "in_scope"
    assert result.side_effect == "commit_path"


def test_unknown_dirty_requires_preservation():
    result = classify_status([" M scripts/backlog_board.py"])
    assert result.route == "archive_required"
    assert result.side_effect == "stash_push_issue_pointer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dirty_intake.py -q`

Expected: `FAILED` because `scripts.dirty_intake` does not exist.

- [ ] **Step 3: Implement classifier**

```python
from __future__ import annotations

from dataclasses import dataclass


LOG_PREFIXES = ("agents/runtime/hook-logs/",)


@dataclass(frozen=True)
class DirtyRoute:
    route: str
    side_effect: str
    files: tuple[str, ...]


def _path_from_status(line: str) -> str:
    return line[3:].strip() if len(line) > 3 else line.strip()


def classify_status(lines: list[str], declared_paths: set[str] | None = None) -> DirtyRoute:
    declared_paths = declared_paths or set()
    files = tuple(_path_from_status(line) for line in lines if line.strip())
    if not files:
        return DirtyRoute("clean", "none", files)
    if all(path.startswith(LOG_PREFIXES) for path in files):
        return DirtyRoute("log_only", "drop_allowed_after_owner_policy", files)
    if files and set(files) <= declared_paths:
        return DirtyRoute("in_scope", "commit_path", files)
    return DirtyRoute("archive_required", "stash_push_issue_pointer", files)
```

- [ ] **Step 4: Add archive plan output**

The CLI should print JSON with:

```json
{
  "route": "archive_required",
  "side_effect": "stash_push_issue_pointer",
  "files": ["scripts/backlog_board.py"],
  "commands": [
    "git stash push -u -m \"archive late dirty work <stamp>\"",
    "git push origin <stash-sha>:refs/heads/archive/stashes/<date>/<slug>",
    "create or update GitHub issue with archive ref"
  ]
}
```

- [ ] **Step 5: Run focused tests**

Run: `pytest tests/test_dirty_intake.py -q`

Expected: all dirty intake tests pass.

- [ ] **Step 6: Commit**

```bash
git add scripts/dirty_intake.py tests/test_dirty_intake.py
git commit -m "feat: classify closeout dirty state"
```

### Task 4: Wire SessionStart, Stop, and Owner-doc preflight hooks

**Files:**
- Modify: `.codex/hooks.json`
- Modify: `scripts/owner_governance_gate.py`
- Test: `tests/test_stop_hook_owner_governance.py`
- Test: `tests/test_owner_doc_format_gate.py`

- [ ] **Step 1: Add hook config test**

```python
import json
from pathlib import Path


def test_codex_hooks_include_session_closeout_guards():
    hooks = json.loads(Path(".codex/hooks.json").read_text(encoding="utf-8"))
    text = json.dumps(hooks)
    assert "scripts/session_baseline.py" in text
    assert "scripts/dirty_intake.py" in text
    assert "scripts/owner_doc_format_gate.py" in text
```

- [ ] **Step 2: Run test to verify it fails before wiring**

Run: `pytest tests/test_stop_hook_owner_governance.py::test_codex_hooks_include_session_closeout_guards -q`

Expected: `FAILED` until hook config includes the commands.

- [ ] **Step 3: Add hook wiring**

`.codex/hooks.json` should add:

```json
{
  "SessionStart": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe scripts/session_baseline.py --root .",
          "timeout": 10
        }
      ]
    }
  ],
  "Stop": [
    {
      "matcher": "*",
      "hooks": [
        {
          "type": "command",
          "command": "C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe scripts/dirty_intake.py --root . --check",
          "timeout": 20
        }
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Write|Edit|MultiEdit",
      "hooks": [
        {
          "type": "command",
          "command": "C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe scripts/owner_doc_format_gate.py --manifest owner-docs.yml",
          "timeout": 20
        }
      ]
    }
  ]
}
```

The actual patch must merge with existing hooks instead of replacing existing Owner governance hooks.

- [ ] **Step 4: Run hook tests**

Run: `pytest tests/test_stop_hook_owner_governance.py tests/test_owner_doc_format_gate.py -q`

Expected: hook config and owner-doc checks pass.

- [ ] **Step 5: Commit**

```bash
git add .codex/hooks.json scripts/owner_governance_gate.py tests/test_stop_hook_owner_governance.py tests/test_owner_doc_format_gate.py
git commit -m "feat: wire session closeout hooks"
```

### Task 5: Package session-closeout skill and verification closeout gate

**Files:**
- Create: `skills/session-closeout/SKILL.md`
- Create: `scripts/verify_session_closeout_taskset.py`
- Modify: `scripts/taskset_work_gate.py`
- Test: `tests/test_taskset_work_gate.py`
- Create: `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md`

- [ ] **Step 1: Add skill file**

```markdown
---
name: session-closeout
description: Use when the Owner says 마무리, 정리, closeout, cleanup, or asks whether stash, branch, PR, issue, worktree, archive, or dirty state remains.
---

# Session Closeout

## Required sequence

1. Capture current `git status -sb`, `git stash list`, `git worktree list --porcelain`, and active branch scan.
2. Separate declared current work from late dirty work.
3. For declared work, commit, PR, merge, and sync `main` when Owner policy allows.
4. For late dirty work, preserve with stash and archive ref before dropping local state.
5. Create or update an issue with every archive ref that replaces local state.
6. Delete only active work branches that have been merged or archived.
7. Final claim requires clean `git status -sb`, empty stash list, root-only worktree list, and documented residual archive refs.
```

- [ ] **Step 2: Add verification wrapper**

```python
from __future__ import annotations

import subprocess
import sys


COMMANDS = [
    [sys.executable, "scripts/taskset_work_gate.py", "--task-set-id", "TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION", "--check"],
    [sys.executable, "scripts/owner_governance_gate.py"],
]


def main() -> int:
    for command in COMMANDS:
        result = subprocess.run(command, text=True)
        if result.returncode != 0:
            return result.returncode
    print("session closeout taskset verification: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Add closeout review format**

The closeout review must include:

```markdown
## Bottom Line
## Signal
## Insight
## Decision
## Action Board
## Risks / Blockers
## Next Steps
```

- [ ] **Step 4: Run focused verification**

Run: `python scripts/verify_session_closeout_taskset.py`

Expected: `session closeout taskset verification: passed`.

- [ ] **Step 5: Commit**

```bash
git add skills/session-closeout/SKILL.md scripts/verify_session_closeout_taskset.py scripts/taskset_work_gate.py tests/test_taskset_work_gate.py reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md
git commit -m "feat: package session closeout automation"
```

## Self-Review

- Spec coverage: The plan covers recording, baseline capture, dirty classification, stash/archive/issue preservation, hook/trigger wiring, Owner-doc preflight, skill packaging, and taskset closeout.
- Placeholder scan: No step uses TBD, TODO, "similar to", or unstated implementation.
- Type consistency: `DirtyRoute`, `capture`, `status_fingerprint`, and `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` names remain consistent across tasks.

