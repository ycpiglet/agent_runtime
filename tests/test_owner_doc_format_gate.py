from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime.owner_brief import render_owner_brief

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_owner_doc_format_gate_rejects_missing_risks_and_next_steps(tmp_path: Path) -> None:
    doc = tmp_path / "owner-report.md"
    doc.write_text(
        """---
signal: pass
score: 100
---

# Owner Report

## Bottom Line
- Summary.

## Signal
- pass

## Decision
- continue

## Action Board

| Item | State |
| --- | --- |
| A | pass |
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/owner_doc_format_gate.py", str(doc)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.returncode == 1
    assert "risk:missing" in result.stdout
    assert "next:missing" in result.stdout


GATES = (
    "scripts/owner_doc_format_gate.py",
    "src/agent_runtime/templates/project/scripts/owner_doc_format_gate.py",
)
LEGACY = """---
signal: pass
score: 100
---
# Owner Report
## Summary
Passed locally.
## Status
pass
## Action
| Item | State |
| --- | --- |
| A | pass |
## Risks
Approval unknown.
## Decision
Review next.
## Next Steps
Independent review.
"""


def compact() -> str:
    return render_owner_brief({
        "title": "검증 결과", "summary": "로컬 통과, 운영 미확인",
        "statuses": [
            {"label": "시험", "state": "done", "detail": "8개 통과"},
            {"label": "운영", "state": "unknown", "detail": "실제 운영 미확인"},
            {"label": "외부", "state": "not_run", "detail": "실행 안 함"},
        ],
        "next_actions": ["독립 검토"], "limits": ["운영 승인 필요"],
        "evidence": [{"label": "시험 기록", "href": "tests/result.md"}],
    })


def run_gate(tmp_path: Path, script: str, text: str) -> subprocess.CompletedProcess:
    path = tmp_path / "report.md"
    path.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, script, str(path)], cwd=REPO_ROOT, capture_output=True, text=True)


@pytest.mark.parametrize("script", GATES)
def test_legacy_pass_and_score_requirement_are_unchanged(tmp_path: Path, script: str) -> None:
    assert run_gate(tmp_path, script, LEGACY).returncode == 0
    result = run_gate(tmp_path, script, LEGACY.replace("score: 100\n", ""))
    assert result.returncode == 1 and "score:missing" in result.stdout


@pytest.mark.parametrize("script", GATES)
def test_compact_passes_without_score_or_legacy_outline(tmp_path: Path, script: str) -> None:
    result = run_gate(tmp_path, script, compact())
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("script", GATES)
@pytest.mark.parametrize("transform,finding", [
    (lambda text: text.replace("compact-v1", "compact-v2"), "report_layout:unknown-or-invalid"),
    (lambda text: text.replace("report_layout: compact-v1", "report_layout:"), "report_layout:unknown-or-invalid"),
    (lambda text: text.replace("report_layout: compact-v1", "'report_layout': compact-v1"), "report_layout:unknown-or-invalid"),
    (lambda text: text.replace("report_layout: compact-v1", "report_layout: compact-v1\nreport_layout: compact-v1"), "report_layout:unknown-or-invalid"),
    (lambda text: text.replace("# 검증 결과", "# " + "가" * 71), "compact:title-invalid"),
    (lambda text: text.replace(r"> **로컬 통과\, 운영 미확인**", "> **" + "가" * 141 + "**"), "compact:summary-too-long"),
    (lambda text: text.replace(r"> **로컬 통과\, 운영 미확인**", "결론 없음"), "compact:summary-invalid"),
    (lambda text: text.replace("- 운영 승인 필요", ""), "compact:limits-count"),
    (lambda text: text.replace("- 운영 승인 필요", "- " + "가" * 1200), "compact:first-layer-too-long"),
    (lambda text: text.replace("- 운영 승인 필요", "- 운영 승인 필요\n" * 4), "compact:limits-count"),
    (lambda text: text.replace("- 독립 검토", "- 독립 검토\n" * 3), "compact:next-count"),
    (lambda text: text.replace("- **완료** · 시험: 8개 통과", "- **완료** · 시험: 8개 통과\n" * 2), "compact:statuses-count"),
    (lambda text: text.replace("## 다음 행동", "## 다른 절"), "compact:sections-missing-or-out-of-order"),
    (lambda text: text.replace("**미확인**", "**확인 완료**"), "compact:state-label-invalid"),
    (lambda text: text.replace("signal: watch", "signal: pass"), "compact:signal-understates-state"),
    (lambda text: text.replace("**미확인**", "**차단**"), "compact:signal-understates-state"),
    (lambda text: text.replace("- 운영 승인 필요", "- <details>운영 승인 필요</details>"), "compact:hidden-or-dense-content"),
    (lambda text: text.replace("- 운영 승인 필요", "```\n- 운영 승인 필요\n```"), "compact:hidden-or-dense-content"),
    (lambda text: text.replace("- 운영 승인 필요", "- [hidden]: /hidden.md"), "compact:hidden-or-dense-content"),
    (lambda text: text.replace("signal: watch", "signal: watch\nscore: 80"), "score:source-required"),
    (lambda text: text.replace("signal: watch", "signal: watch\nscore: 101\nscore_source: test percentage"), "score:out-of-range"),
])
def test_compact_rejects_dense_hidden_unknown_or_incomplete_reports(tmp_path: Path, script: str, transform, finding: str) -> None:
    result = run_gate(tmp_path, script, transform(compact()))
    assert result.returncode == 1
    assert finding in result.stdout


@pytest.mark.parametrize("script", GATES)
def test_unknown_profile_cannot_fall_back_to_valid_legacy(tmp_path: Path, script: str) -> None:
    result = run_gate(tmp_path, script, LEGACY.replace("signal: pass", "report_layout: future-v2\nsignal: pass"))
    assert result.returncode == 1 and "report_layout:unknown-or-invalid" in result.stdout


def test_gate_template_bytes_stay_in_sync() -> None:
    assert (REPO_ROOT / GATES[0]).read_bytes() == (REPO_ROOT / GATES[1]).read_bytes()


@pytest.mark.parametrize("script", GATES)
def test_inline_section_names_are_not_section_boundaries(tmp_path: Path, script: str) -> None:
    # A literal section name in a short heading must not split the parser or crash.
    text = compact().replace("# 검증 결과", "# 결과: ## 검증 근거, ## 현재 상태")
    result = run_gate(tmp_path, script, text)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", GATES)
def test_generated_literal_controls_and_empty_actions_still_pass(tmp_path: Path, script: str) -> None:
    text = render_owner_brief({
        "title": "<img> **제목**", "summary": "[x](javascript:alert(1))",
        "statuses": [{"label": "x", "state": "unknown", "detail": "<script>`text`</script>"}],
        "next_actions": [], "limits": ["[승인] **미확인**"], "evidence": [],
        "score": 80, "score_source": "x",
    })
    result = run_gate(tmp_path, script, text)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", GATES)
@pytest.mark.parametrize("entity", ["&#8238;", "&#x202e;", "&rlm;", "&Tab;", "&NewLine;", "&#8232;"])
def test_decoded_control_entities_cannot_hide_first_layer_limits(tmp_path: Path, script: str, entity: str) -> None:
    result = run_gate(tmp_path, script, compact().replace("- 운영 승인 필요", f"- 운영 {entity}미실행"))
    assert result.returncode == 1 and "compact:hidden-or-dense-content" in result.stdout


@pytest.mark.parametrize("script", GATES)
@pytest.mark.parametrize("entity", ["&amp;#8238;", "&amp;rlm;"])
def test_entity_literals_are_decoded_only_once(tmp_path: Path, script: str, entity: str) -> None:
    result = run_gate(tmp_path, script, compact().replace("- 운영 승인 필요", f"- 운영 {entity}미실행"))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("script", GATES)
@pytest.mark.parametrize("metadata", [
    "signal: watch\n signal: pass",
    'signal: watch\n"signal": pass',
    "signal: watch\nsignal : pass",
    "signal: watch\nSIGNAL: pass",
    "signal: watch\nscore: 80\n score: 100\nscore_source: tests",
    "signal: watch\nscore: 80\nscore: 100\nscore_source: tests",
    "signal: watch\nscore: 80\nscore_source: tests\n score_source: other",
    "signal: watch\n report_layout: compact-v1",
])
def test_noncanonical_or_duplicate_core_metadata_is_not_a_parser_bypass(tmp_path: Path, script: str, metadata: str) -> None:
    result = run_gate(tmp_path, script, compact().replace("signal: watch", metadata))
    assert result.returncode == 1
    assert "compact:metadata-" in result.stdout or "report_layout:unknown-or-invalid" in result.stdout
