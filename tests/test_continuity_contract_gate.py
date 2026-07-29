from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "continuity_contract_gate.py"


def _run_gate(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), "--check"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _portable_contract() -> str:
    return "\n".join(
        [
            "# Agent Runtime",
            "",
            "## 한국어",
            "",
            "AGENTS.md, CLAUDE.md, agents/project/, NEXT-SESSION-POINTER.yml",
            "",
            "## English",
            "",
            "Maintain active_work, pane_id, and progress_pct in the pointer.",
            "Use Evaluate -> Propose -> Verify -> Merge.",
            "Repeated Request API promotes repetition into a function/API.",
            "Compound capture is automatic and mandatory for repeated mistakes.",
            "Preserve a golden set of failures and edge cases.",
            "Owner retains final criteria and merge authority.",
            "",
        ]
    )


def _valid_pointer() -> str:
    return "\n".join(
        [
            "schema: agent-runtime-next-session-pointer/v1",
            "updated_at: 2026-07-30T00:00:00+09:00",
            "current_state:",
            "  task_set_id: TASKSET-CONSUMER",
            "  step_index: 1",
            "  step_total: 2",
            "  status_text: ready",
            "active_work:",
            "  current_agents: []",
            "resume:",
            "  active_task: TASK-CONSUMER",
            "roles:",
            "  owner: Owner",
            "pointers:",
            "  active_claims: []",
            "rules:",
            "  fail_closed: true",
            "verification:",
            "  required: []",
            "",
        ]
    )


def _strict_readme() -> str:
    return "\n".join(
        [
            "# Runtime source",
            "## 한국어",
            "AGENTS.md CLAUDE.md NEXT-SESSION-POINTER.yml agents/project/",
            "## English",
            "AGENTS.md CLAUDE.md NEXT-SESSION-POINTER.yml agents/project/",
            "",
        ]
    )


def _write_config(
    root: Path,
    *,
    project: str = "consumer-host",
    ownership: str = "host_owned",
    upstream_ref: str = "product-commit",
) -> None:
    _write(
        root / "agent_runtime.yml",
        "\n".join(
            [
                "schema: agent-runtime-config/v2",
                f"project: {project}",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/ycpiglet/agent_runtime.git",
                f"  ref: {upstream_ref}",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "profiles:",
                "  - core",
                "ownership:",
                f"  {ownership}:",
                "    - AGENTS.md",
                "    - CLAUDE.md",
                "",
            ]
        ),
    )


def _write_lock(
    root: Path,
    *,
    project: str = "consumer-host",
    ownership: str = "host_owned",
    upstream_ref: str = "product-commit",
) -> None:
    managed_paths = ("AGENT_RUNTIME.md", "scripts/continuity_contract_gate.py")
    record = {
        "schema": "agent-runtime-lock/v2",
        "project": project,
        "profiles": ["core"],
        "capabilities": ["continuity"],
        "upstream": {
            "package": "agent_runtime",
            "remote_url": "https://github.com/ycpiglet/agent_runtime.git",
            "ref": upstream_ref,
        },
        "installed": {
            "package_version": "0.8.0-test",
            "ownership": {
                "AGENTS.md": ownership,
                "AGENT_RUNTIME.md": "managed",
                "CLAUDE.md": ownership,
                "agents/project/NEXT-SESSION-POINTER.yml": "seed_once",
                "scripts/continuity_contract_gate.py": "managed",
            },
            "managed_files": {
                rel: _digest(root / rel)
                for rel in managed_paths
            },
            "seeded": [
                "AGENTS.md",
                "CLAUDE.md",
                "agents/project/NEXT-SESSION-POINTER.yml",
            ],
        },
    }
    _write(root / "agent_runtime.lock.json", json.dumps(record, indent=2, sort_keys=True) + "\n")


def _prepare_consumer(
    root: Path,
    *,
    ownership: str = "host_owned",
    strict_host_docs: bool = False,
) -> None:
    _write_config(root, ownership=ownership)
    _write(root / "AGENT_RUNTIME.md", _portable_contract())
    target_gate = root / "scripts" / "continuity_contract_gate.py"
    target_gate.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SCRIPT, target_gate)
    _write(root / "README.md", _strict_readme() if strict_host_docs else "# Host product\n")
    protocol = _portable_contract() if strict_host_docs else "# Host-owned product protocol\n"
    _write(root / "AGENTS.md", protocol)
    _write(root / "CLAUDE.md", protocol)
    _write(root / "agents" / "project" / "NEXT-SESSION-POINTER.yml", _valid_pointer())
    _write_lock(root, ownership=ownership)


