from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from agent_runtime import cli
from agent_runtime import adoption
from agent_runtime.adoption import build_adoption_plan, plan_json, render
from agent_runtime import doctor


def _write(root: Path, rel: str, text: str = "x\n") -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _git(root: Path) -> None:
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def _snapshot(root: Path) -> tuple[tuple[str, int, int, str], ...]:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            stat = path.stat()
            rows.append((path.relative_to(root).as_posix(), stat.st_mtime_ns, stat.st_size, hashlib.sha256(path.read_bytes()).hexdigest()))
    return tuple(rows)


def test_adoption_git_ignore_generated_and_assets_are_deterministic_and_read_only(tmp_path):
    root = tmp_path / "bean shape"
    root.mkdir()
    _git(root)
    _write(root, ".gitignore", "ignored/\n.next/\nnode_modules/\n.claude/worktrees/\n")
    _write(root, "AGENTS.md")
    _write(root, "CLAUDE.md")
    _write(root, ".claude/agents/editor.md")
    _write(root, ".claude/skills/editing/SKILL.md")
    _write(root, "docs/editorial-guide.md")
    _write(root, "src/visible file.ts")
    _write(root, "ignored/secret.md")
    _write(root, ".next/cache/file")
    _write(root, "node_modules/pkg/index.js")
    _write(root, ".claude/worktrees/feature/.next/cache/file")
    before = _snapshot(root)
    first, second = build_adoption_plan(root), build_adoption_plan(root)
    assert plan_json(first) == plan_json(second)
    assert first.scan_strategy == "git-ignore-aware"
    assert "ignored/secret.md" not in first.source_paths
    assert ".next/cache/file" in first.generated_paths
    assert "node_modules/pkg/index.js" in first.generated_paths
    assert set(first.generated_roots) >= {".next", "node_modules", ".claude/worktrees/feature/.next"}
    assert {"AGENTS.md", "CLAUDE.md", ".claude/agents/editor.md", ".claude/skills/editing/SKILL.md", "docs/editorial-guide.md"} <= set(first.assets)
    assert all(action.path not in {"ignored/secret.md", ".next/cache/file"} or action.action == "skip" for action in first.actions)
    assert _snapshot(root) == before


