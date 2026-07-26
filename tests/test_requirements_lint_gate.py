from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import requirements_lint_gate as rlg


def test_check_text_flags_english_vague_terms():
    findings = rlg.check_text("The endpoint responds quickly and handles errors as needed")
    joined = " ".join(findings)
    assert "vague-term:quickly" in joined
    assert "vague-term:as needed" in joined


def test_check_text_flags_korean_vague_terms():
    findings = rlg.check_text("응답을 빠르게 처리하고 적절히 검증한다")
    joined = " ".join(findings)
    assert "vague-term:빠르게" in joined
    assert "vague-term:적절히" in joined


def test_check_text_clean_measurable_criterion_has_no_findings():
    assert rlg.check_text("WHEN a task closes, THE system SHALL set actual_hours within 5s") == []
