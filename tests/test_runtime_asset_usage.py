from __future__ import annotations

import importlib.util
import json
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


def write_manifest(root: Path, *, core: list[str] | None = None) -> None:
    write_json(
        root / "agents/project/RUNTIME-PROFILE-MANIFEST.json",
        '{"schema":"agent-runtime-template-profiles/v1","profiles":{"core":{"include":'
        + json.dumps(core or ["**"])
        + ',"exclude":[]},"web-content":{"include":[],"exclude":[]},"security-service":{"include":[],"exclude":[]}}}',
    )


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
    write_manifest(tmp_path)
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


def test_profile_matrix_is_deterministic_and_security_is_additive():
    usage = load_module()
    root = Path(__file__).resolve().parents[1] / "src/agent_runtime/templates/project"
    first = usage.profile_matrix(root)
    assert first == usage.profile_matrix(root)
    assert first["core"] == first["core+web-content"]
    assert first["core+security-service"]["selected_files"] > first["core"]["selected_files"]
    assert first["full-runtime"] == first["core+security-service"]
    core = usage._profile_paths(root, ("core",))
    security = usage._profile_paths(root, ("core", "security-service"))
    assert "scripts/allimbot.py" not in core
    assert {
        ".allimbot.json",
        "agents/project/SECURITY-SERVICE-POLICY.json",
        "docs/security-service.md",
        "scripts/allimbot.py",
        "scripts/security_service_gate.py",
    } <= security
    assert "scripts/allimbot_stop_hook.cmd" not in core
    assert "scripts/allimbot_stop_hook.cmd" not in security
    assert "skills/failure-to-regression/SKILL.md" in core


def test_failure_to_regression_skill_is_registered_on_source_and_consumer_surfaces():
    root = Path(__file__).resolve().parents[1]
    source_registry = json.loads(
        (root / "agents/project/RUNTIME-ASSET-REGISTRY.json").read_text(
            encoding="utf-8"
        )
    )
    template_root = root / "src/agent_runtime/templates/project"
    consumer_registry = json.loads(
        (
            template_root / "agents/project/RUNTIME-ASSET-REGISTRY.json"
        ).read_text(encoding="utf-8")
    )
    source_asset = next(
        asset
        for asset in source_registry["assets"]
        if asset["id"] == "skill.failure_to_regression"
    )
    consumer_asset = next(
        asset
        for asset in consumer_registry["assets"]
        if asset["id"] == "skill.failure_to_regression"
    )

    assert source_asset["paths"] == [
        "skills/failure-to-regression/SKILL.md",
        "src/agent_runtime/templates/project/skills/failure-to-regression/SKILL.md",
    ]
    assert consumer_asset["paths"] == [
        "skills/failure-to-regression/SKILL.md"
    ]
    assert (
        template_root / "skills/failure-to-regression/SKILL.md"
    ).is_file()


def test_missing_and_cross_profile_findings_are_distinct(tmp_path):
    usage = load_module()
    findings = []
    asset = {"id": "script.edge", "kind": "script", "status": "active", "lifecycle": "keep", "paths": ["scripts/edge.py"]}
    usage._analyze_asset(tmp_path, asset, findings, {"scripts/edge.py"})
    assert any(f.subject == "asset-missing:script.edge" for f in findings)
    (tmp_path / "scripts").mkdir(); (tmp_path / "scripts/edge.py").write_text("# edge")
    findings = []
    usage._analyze_asset(tmp_path, asset, findings, set())
    assert any(f.subject == "asset-cross-profile:script.edge" for f in findings)
