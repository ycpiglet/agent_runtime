"""Host-context read-location convention (issue #121 item 2; doc-only scope).

`agents/host/` is the reserved host-owned namespace: templates must never ship
files there, or sync would start managing (and clobbering) host context.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "src" / "agent_runtime" / "templates" / "project"


def test_templates_reserve_the_host_namespace():
    shipped = list((TEMPLATE_ROOT / "agents" / "host").rglob("*")) if (TEMPLATE_ROOT / "agents" / "host").exists() else []
    assert shipped == [], f"templates must not ship files under agents/host/: {shipped}"


def test_convention_doc_exists_and_names_the_entry_point():
    doc = (REPO_ROOT / "docs" / "host-context-read-location.md").read_text(encoding="utf-8")
    assert "agents/host/HOST-CONTEXT.yml" in doc
    assert "sync.unmanaged" in doc
