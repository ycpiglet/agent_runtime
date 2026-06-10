from __future__ import annotations

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
    assert "continuity:repeated-request-api-rule-missing" in result.stdout
    assert "continuity:compound-auto-capture-rule-missing" in result.stdout


def test_owner_governance_runs_continuity_contract_gate():
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert "continuity_contract_gate.py" in root_gate
    assert "continuity_contract_gate.py" in template_gate
