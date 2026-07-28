from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_runtime import cli
from agent_runtime.config import CANONICAL_HOST_CONTEXT, _scalar, load_config


def _write(root: Path, text: str) -> None:
    (root / "agent_runtime.yml").write_text(text.strip() + "\n", encoding="utf-8")


def _write_raw(root: Path, text: str) -> None:
    (root / "agent_runtime.yml").write_text(text, encoding="utf-8")


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


def test_v1_unmanaged_backslashes_keep_legacy_posix_normalization(tmp_path):
    _write(tmp_path, """project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
  unmanaged:
    - agents\\host\\NOTES.md
""")
    config = load_config(tmp_path)
    assert config.unmanaged_paths == ("agents/host/NOTES.md",)
    assert config.ownership_for("host_owned") == ("agents/host/NOTES.md",)


def test_v2_defaults_to_core_and_full_runtime_expands_in_registry_order(tmp_path):
    _write(tmp_path, _v2())
    assert load_config(tmp_path).profiles == ("core",)
    _write(tmp_path, _v2("profiles:\n  - full-runtime"))
    assert load_config(tmp_path).profiles == ("core", "web-content", "security-service")


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


@pytest.mark.parametrize("extra, match", [
    ("profilse: nope", "unknown root keys"),
    ("upstream:\n  pakcage: nope", "upstream has unknown keys"),
    ("host:\n  role_overly: agents/host/X.yml", "host has unknown keys"),
    ("ownership:\n  managed:\n    - C:/temp/x", "safe repo-relative"),
    ("ownership:\n  managed:\n    - internal//path", "safe repo-relative"),
    ("ownership:\n  managed:\n    - agents/host", "may only be host_owned"),
])
def test_v2_schema_is_fail_closed(tmp_path, extra, match):
    _write(tmp_path, _v2(extra))
    with pytest.raises(ValueError, match=match):
        load_config(tmp_path)


@pytest.mark.parametrize("sync_extra, match", [
    ("  typo: nope", "sync has unknown keys"),
    ("  unmanaged:\n    - AGENTS.md", "v2 sync.unmanaged"),
])
def test_v2_sync_is_fail_closed(tmp_path, sync_extra, match):
    _write(tmp_path, """schema: agent-runtime-config/v2
project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
""" + sync_extra)
    with pytest.raises(ValueError, match=match):
        load_config(tmp_path)


@pytest.mark.parametrize("mode", ["managed", "seed_once", "generated"])
def test_exact_host_namespace_is_host_owned_only(tmp_path, mode):
    _write(tmp_path, _v2(f"ownership:\n  {mode}:\n    - agents/host"))
    with pytest.raises(ValueError, match="may only be host_owned"):
        load_config(tmp_path)


def test_schema_less_documents_reject_v2_fields_and_explicit_v1(tmp_path):
    _write(tmp_path, """project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
profiles:
  - core
""")
    with pytest.raises(ValueError, match="unknown root keys"):
        load_config(tmp_path)
    _write(tmp_path, _v2().replace("agent-runtime-config/v2", "agent-runtime-config/v1"))
    with pytest.raises(ValueError, match="unsupported schema"):
        load_config(tmp_path)


def test_malformed_top_level_and_quoted_scalars_block(tmp_path):
    _write_raw(tmp_path, "  project: demo\n  sync:\n    mode: check-diff-apply\n    allow_silent_overwrite: false\n")
    with pytest.raises(ValueError, match="zero-indented"):
        load_config(tmp_path)
    _write_raw(tmp_path, """schema: agent-runtime-config/v2
project: 'unterminated
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
""")
    with pytest.raises(ValueError, match="malformed quoted scalar"):
        load_config(tmp_path)


def test_host_context_scalar_comments_preserve_apostrophes_and_quoted_hashes(tmp_path):
    _write(tmp_path, _v2())
    context = tmp_path / CANONICAL_HOST_CONTEXT
    context.parent.mkdir(parents=True)
    context.write_text(
        "schema: host-context/v1\n"
        "purpose: world's coffee # trailing comment\n"
        'domain: "editors # research" # trailing comment\n',
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.host_context.purpose == "world's coffee"
    assert config.host_context.domain == "editors # research"


def test_quoted_scalar_tail_requires_whitespace_before_a_comment():
    assert _scalar('"x" # good') == "x"
    with pytest.raises(ValueError, match="malformed quoted scalar"):
        _scalar('"x"#bad')


def test_host_context_is_optional_and_consumed_from_canonical_location(tmp_path):
    _write(tmp_path, _v2("""host:
  context: agents/host/HOST-CONTEXT.yml
  role_overlay: agents/host/ROLE-OVERLAY.yml
  risk_paths:
    - app/production/
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
    assert config.risk_paths == ("app/production",)
    assert dict(config.state_adapters) == {"backlog": "BACKLOG.md", "status": "STATUS.md"}


def test_invalid_present_host_context_blocks(tmp_path):
    _write(tmp_path, _v2())
    context = tmp_path / CANONICAL_HOST_CONTEXT
    context.parent.mkdir(parents=True)
    context.write_text("schema: host-context/v2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="host-context/v1"):
        load_config(tmp_path)


@pytest.mark.parametrize("context_body, match", [
    ("purpose:\n  nested: value", "purpose must be a scalar"),
    ("domain:\n  - editorial", "domain must be a scalar"),
    ("role_mapping:\n  lead_engineer:\n    team: platform", "role_mapping values"),
    ("unexpected: value", "unknown keys"),
])
def test_host_context_rejects_non_scalar_or_unknown_shapes(tmp_path, context_body, match):
    _write(tmp_path, _v2())
    context = tmp_path / CANONICAL_HOST_CONTEXT
    context.parent.mkdir(parents=True)
    context.write_text("schema: host-context/v1\n" + context_body + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        load_config(tmp_path)


def test_doctor_json_is_valid_for_effective_and_invalid_config(tmp_path, capsys):
    _write(tmp_path, _v2("profiles:\n  - web-content"))
    assert cli.main(["doctor", "--root", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "agent-runtime-doctor/v1"
    assert payload["config"]["profiles"] == ["core", "web-content"]
    assert payload["config"]["valid"] is True
    assert payload["config"]["source_path"] == "agent_runtime.yml"
    _write(tmp_path, _v2("profiles:\n  - not-real"))
    assert cli.main(["doctor", "--root", str(tmp_path), "--json", "--check"]) == 1
    invalid = json.loads(capsys.readouterr().out)
    assert invalid["config"]["valid"] is False
    assert invalid["config"]["source_path"] == "agent_runtime.yml"
    assert any(finding["kind"] == "config-invalid" for finding in invalid["findings"])


def test_doctor_json_missing_and_legacy_source_paths_are_relative(tmp_path, capsys):
    assert cli.main(["doctor", "--root", str(tmp_path), "--json", "--check"]) == 1
    missing = json.loads(capsys.readouterr().out)
    assert missing["config"]["source_path"] == "agent_runtime.yml"
    (tmp_path / "ralph.yml").write_text("""project: demo
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
""", encoding="utf-8")
    assert cli.main(["doctor", "--root", str(tmp_path), "--json"]) == 0
    legacy = json.loads(capsys.readouterr().out)
    assert legacy["config"]["source_path"] == "ralph.yml"
