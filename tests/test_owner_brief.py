from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime.owner_brief import render_owner_brief, safe_href


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "src/agent_runtime/templates/project"


def facts() -> dict:
    return {
        "title": "검증 결과",
        "summary": "로컬 검증 통과, 실제 운영과 승인은 미확인",
        "statuses": [
            {"label": "로컬 시험", "state": "done", "detail": "8개 통과"},
            {"label": "운영 적용", "state": "unknown", "detail": "확인 근거 없음"},
            {"label": "외부 시험", "state": "not_run", "detail": "아직 실행하지 않음"},
        ],
        "next_actions": ["독립 검토 후 적용 승인 확인"],
        "limits": ["승인 상태 미확인", "직접 현금 지출 허용액 0원"],
        "evidence": [{"label": "시험 기록", "href": "evidence/results.md", "detail": "로컬 실행"}],
    }


def test_compact_is_deterministic_and_keeps_limits_and_uncertainty_visible() -> None:
    source = facts()
    original = json.dumps(source, ensure_ascii=False)
    rendered = render_owner_brief(source)
    assert rendered == render_owner_brief(source)
    assert json.dumps(source, ensure_ascii=False) == original
    header, visible = rendered.split("---", 2)[1:]
    first_layer, evidence = visible.strip().split("## 검증 근거", 1)
    assert "report_layout: compact-v1" in header and "signal: watch" in header
    assert "score:" not in header
    assert "**미확인**" in first_layer and "**미실행**" in first_layer
    assert "승인 상태 미확인" in first_layer and "직접 현금 지출 허용액 0원" in first_layer
    assert len(first_layer.rstrip()) <= 1200
    assert "evidence/results.md" in evidence


@pytest.mark.parametrize("state,expected", [("done", "pass"), ("in_progress", "watch"), ("unknown", "watch"), ("not_run", "watch"), ("blocked", "block")])
def test_signal_never_understates_source_state(state: str, expected: str) -> None:
    source = facts()
    source["statuses"] = [{"label": "시험", "state": state, "detail": "원본 상태 유지"}]
    source["signal"] = "pass"
    assert f"signal: {expected}\n" in render_owner_brief(source)
    source["signal"] = "block"
    assert "signal: block\n" in render_owner_brief(source)


@pytest.mark.parametrize("change", [
    {"title": "가" * 71}, {"summary": "가" * 141},
    {"limits": []}, {"limits": [""]}, {"limits": ["a"] * 4},
    {"statuses": []}, {"statuses": [{"label": "x", "state": "done", "detail": "d"}] * 4},
    {"next_actions": ["a"] * 3}, {"signal": "green"},
    {"score": 100}, {"score": True, "score_source": "test percentage"},
    {"score": 101, "score_source": "test percentage"},
    {"score_source": "test percentage"}, {"extra_fact": "must not silently disappear"},
])
def test_rejects_invalid_or_oversized_input_without_dropping_facts(change: dict) -> None:
    source = facts()
    source.update(change)
    with pytest.raises(ValueError):
        render_owner_brief(source)


def test_rejects_dense_first_layer_but_keeps_long_secondary_evidence() -> None:
    source = facts()
    source["limits"] = ["가" * 1100]
    with pytest.raises(ValueError, match="first_layer"):
        render_owner_brief(source)
    source["limits"] = ["운영 미확인"]
    source["evidence"][0]["detail"] = "기록" * 1000
    assert "기록" * 1000 in render_owner_brief(source)


def test_escapes_caller_markdown_html_and_link_breakouts() -> None:
    source = facts()
    source["title"] = "<img> **제목**"
    source["summary"] = "[링크](javascript:alert(1))"
    source["statuses"][0]["label"] = "*시험*"
    source["statuses"][0]["detail"] = "<script>내용</script>"
    source["limits"] = ["[승인](https://example.test) 아님"]
    source["evidence"] = [{"label": "][공격]", "href": "logs/a) [b].md", "detail": "**원문**"}]
    rendered = render_owner_brief(source)
    assert "<img>" not in rendered and "<script>" not in rendered
    assert "&lt;img&gt;" in rendered and r"\*\*제목\*\*" in rendered
    assert r"\[링크\]\(javascript\:alert\(1\)\)" in rendered
    assert "logs/a%29%20%5Bb%5D.md" in rendered
    assert r"\]\[공격\]" in rendered and r"\*\*원문\*\*" in rendered


