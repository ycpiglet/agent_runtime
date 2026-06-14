"""Regression guards for the host-filed bugs (TASK-AR-532).

The council found #21 (cp949) and #20 (stale config) already mitigated in v0.2.0
and #19 (template doc links) fixable with the dot-file/template work -- so these
are verify-first: lock the fixes so they cannot silently regress.
"""

import io
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
HOST = ROOT / "tests" / "fixtures" / "host"


def test_template_role_docs_have_no_broken_links() -> None:
    """GH #19 / BUG-004: template role SKILL.md docs must not link to unshipped files."""
    base = ROOT / "src" / "agent_runtime" / "templates" / "project"
    missing: list[str] = []
    for skill in base.rglob("agents/*/SKILL.md"):
        text = skill.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"\]\(([^)]+\.(?:md|json|yml))\)", text):
            target = match.group(1).split("#")[0]
            if target.startswith("http"):
                continue
            if not (skill.parent / target).resolve().exists():
                missing.append(f"{skill.parent.name}/{skill.name} -> {target}")
    assert missing == [], missing


def test_build_sync_plan_rejects_non_path_like() -> None:
    """GH #20 / BUG-001: a stale config arg must raise a CLEAR TypeError, not AttributeError."""
    from agent_runtime import sync

    class StaleConfig:  # an old config object passed where a path is expected
        pass

    with pytest.raises(TypeError, match="path-like"):
        sync.build_sync_plan(HOST, template_root=StaleConfig())


def test_print_output_is_cp949_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    """GH #21 / BUG-002: sync output must not crash on a cp949 console with non-cp949 chars."""
    from agent_runtime import sync

    class FakeStdout(io.StringIO):
        encoding = "cp949"

    fake = FakeStdout()
    monkeypatch.setattr(sys, "stdout", fake)
    # The snowman is not encodable in cp949; with errors="replace" it must NOT raise.
    sync._print_output("snowman ☃ plus 한글 ok")
    assert "ok" in fake.getvalue()