def test_adoption_fallback_is_conservative_and_records_warning(tmp_path, monkeypatch):
    root = tmp_path / "host"
    root.mkdir()
    _write(root, "src/app.py")
    _write(root, "dist/bundle.js")
    monkeypatch.setattr("agent_runtime.inventory.subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("git")))
    plan = build_adoption_plan(root)
    assert plan.scan_strategy == "filesystem-conservative"
    assert plan.scan_warnings
    assert "src/app.py" in plan.source_paths
    assert "dist/bundle.js" in plan.generated_paths


def test_plan_renderers_do_not_rescan_after_plan_is_built(tmp_path, monkeypatch):
    root = tmp_path / "host"
    root.mkdir()
    _git(root)
    _write(root, ".gitignore", ".next/\n")
    _write(root, ".next/cache/x")
    plan = build_adoption_plan(root)
    monkeypatch.setattr(adoption, "adoption_scan", lambda _root: (_ for _ in ()).throw(AssertionError("renderer rescanned")))
    payload = json.loads(plan_json(plan))
    assert payload["inventory"]["ignored_count"] == plan.ignored_count
    assert payload["inventory"]["generated_roots"] == [".next"]
    assert "generated_roots=.next" in render(plan)


def test_ignored_git_query_failure_falls_back_conservatively(tmp_path, monkeypatch):
    root = tmp_path / "host"
    root.mkdir()
    _git(root)
    _write(root, ".gitignore", "ignored/\n")
    _write(root, "src/app.py")
    _write(root, "ignored/private.md")
    real_run = subprocess.run

    def fail_ignored_query(command, *args, **kwargs):
        if "ls-files" in command and "-oi" in command:
            return subprocess.CompletedProcess(command, 1, b"", b"forced ignored-query failure")
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr("agent_runtime.inventory.subprocess.run", fail_ignored_query)
    plan = build_adoption_plan(root)
    assert plan.scan_strategy == "filesystem-conservative"
    assert plan.scan_warnings
    assert "src/app.py" in plan.source_paths


def test_explicit_generated_missing_skips_while_existing_seed_files_preserve(tmp_path):
    root = tmp_path / "host"
    root.mkdir()
    _git(root)
    _write(
        root,
        "agent_runtime.yml",
        """schema: agent-runtime-config/v2
project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
ownership:
  generated:
    - AGENTS.md
""",
    )
    _write(root, "CURSOR.md", "host cursor\n")
    _write(root, "GEMINI.md", "host gemini\n")
    plan = build_adoption_plan(root)
    actions = {action.path: action for action in plan.actions}
    assert actions["AGENTS.md"].action == "skip"
    assert actions["AGENTS.md"].ownership == "generated"
    assert actions["CURSOR.md"].action == "preserve"
    assert actions["CURSOR.md"].ownership == "seed_once"
    assert actions["GEMINI.md"].action == "preserve"
    assert actions["GEMINI.md"].ownership == "seed_once"


def test_allimbot_shape_and_cli_json_pre_adoption_do_not_write(tmp_path, capsys):
    root = tmp_path / "allimbot"
    root.mkdir()
    _git(root)
    _write(root, ".gitignore", ".venv/\nbuild/\nsupabase/.temp/\n")
    _write(root, "agents/marketplace/catalog.md")
    _write(root, "plugins/security/SKILL.md")
    _write(root, "docs/integration-status-security.md")
    _write(root, ".venv/bin/python")
    _write(root, "build/client.js")
    _write(root, "supabase/.temp/cli")
    before = _snapshot(root)
    assert cli.main(["adopt", "--root", str(root), "--plan", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "agent-runtime-adoption-plan/v1"
    assert {"agents/marketplace/catalog.md", "plugins/security/SKILL.md", "docs/integration-status-security.md"} <= set(payload["assets"])
    assert cli.main(["doctor", "--root", str(root), "--pre-adoption", "--check"]) == 0
    capsys.readouterr()
    pre_plan, _ = doctor.build_pre_adoption_plan(root)
    normal_plan, _ = doctor.build_doctor_plan(root)
    assert pre_plan.blocker_count == 0
    assert normal_plan.blocker_count > 0
    assert _snapshot(root) == before


def test_adopt_requires_plan(tmp_path):
    root = tmp_path / "host"
    root.mkdir()
    try:
        cli.main(["adopt", "--root", str(root)])
    except ValueError as exc:
        assert "requires --plan" in str(exc)
    else:
        raise AssertionError("adopt without --plan must fail")


def test_generated_is_compact_external_symlink_and_bad_config_block(tmp_path, capsys):
    root = tmp_path / "host"
    root.mkdir()
    _git(root)
    _write(root, ".gitignore", "node_modules/\n")
    _write(root, "node_modules/a.js")
    _write(root, "agent_runtime.yml", "schema: agent-runtime-config/v2\nproject:\n  bad: value\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n")
    outside = tmp_path / "outside"
    outside.write_text("x", encoding="utf-8")
    (root / "src-link").symlink_to(outside)
    plan = build_adoption_plan(root)
    assert len(plan.actions) == len({action.path for action in plan.actions})
    assert "node_modules/a.js" not in {action.path for action in plan.actions}
    assert plan.config_invalid and any("external symlink" in finding for finding in plan.findings)
    payload = json.loads(plan_json(plan))
    assert payload["inventory"]["ignored_count"] >= 1
    assert payload["readiness"]["ready"] is False
    assert cli.main(["doctor", "--root", str(root), "--pre-adoption", "--check"]) == 1
    capsys.readouterr()
    assert doctor.main(["--root", str(root), "--pre-adoption", "--check"]) == 1
