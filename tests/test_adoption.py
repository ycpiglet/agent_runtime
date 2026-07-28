from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from agent_runtime import cli
from agent_runtime.adoption import build_adoption_plan, plan_json
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
    _write(root, ".gitignore", "ignored/\n.next/\nnode_modules/\n")
    _write(root, "AGENTS.md")
    _write(root, "CLAUDE.md")
    _write(root, ".claude/agents/editor.md")
    _write(root, ".claude/skills/editing/SKILL.md")
    _write(root, "docs/editorial-guide.md")
    _write(root, "src/visible file.ts")
    _write(root, "ignored/secret.md")
    _write(root, ".next/cache/file")
    _write(root, "node_modules/pkg/index.js")
    before = _snapshot(root)
    first, second = build_adoption_plan(root), build_adoption_plan(root)
    assert plan_json(first) == plan_json(second)
    assert first.scan_strategy == "git-ignore-aware"
    assert "ignored/secret.md" not in first.source_paths
    assert ".next/cache/file" in first.generated_paths
    assert "node_modules/pkg/index.js" in first.generated_paths
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
