from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_runtime import cli
from agent_runtime.config import CANONICAL_HOST_CONTEXT, load_config


def _write(root: Path, text: str) -> None:
    (root / "agent_runtime.yml").write_text(text.strip() + "\n", encoding="utf-8")


def _v2(extra: str = "") -> str:
    return f"""
schema: agent-runtime-config/v2
project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
{extra}
"""


def test_v1_unmanaged_paths_remain_compatible_and_project_full_runtime(tmp_path):
    _write(tmp_path, """project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
  unmanaged:
    - AGENTS.md
    - scripts/check_agent_docs.py
""")
    config = load_config(tmp_path)
    assert config.unmanaged_paths == ("AGENTS.md", "scripts/check_agent_docs.py")
    assert config.profiles == ("core", "web-content", "security-service")
    assert config.ownership_for("host_owned") == config.unmanaged_paths


def test_v2_profiles_and_capabilities_are_registry_ordered(tmp_path):
    _write(tmp_path, _v2("""profiles:
  - security-service
  - core
  - security-service
capabilities:
  - web-content
"""))
    config = load_config(tmp_path)
    assert config.profiles == ("core", "security-service")
    assert config.capabilities == (
        "lifecycle", "continuity", "verification", "compound", "scribe", "model-routing", "web-content", "security-service"
    )


@pytest.mark.parametrize("extra, match", [
    ("profiles:\n  - unknown", "unknown profile"),
    ("profiles:\n  - full-runtime\n  - core", "cannot be combined"),
    ("capabilities:\n  - unknown", "unknown capability"),
    ("ownership:\n  managed:\n    - scripts\n  host_owned:\n    - scripts/check.py", "mixed ownership overlap"),
    ("ownership:\n  managed:\n    - agents/host/NOTE.md", "may only be host_owned"),
    ("ownership:\n  managed:\n    - ../escape", "safe repo-relative"),
])
def test_v2_invalid_selection_or_ownership_blocks(tmp_path, extra, match):
    _write(tmp_path, _v2(extra))
    with pytest.raises(ValueError, match=match):
        load_config(tmp_path)


def test_host_context_is_optional_and_consumed_from_canonical_location(tmp_path):
    _write(tmp_path, _v2("""host:
  context: agents/host/HOST-CONTEXT.yml
  role_overlay: agents/host/ROLE-OVERLAY.yml
  risk_paths:
    - app/production
  state_adapters:
    status: STATUS.md
    backlog: BACKLOG.md
"""))
    absent = load_config(tmp_path)
    assert absent.host_context.path == CANONICAL_HOST_CONTEXT
    assert not absent.host_context.present
    context = tmp_path / CANONICAL_HOST_CONTEXT
    context.parent.mkdir(parents=True)
    context.write_text("""schema: host-context/v1
purpose: >-
  teach coffee
domain: editorial
safety_constraints:
  - no live orders
role_mapping:
  lead_engineer: platform
read_more:
  - agents/host/GLOSSARY.md
""", encoding="utf-8")
    config = load_config(tmp_path)
    assert config.host_context.present
    assert config.host_context.purpose == "teach coffee"
    assert config.host_context.role_mapping == (("lead_engineer", "platform"),)
    assert config.role_overlay == "agents/host/ROLE-OVERLAY.yml"
    assert dict(config.state_adapters) == {"backlog": "BACKLOG.md", "status": "STATUS.md"}


def test_invalid_present_host_context_blocks(tmp_path):
    _write(tmp_path, _v2())
    context = tmp_path / CANONICAL_HOST_CONTEXT
    context.parent.mkdir(parents=True)
    context.write_text("schema: host-context/v2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="host-context/v1"):
        load_config(tmp_path)


def test_doctor_json_is_valid_for_effective_and_invalid_config(tmp_path, capsys):
    _write(tmp_path, _v2("profiles:\n  - web-content"))
    assert cli.main(["doctor", "--root", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "agent-runtime-doctor/v1"
    assert payload["config"]["profiles"] == ["core", "web-content"]
    assert payload["config"]["valid"] is True
    _write(tmp_path, _v2("profiles:\n  - not-real"))
    assert cli.main(["doctor", "--root", str(tmp_path), "--json", "--check"]) == 1
    invalid = json.loads(capsys.readouterr().out)
    assert invalid["config"]["valid"] is False
    assert any(finding["kind"] == "config-invalid" for finding in invalid["findings"])
