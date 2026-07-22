from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "response_contract_gate.py"


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


def _write_reporting_format(root: Path, body: str) -> Path:
    path = root / "src" / "agent_runtime" / "templates" / "project" / "agents" / "lead_engineer" / "REPORTING-FORMAT.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_response_contract_gate_blocks_color_status_contract_in_reporting_format(tmp_path: Path):
    _write_reporting_format(
        tmp_path,
        "\n".join(
            [
                "# 보고 형식",
                "",
                "```yaml",
                "status: G|Y|R",
                "```",
                "",
                "상태는 G/Y/R/B로 표기한다.",
            ]
        ),
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "response-contract:color-status-contract" in result.stdout


def test_response_contract_gate_requires_pre_answer_language_and_brief_rules(tmp_path: Path):
    _write_reporting_format(
        tmp_path,
        "\n".join(
            [
                "# 보고 형식",
                "",
                "- Status signal: `pass`, `watch`, `block`.",
                "- Numeric score: `0-100`.",
            ]
        ),
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "response-contract:pre-answer-check-missing" in result.stdout
    assert "response-contract:user-language-missing" in result.stdout
    assert "response-contract:owner-default-korean-missing" in result.stdout


def test_response_contract_gate_requires_owner_default_korean_not_only_user_language(tmp_path: Path):
    _write_reporting_format(
        tmp_path,
        "\n".join(
            [
                "# 보고 형식",
                "",
                "### 대화 응답 전 자체 점검",
                "",
                "1. 사용자 언어를 따른다.",
                "2. Bottom Line -> Signal -> Insight -> Decision 흐름을 지킨다.",
                "3. 상태는 pass/watch/block + score: 0-100으로 쓴다.",
            ]
        ),
    )

    result = _run_gate(tmp_path)

    assert result.returncode == 1
    assert "response-contract:owner-default-korean-missing" in result.stdout


def test_owner_governance_runs_response_contract_gate():
    root_gate = (REPO_ROOT / "scripts" / "owner_governance_gate.py").read_text(encoding="utf-8")
    template_gate = (
        REPO_ROOT / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "owner_governance_gate.py"
    ).read_text(encoding="utf-8")

    assert "response_contract_gate.py" in root_gate
    assert "response_contract_gate.py" in template_gate


def test_response_contract_gate_flags_missing_canonical_reporting_format(tmp_path: Path):
    # TASK-AR-607: the canonical live agents/lead_engineer/REPORTING-FORMAT.md must
    # exist; its absence is now a hard finding (previously silent when only the
    # template copy was present).
    result = _run_gate(tmp_path)  # empty root: no canonical reporting format
    assert result.returncode == 1
    assert "response-contract:reporting-format-missing" in result.stdout


def test_ops_reference_lists_the_six_missing_skills():
    # TASK-AR-607: OPS skill table must register the previously-missing skills.
    ops = (REPO_ROOT / "OPS-COMMAND-REFERENCE.md").read_text(encoding="utf-8")
    for skill in ("grill", "enable", "scaffold", "rsi-planning-loop", "failure-to-regression", "session-closeout"):
        assert f"`{skill}`" in ops, f"OPS reference missing skill: {skill}"
    assert "powershell" not in ops.lower()
