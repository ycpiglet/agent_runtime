"""Tests for lock_merge_driver — auto-resolve the derived host lock on merge.

The host lock is a digest over every template file, so concurrent template branches
collide on it (COMPOUND-2026-06-14-003). A `true` merge driver suppresses the conflict
and a post-merge hook regenerates the authoritative lock. RETRO-2026-06-14 action #1.
"""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lock_merge_driver as lmd  # noqa: E402

FIXTURE_LOCK = ROOT / "tests" / "fixtures" / "host" / "agent_runtime.lock.json"
FIXTURE_HOST = FIXTURE_LOCK.parent


def test_host_roots_includes_fixture():
    roots = lmd._host_roots()
    assert FIXTURE_HOST.resolve() in {r.resolve() for r in roots}


def test_regenerate_noop_when_current():
    # The committed fixture lock must already match the template tree. Assert by
    # comparing content READ-ONLY instead of calling regenerate(FIXTURE_HOST):
    # regenerate() rewrites the tracked fixture when stale, so the old form
    # silently mutated the checkout exactly when it failed — which then made the
    # local repro look "already current" and hid the diagnosis
    # (casebook: nonhermetic-test-tracked-mutation; observed 2026-07-04 on PR #254).
    # Staleness recovery itself is covered hermetically by
    # test_regenerate_restores_stale_lock on a tmp copy.
    from agent_runtime import lock

    plan = lock.build_lock_plan(FIXTURE_HOST)
    expected = json.dumps(plan.record, indent=2, sort_keys=True) + "\n"
    actual = FIXTURE_LOCK.read_text(encoding="utf-8")
    # Regen with: python scripts/lock_merge_driver.py pre-commit (templates staged)
    assert actual == expected


def test_regenerate_restores_stale_lock(tmp_path):
    # copy the fixture host into a tmp dir, corrupt the lock, regenerate
    host = tmp_path / "host"
    host.mkdir()
    (host / "agent_runtime.yml").write_text((FIXTURE_HOST / "agent_runtime.yml").read_text(encoding="utf-8"), encoding="utf-8")
    (host / "agent_runtime.lock.json").write_text('{"stale": true}\n', encoding="utf-8")
    assert lmd.regenerate(host) is True
    record = json.loads((host / "agent_runtime.lock.json").read_text(encoding="utf-8"))
    assert record["installed"]["template_digest"].startswith("sha256:")
    # second run is a no-op now that it is current
    assert lmd.regenerate(host) is False
    # and it equals what the canonical writer would produce
    assert (host / "agent_runtime.lock.json").read_text(encoding="utf-8") == FIXTURE_LOCK.read_text(encoding="utf-8")


