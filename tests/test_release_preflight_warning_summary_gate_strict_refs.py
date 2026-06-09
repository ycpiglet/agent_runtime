from __future__ import annotations

from src.agent_runtime import release_preflight


def test_parse_warning_summary_gate_strict_refs_trims_lines_and_skips_empty():
    raw = "refs/heads/main  \n\n  refs/heads/release/\n\t\nrefs/tags/\n"
    parsed = release_preflight._parse_warning_summary_gate_strict_refs(raw)
    assert parsed == (
        "refs/heads/main",
        "refs/heads/release/",
        "refs/tags/",
    )


def test_warning_summary_gate_strict_refs_findings_none_for_valid_refs():
    raw = "refs/heads/main\nrefs/heads/release/\nrefs/tags/"
    findings = release_preflight._warning_summary_gate_strict_refs_findings(raw)
    assert findings == ()


def test_warning_summary_gate_strict_refs_findings_empty_when_none():
    findings = release_preflight._warning_summary_gate_strict_refs_findings(None)
    assert findings == ()


def test_warning_summary_gate_strict_refs_findings_empty_list_is_blocked():
    findings = release_preflight._warning_summary_gate_strict_refs_findings("")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.kind == "missing-warning-summary-gate-strict-ref"


def test_warning_summary_gate_strict_refs_findings_invalid_refs_are_flagged():
    findings = release_preflight._warning_summary_gate_strict_refs_findings("main\nrefs/heads/main\nHEAD~1")
    assert len(findings) == 2
    kinds = {item.kind for item in findings}
    assert kinds == {
        "invalid-warning-summary-gate-strict-ref",
    }