@pytest.mark.parametrize("href", [
    "javascript:alert(1)", "JaVaScRiPt:alert(1)", "data:text/html,<svg>", "file:///tmp/a",
    "mailto:a@example.test", "https://user:secret@example.test/a", "https://user@example.test",
    "//example.test/a", "https://example.test\\@evil.test/a", "https://example.test:bad/a",
    "https:///a", "relative\npath", "relative%0apath", " https://example.test", "a\x00b",
])
def test_rejects_active_or_ambiguous_links(href: str) -> None:
    with pytest.raises(ValueError):
        safe_href(href)


@pytest.mark.parametrize("href,expected", [
    ("https://example.test/a?q=1&x=2#result", "https://example.test/a?q=1&x=2#result"),
    ("http://example.test/a(b)", "http://example.test/a%28b%29"),
    ("/tmp/local record.md", "/tmp/local%20record.md"),
    ("../results/test.md", "../results/test.md"),
])
def test_allows_encoded_http_and_local_links(href: str, expected: str) -> None:
    assert safe_href(href) == expected


@pytest.mark.parametrize("text", ["a\nb", "a\rb", "a\tb", "a\u202eb", "a\u2028b"])
def test_rejects_hidden_or_multiline_caller_text(text: str) -> None:
    source = facts()
    source["limits"] = [text]
    with pytest.raises(ValueError, match="control"):
        render_owner_brief(source)


def test_only_explicit_source_score_is_retained() -> None:
    source = facts()
    source.update(score=80, score_source="test-results: 8 of 10 checks")
    output = render_owner_brief(source)
    assert "score: 80\n" in output
    assert 'score_source: "test-results: 8 of 10 checks"' in output


TEXT_FIELDS = (
    ("title",), ("summary",), ("statuses", 0, "label"), ("statuses", 0, "detail"),
    ("next_actions", 0), ("limits", 0), ("evidence", 0, "label"),
    ("evidence", 0, "href"), ("evidence", 0, "detail"), ("score_source",),
)


def set_text_field(source: dict, path: tuple, value: str) -> None:
    target = source
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


@pytest.mark.parametrize("path", TEXT_FIELDS)
@pytest.mark.parametrize("value", [" 검토 완료", "검토 완료 ", "검토 완료\u00a0"])
def test_every_text_field_rejects_boundary_whitespace_without_trimming(path: tuple, value: str) -> None:
    source = facts()
    source.update(score=80, score_source="test-results")
    set_text_field(source, path, value)
    original = json.dumps(source, ensure_ascii=False)
    with pytest.raises(ValueError, match="leading or trailing whitespace"):
        render_owner_brief(source)
    assert json.dumps(source, ensure_ascii=False) == original


@pytest.mark.parametrize("path", TEXT_FIELDS)
def test_valid_text_field_boundaries_roundtrip_both_gates(tmp_path: Path, path: tuple) -> None:
    source = facts()
    source.update(score=80, score_source="test-results")
    set_text_field(source, path, "logs/source evidence.md" if path[-1] == "href" else "검토 완료")
    # Entity-looking caller text remains literal after generator escaping.
    source["limits"].append("원문 &#8238;미실행 &rlm;")
    report = tmp_path / "brief.md"
    report.write_text(render_owner_brief(source), encoding="utf-8")
    for script in (REPO_ROOT / "scripts/owner_doc_format_gate.py", TEMPLATE / "scripts/owner_doc_format_gate.py"):
        result = subprocess.run([sys.executable, str(script), str(report)], cwd=REPO_ROOT, capture_output=True, text=True)
        assert result.returncode == 0, result.stdout + result.stderr


def test_cli_reads_json_and_does_not_overwrite_output_on_invalid_input(tmp_path: Path) -> None:
    source = tmp_path / "facts.json"
    output = tmp_path / "brief.md"
    source.write_text(json.dumps(facts(), ensure_ascii=False), encoding="utf-8")
    command = [sys.executable, "-m", "agent_runtime.owner_brief", str(source), "-o", str(output)]
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == render_owner_brief(facts())
    source.write_text('{"title": "invalid"}', encoding="utf-8")
    before = output.read_bytes()
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
    assert result.returncode == 2 and output.read_bytes() == before


def host_scripts(tmp_path: Path) -> Path:
    host = tmp_path / "host"
    scripts = host / "scripts"
    scripts.mkdir(parents=True)
    for name in ("save_report.py", "owner_doc_format_gate.py", "check_agent_docs.py", "generate_report_views.py", "now.py"):
        shutil.copy2(TEMPLATE / "scripts" / name, scripts / name)
    return host