def test_install_sets_driver_and_hookspath(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert lmd.install(tmp_path, posix=False) == 0
    assert lmd.install(tmp_path, posix=False) == 0  # idempotent

    def _cfg(key):
        return subprocess.run(["git", "config", "--get", key], cwd=tmp_path, capture_output=True, text=True).stdout.strip()

    assert _cfg(f"merge.{lmd.DRIVER_NAME}.driver") == "true"
    assert _cfg("core.hooksPath") == ".githooks"


@pytest.mark.skipif(os.name == "nt", reason="POSIX execute bits are not represented by Windows chmod")
def test_install_repairs_pre_commit_executable_mode(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    hook = tmp_path / ".githooks" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hook.chmod(0o644)

    assert lmd.install(tmp_path, posix=True) == 0
    assert stat.S_IMODE(hook.stat().st_mode) == 0o755

    subprocess.run(
        ["git", "config", "user.email", "hook-test@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Hook Test"], cwd=tmp_path, check=True)
    marker = tmp_path / "hook-ran"
    hook.write_text(f"#!/bin/sh\nprintf ran > '{marker.as_posix()}'\n", encoding="utf-8")
    hook.chmod(0o644)
    assert lmd.install(tmp_path, posix=True) == 0
    assert stat.S_IMODE(hook.stat().st_mode) == 0o755
    subprocess.run(["git", "commit", "--allow-empty", "-m", "hook probe"], cwd=tmp_path, check=True)
    assert marker.read_text(encoding="utf-8") == "ran"


def test_install_rejects_missing_posix_hook_before_configuring(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)

    assert lmd.install(tmp_path, posix=True) == 1
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert configured.returncode != 0


def test_install_rejects_non_regular_posix_hook_before_configuring(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".githooks" / "pre-commit").mkdir(parents=True)

    assert lmd.install(tmp_path, posix=True) == 1
    configured = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert configured.returncode != 0


def test_executable_repair_is_noop_on_non_posix(tmp_path):
    hook = tmp_path / ".githooks" / "pre-commit"
    hook.parent.mkdir()
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    before = hook.stat().st_mode

    assert lmd.repair_pre_commit_executable(tmp_path, posix=False) is False
    assert hook.stat().st_mode == before


def test_executable_repair_refuses_non_regular_hook(tmp_path):
    hook = tmp_path / ".githooks" / "pre-commit"
    hook.mkdir(parents=True)

    assert lmd.repair_pre_commit_executable(tmp_path, posix=True) is False
    assert lmd.is_pre_commit_executable(tmp_path, posix=True) is False


def test_executable_repair_refuses_linked_hooks_directory(tmp_path):
    repo = tmp_path / "repo"
    outside = tmp_path / "outside"
    repo.mkdir()
    outside.mkdir()
    hook = outside / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    before = hook.stat().st_mode
    linked = repo / ".githooks"
    if os.name == "nt":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(linked), str(outside)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        linked.symlink_to(outside, target_is_directory=True)

    assert lmd.repair_pre_commit_executable(repo, posix=True) is False
    assert lmd.is_pre_commit_executable(repo, posix=True) is False
    assert hook.stat().st_mode == before


def test_executable_repair_refuses_multi_link_hook(tmp_path):
    repo = tmp_path / "repo"
    hooks = repo / ".githooks"
    hooks.mkdir(parents=True)
    outside = tmp_path / "outside-hook"
    outside.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hook = hooks / "pre-commit"
    os.link(outside, hook)
    before = outside.stat().st_mode
    assert hook.stat().st_nlink > 1

    assert lmd.repair_pre_commit_executable(repo, posix=True) is False
    assert lmd.is_pre_commit_executable(repo, posix=True) is False
    assert outside.stat().st_mode == before


def test_committed_post_merge_hook_invokes_driver():
    hook = ROOT / ".githooks" / "post-merge"
    assert hook.exists()
    assert "lock_merge_driver.py post-merge" in hook.read_text(encoding="utf-8")


def test_gitattributes_declares_driver():
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "agent_runtime.lock.json merge=arlock-keepours" in attrs


def test_pre_commit_noop_without_staged_templates(monkeypatch):
    calls = []
    monkeypatch.setattr(
        lmd, "_git",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, stdout="README.md\nscripts/foo.py\n", stderr=""),
    )
    monkeypatch.setattr(lmd, "post_merge", lambda: calls.append(1) or 0)
    assert lmd.pre_commit() == 0
    assert calls == []  # ordinary commits stay fast: no regen


def test_pre_commit_regenerates_when_template_staged(monkeypatch):
    calls = []
    monkeypatch.setattr(
        lmd, "_git",
        lambda *a, **k: subprocess.CompletedProcess(
            a, 0, stdout="src/agent_runtime/templates/project/scripts/x.py\n", stderr=""
        ),
    )
    monkeypatch.setattr(lmd, "post_merge", lambda: calls.append(1) or 0)
    assert lmd.pre_commit() == 0
    assert calls == [1]


def test_committed_pre_commit_hooks_invoke_driver():
    # Both the repo hook and the shipped template hook must wire the staged-template
    # lock regen, or a template commit goes stale until CI (template-stale-host-lock).
    for hook in (
        ROOT / ".githooks" / "pre-commit",
        ROOT / "src" / "agent_runtime" / "templates" / "project" / ".githooks" / "pre-commit",
    ):
        assert "lock_merge_driver.py pre-commit" in hook.read_text(encoding="utf-8"), hook


def test_committed_pre_commit_hooks_are_tracked_executable():
    paths = (
        ".githooks/pre-commit",
        "src/agent_runtime/templates/project/.githooks/pre-commit",
    )
    result = subprocess.run(
        ["git", "ls-files", "-s", *paths],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    modes = {line.split(maxsplit=1)[0] for line in result.stdout.splitlines()}
    assert modes == {"100755"}