def test_continuity_contract_gate_blocks_missing_resume_pointer(tmp_path: Path):
    _write(tmp_path / "README.md", "# Agent Runtime\n\n## 한국어\n\n## English\n")
    _write(tmp_path / "src" / "agent_runtime" / "templates" / "project" / "AGENTS.md", "## Session Continuity\n")
    _write(tmp_path / "src" / "agent_runtime" / "templates" / "project" / "CLAUDE.md", "## Session Continuity\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:pointer-missing" in result.stdout


def test_continuity_contract_gate_requires_bilingual_readme_and_self_improvement_rules(tmp_path: Path):
    _write(tmp_path / "README.md", "# Agent Runtime\n")
    _write(
        tmp_path / "src" / "agent_runtime" / "templates" / "project" / "AGENTS.md",
        "\n".join(
            [
                "## Session Continuity",
                "- Maintain `agents/project/NEXT-SESSION-POINTER.yml`.",
            ]
        ),
    )
    _write(
        tmp_path / "src" / "agent_runtime" / "templates" / "project" / "CLAUDE.md",
        "\n".join(
            [
                "## Session Continuity",
                "- Maintain `agents/project/NEXT-SESSION-POINTER.yml`.",
            ]
        ),
    )
    _write(
        tmp_path / "src" / "agent_runtime" / "templates" / "project" / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        "schema: agent-runtime-next-session-pointer/v1\n",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:readme-korean-section-missing" in result.stdout
    assert "continuity:readme-english-section-missing" in result.stdout
    assert "continuity:pointer-field-missing:step_index" in result.stdout
    assert "continuity:pointer-field-missing:status_text" in result.stdout
    assert "continuity:repeated-request-api-rule-missing" in result.stdout
    assert "continuity:compound-auto-capture-rule-missing" in result.stdout


def test_owner_governance_runs_continuity_contract_gate():
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert "continuity_contract_gate.py" in root_gate
    assert "continuity_contract_gate.py" in template_gate


def test_continuity_gate_accepts_root_protocol_docs_without_template_tree(tmp_path: Path):
    # Generated consumer-project layout: protocol docs live at the project ROOT and
    # the src/agent_runtime/templates/** tree is absent. The gate must not report
    # protocol-doc-missing in that case (issue #185).
    _write(tmp_path / "README.md", "# X\n## 한국어\n## English\nAGENTS.md CLAUDE.md NEXT-SESSION-POINTER.yml agents/project/\n")
    _write(tmp_path / "AGENTS.md", "## Protocol\nNEXT-SESSION-POINTER.yml active_work\n")
    _write(tmp_path / "CLAUDE.md", "## Protocol\n")

    result = _run_gate(tmp_path)

    assert "continuity:protocol-doc-missing" not in result.stdout


def test_continuity_gate_flags_protocol_docs_missing_from_all_locations(tmp_path: Path):
    # No protocol docs at root OR template path -> the check must still fire.
    _write(tmp_path / "README.md", "# X\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:protocol-doc-missing" in result.stdout


def test_generated_consumer_preserves_host_owned_docs_and_unmanaged_readme(tmp_path: Path):
    _prepare_consumer(tmp_path)
    before = {
        rel: (tmp_path / rel).read_bytes()
        for rel in ("README.md", "AGENTS.md", "CLAUDE.md")
    }

    result = _run_gate(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "continuity-contract-gate: pass" in result.stdout
    assert {
        rel: (tmp_path / rel).read_bytes()
        for rel in ("README.md", "AGENTS.md", "CLAUDE.md")
    } == before


def test_generated_consumer_still_requires_pointer(tmp_path: Path):
    _prepare_consumer(tmp_path)
    (tmp_path / "agents" / "project" / "NEXT-SESSION-POINTER.yml").unlink()

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:pointer-missing" in result.stdout


def test_generated_consumer_still_validates_pointer_fields(tmp_path: Path):
    _prepare_consumer(tmp_path)
    _write(
        tmp_path / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        "schema: agent-runtime-next-session-pointer/v1\n",
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:pointer-field-missing:active_work" in result.stdout
    assert "continuity:pointer-field-missing:status_text" in result.stdout


def test_consumer_mode_fails_closed_without_v2_config(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    (tmp_path / "agent_runtime.yml").unlink()

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-config-missing" in result.stdout


def test_consumer_mode_fails_closed_with_malformed_config(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    _write(tmp_path / "agent_runtime.yml", "schema: agent-runtime-config/v2\nproject:\n  bad: shape\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-config-invalid" in result.stdout


def test_consumer_mode_fails_closed_without_v2_lock(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    (tmp_path / "agent_runtime.lock.json").unlink()

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-lock-missing" in result.stdout


def test_consumer_mode_fails_closed_with_malformed_lock(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    _write(tmp_path / "agent_runtime.lock.json", "{not-json\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-lock-invalid" in result.stdout


def test_consumer_mode_fails_closed_when_config_and_lock_project_mismatch(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    _write_lock(tmp_path, project="different-project")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-project-mismatch" in result.stdout


def test_consumer_mode_fails_closed_when_config_and_lock_upstream_mismatch(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    _write_lock(tmp_path, upstream_ref="different-product")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-upstream-mismatch:ref" in result.stdout


def test_consumer_mode_requires_config_and_lock_ownership_agreement(tmp_path: Path):
    _prepare_consumer(tmp_path, strict_host_docs=True)
    _write_lock(tmp_path, ownership="seed_once")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-ownership-mismatch:AGENTS.md" in result.stdout
    assert "continuity:consumer-ownership-mismatch:CLAUDE.md" in result.stdout


def test_consumer_mode_requires_managed_runtime_contract(tmp_path: Path):
    _prepare_consumer(tmp_path)
    (tmp_path / "AGENT_RUNTIME.md").unlink()

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-managed-contract-missing:AGENT_RUNTIME.md" in result.stdout


def test_consumer_mode_requires_managed_runtime_contract_digest_match(tmp_path: Path):
    _prepare_consumer(tmp_path)
    _write(tmp_path / "AGENT_RUNTIME.md", _portable_contract() + "Locally changed but semantically valid.\n")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:consumer-managed-contract-digest-mismatch:AGENT_RUNTIME.md" in result.stdout


def test_seed_once_protocol_docs_remain_strict_in_consumer_mode(tmp_path: Path):
    _prepare_consumer(tmp_path, ownership="seed_once")

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "continuity:pointer-rule-missing" in result.stdout
    assert "continuity:compound-auto-capture-rule-missing" in result.stdout
