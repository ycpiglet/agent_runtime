from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PACKET_SCRIPT = (
    PACKAGE_ROOT
    / "src"
    / "agent_runtime"
    / "templates"
    / "project"
    / "scripts"
    / "agent_context_packet.py"
)


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_context_packet_module():
    spec = importlib.util.spec_from_file_location("agent_context_packet_under_test", CONTEXT_PACKET_SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_project_context_overlay_prefers_host_context_over_example(tmp_path):
    packet = _load_context_packet_module()
    _write(tmp_path / "agents" / "project" / "README.md", "policy\n")
    _write(tmp_path / "agents" / "project" / "PROJECT-CONTEXT.example.yml", "example\n")
    _write(tmp_path / "agents" / "project" / "PROJECT-CONTEXT.yml", "actual\n")
    _write(tmp_path / "agents" / "project" / "CONTEXT-SOURCES.yml", "sources\n")
    _write(tmp_path / "agents" / "project" / "EVAL-POLICY.yml", "evals\n")
    _write(tmp_path / "agents" / "project" / "SKILL-GOVERNANCE.md", "skills\n")
    _write(tmp_path / "agents" / "project" / "VISION.md", "vision\n")
    _write(tmp_path / "agents" / "project" / "teams" / "product-core.md", "team\n")

    result = packet.discover_project_context_files(tmp_path)

    assert "agents/project/README.md" in result
    assert "agents/project/PROJECT-CONTEXT.yml" in result
    assert "agents/project/CONTEXT-SOURCES.yml" in result
    assert "agents/project/EVAL-POLICY.yml" in result
    assert "agents/project/SKILL-GOVERNANCE.md" in result
    assert "agents/project/VISION.md" in result
    assert "agents/project/teams/product-core.md" in result
    assert "agents/project/PROJECT-CONTEXT.example.yml" not in result


def test_project_context_overlay_uses_example_until_host_context_exists(tmp_path):
    packet = _load_context_packet_module()
    _write(tmp_path / "agents" / "project" / "README.md", "policy\n")
    _write(tmp_path / "agents" / "project" / "PROJECT-CONTEXT.example.yml", "example\n")

    result = packet.discover_project_context_files(tmp_path)

    assert result == [
        "agents/project/README.md",
        "agents/project/PROJECT-CONTEXT.example.yml",
    ]