def save_in_host(host: Path, body: str) -> subprocess.CompletedProcess:
    source = host / "source.md"
    source.write_text(body, encoding="utf-8")
    # No installed agent_runtime source is required by the generated scripts.
    env = dict(os.environ, PYTHONPATH="")
    return subprocess.run([
        sys.executable, "scripts/save_report.py", "brief", "--title", "검증 결과",
        "--audience", "Owner", "--scale", "mini", "--body-file", str(source),
        "--now", "2026-11-02T00:00:00+00:00", "--root", str(host),
    ], cwd=host, env=env, capture_output=True, text=True)


def check_host_reports(host: Path) -> list[str]:
    probe = "import sys,json; sys.path.insert(0,'scripts'); import check_agent_docs as c; e=[]; w=[]; c.check_reports(e,w); print(json.dumps(e))"
    result = subprocess.run([sys.executable, "-c", probe], cwd=host, env=dict(os.environ, PYTHONPATH=""), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_compact_archive_roundtrip_preserves_one_header_profile_and_index(tmp_path: Path) -> None:
    host = host_scripts(tmp_path)
    source = facts()
    source.update(score=80, score_source="test-results: 8 of 10 checks")
    original = render_owner_brief(source)
    result = save_in_host(host, original)
    assert result.returncode == 0, result.stderr
    report = next((host / "agents/lead_engineer/reports").glob("BRIEF-*.md"))
    saved = report.read_text(encoding="utf-8")
    assert saved.count("\n---\n") == 1
    assert saved.count("report_layout: compact-v1") == 1
    assert "Bottom Line:" not in saved
    assert saved.split("\n---\n", 1)[1].strip() == original.split("\n---\n", 1)[1].strip()
    assert "score: 80" in saved and "score_source:" in saved
    assert 'type: "report"' in saved and f'id: "{report.stem}"' in saved
    assert f"[{report.stem}]({report.name})" in (report.parent / "INDEX.md").read_text(encoding="utf-8")
    assert check_host_reports(host) == []
    # The archive checker enforces the compact contract, not just a prefix waiver.
    report.write_text(saved.replace("report_layout: compact-v1", "report_layout: future-v2"), encoding="utf-8")
    assert any("report_layout:unknown-or-invalid" in error for error in check_host_reports(host))


def test_archive_keeps_legacy_prefix_behavior(tmp_path: Path) -> None:
    host = host_scripts(tmp_path)
    result = save_in_host(host, "완료 기록")
    assert result.returncode == 0, result.stderr
    report = next((host / "agents/lead_engineer/reports").glob("BRIEF-*.md"))
    assert "\nBottom Line: 완료 기록\n" in report.read_text(encoding="utf-8")
    assert check_host_reports(host) == []


@pytest.mark.parametrize("transform", [
    lambda text: text.replace("compact-v1", "future-v2"),
    lambda text: text.replace("report_layout: compact-v1", "report_layout:"),
    lambda text: text.replace("report_layout: compact-v1", "'report_layout': compact-v1"),
    lambda text: text.replace("report_layout: compact-v1", "report_layout: compact-v1\nreport_layout: compact-v1"),
    lambda text: text.replace("signal: watch", "signal: pass"),
    lambda text: text.replace("## 한도와 미확인", "## 숨긴 한도"),
    lambda text: text.replace("signal: watch", "signal: watch\nunrecognized: retained?"),
    lambda text: text.replace("---\n", "", 1),
    lambda text: text.replace("signal: watch", "signal: watch\n signal: pass"),
    lambda text: text.replace("signal: watch", "signal: watch\nscore: 80\n score: 100\nscore_source: tests"),
    lambda text: text.replace("signal: watch", "signal: watch\nscore: 80\nscore_source: tests\n score_source: other"),
])
def test_archive_rejects_invalid_profiles_before_writing(tmp_path: Path, transform) -> None:
    host = host_scripts(tmp_path)
    result = save_in_host(host, transform(render_owner_brief(facts())))
    assert result.returncode == 2
    assert not (host / "agents/lead_engineer/reports").exists()


@pytest.mark.parametrize("extra", [" signal: pass", " score: 100", " score_source: other"])
def test_host_archive_checker_rejects_metadata_aliases(tmp_path: Path, extra: str) -> None:
    host = host_scripts(tmp_path)
    source = facts()
    source.update(score=80, score_source="test-results")
    result = save_in_host(host, render_owner_brief(source))
    assert result.returncode == 0, result.stderr
    report = next((host / "agents/lead_engineer/reports").glob("BRIEF-*.md"))
    saved = report.read_text(encoding="utf-8")
    report.write_text(saved.replace("signal: watch", "signal: watch\n" + extra), encoding="utf-8")
    assert any("compact:metadata-noncanonical:" in error for error in check_host_reports(host))
