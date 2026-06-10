from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "runtime_asset_usage.py"


def load_module():
    spec = importlib.util.spec_from_file_location("runtime_asset_usage", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_missing_registry_blocks(tmp_path):
    usage = load_module()

    findings, metrics = usage.analyze(tmp_path)

    assert metrics == []
    assert any(f.severity == "block" and f.subject == "registry:missing-or-invalid" for f in findings)


def test_missing_active_asset_path_blocks(tmp_path):
    usage = load_module()
    write_json(
        tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json",
        """{
          "schema": "agent-runtime-asset-registry/v1",
          "assets": [
            {
              "id": "hook.missing",
              "kind": "hook",
              "status": "active",
              "lifecycle": "keep",
              "paths": ["scripts/missing_hook.py"],
              "evidence_paths": [],
              "min_recent_uses": 0
            }
          ]
        }""",
    )

    findings, _metrics = usage.analyze(tmp_path)

    assert any(f.severity == "block" and f.subject == "asset-missing:hook.missing" for f in findings)


def test_configured_usage_counts_as_metric(tmp_path):
    usage = load_module()
    write_json(tmp_path / "scripts/taskset_prompt_hook.py", "# taskset_prompt_hook\n")
    write_json(tmp_path / ".codex/hooks.json", '{"command": "scripts\\\\taskset_prompt_hook.cmd", "event": "UserPromptSubmit"}')
    write_json(
        tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json",
        """{
          "schema": "agent-runtime-asset-registry/v1",
          "assets": [
            {
              "id": "hook.taskset_prompt",
              "kind": "hook",
              "status": "active",
              "lifecycle": "keep",
              "paths": ["scripts/taskset_prompt_hook.py"],
              "evidence_paths": [".codex/hooks.json"],
              "tokens": ["taskset_prompt_hook", "UserPromptSubmit"],
              "min_recent_uses": 1
            }
          ]
        }""",
    )

    findings, metrics = usage.analyze(tmp_path)

    assert not [f for f in findings if f.severity == "block"]
    assert metrics[0].usage_count >= 1
    assert metrics[0].distinct_evidence_hits == 1


def test_deprecate_requires_replacement_or_rationale(tmp_path):
    usage = load_module()
    write_json(tmp_path / "scripts/old.py", "# old\n")
    write_json(
        tmp_path / "agents/project/RUNTIME-ASSET-REGISTRY.json",
        """{
          "schema": "agent-runtime-asset-registry/v1",
          "assets": [
            {
              "id": "script.old",
              "kind": "script",
              "status": "active",
              "lifecycle": "deprecate",
              "paths": ["scripts/old.py"],
              "evidence_paths": [],
              "min_recent_uses": 0
            }
          ]
        }""",
    )

    findings, _metrics = usage.analyze(tmp_path)

    assert any(f.severity == "block" and f.subject == "asset-decision-incomplete:script.old" for f in findings)
