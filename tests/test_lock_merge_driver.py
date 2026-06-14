"""Tests for lock_merge_driver — auto-resolve the derived host lock on merge.

The host lock is a digest over every template file, so concurrent template branches
collide on it (COMPOUND-2026-06-14-003). A `true` merge driver suppresses the conflict
and a post-merge hook regenerates the authoritative lock. RETRO-2026-06-14 action #1.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lock_merge_driver as lmd  # noqa: E402

FIXTURE_LOCK = ROOT / "tests" / "fixtures" / "host" / "agent_runtime.lock.json"
FIXTURE_HOST = FIXTURE_LOCK.parent


def test_host_roots_includes_fixture():
    roots = lmd._host_roots()
    assert FIXTURE_HOST.resolve() in {r.resolve() for r in roots}


def test_regenerate_noop_when_current():
    # the committed fixture lock already matches the template tree
    assert lmd.regenerate(FIXTURE_HOST) is False


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
    assert lmd.install(tmp_path) == 0
    assert lmd.install(tmp_path) == 0  # idempotent

    def _cfg(key):
        return subprocess.run(["git", "config", "--get", key], cwd=tmp_path, capture_output=True, text=True).stdout.strip()

    assert _cfg(f"merge.{lmd.DRIVER_NAME}.driver") == "true"
    assert _cfg("core.hooksPath") == ".githooks"


def test_committed_post_merge_hook_invokes_driver():
    hook = ROOT / ".githooks" / "post-merge"
    assert hook.exists()
    assert "lock_merge_driver.py post-merge" in hook.read_text(encoding="utf-8")


def test_gitattributes_declares_driver():
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "agent_runtime.lock.json merge=arlock-keepours" in attrs
