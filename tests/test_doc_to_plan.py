import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

SAMPLE = """# AwesomeApp Pitch
## Vision
- Goal: help users plan faster
## Features
- Feature: drag-and-drop board
- Feature: AI task suggestions
## Constraints
- Constraint: no external data sharing
"""


def _load():
    spec = importlib.util.spec_from_file_location("doc_to_plan", ROOT / "scripts" / "doc_to_plan.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_analyze_extracts_goals_features_constraints():
    mod = _load()
    a = mod.analyze(SAMPLE)
    assert a["title"] == "AwesomeApp Pitch"
    assert any("plan faster" in g for g in a["goals"])
    assert any("drag-and-drop" in f for f in a["features"])
    assert any("external data" in c for c in a["constraints"])
    assert "Features" in a["milestones"]


def test_propose_plan_is_owner_gated_bmode():
    mod = _load()
    proposal = mod.propose_plan(mod.analyze(SAMPLE), source="pitch.md")
    assert proposal["mode"] == "B-mode"
    assert proposal["approval"] == "owner_gated"
    assert proposal["status"] == "proposed"
    assert proposal["origin_type"] == "doc_intake"
    assert proposal["taskset"]["task_set_id"].startswith("TASKSET-AR-")
    assert len(proposal["tasks"]) >= 2          # one task per feature
    assert "approval" in proposal["note"].lower() or "approv" in proposal["note"].lower()


def test_doc_to_plan_on_sample_file(tmp_path):
    mod = _load()
    f = tmp_path / "pitch.md"
    f.write_text(SAMPLE, encoding="utf-8")
    proposal = mod.doc_to_plan(f)
    assert proposal["source_document"].endswith("pitch.md")
    assert any("drag-and-drop" in t["context"] for t in proposal["tasks"])


def test_html_extraction(tmp_path):
    mod = _load()
    f = tmp_path / "deck.html"
    f.write_text("<html><body><h1>Plan</h1><p>Feature: search</p></body></html>", encoding="utf-8")
    text = mod.extract_text(f)
    assert "Plan" in text and "Feature: search" in text and "<p>" not in text


def test_unsupported_and_missing_binary_lib_are_graceful(tmp_path):
    mod = _load()
    # unknown extension -> clear ValueError, not a crash
    with pytest.raises(ValueError):
        mod.extract_text(tmp_path / "x.xyz")
    # .pdf without the optional lib -> clear RuntimeError naming the library
    pdf = tmp_path / "deck.pdf"
    pdf.write_text("x", encoding="utf-8")
    try:
        import pdfplumber  # noqa: F401
        has = True
    except ImportError:
        has = False
    if not has:
        with pytest.raises(RuntimeError):
            mod.extract_text(pdf)


def test_main_out_writes_and_is_ascii_safe(tmp_path):
    # W4b MEDIUM: the --out success message must be ASCII so it never crashes the
    # success exit on a non-UTF-8 (cp949/cp1252) Windows console.
    mod = _load()
    src = (ROOT / "scripts" / "doc_to_plan.py").read_text(encoding="utf-8")
    line = next(ln for ln in src.splitlines() if "proposal written to" in ln)
    assert line.isascii(), line
    f = tmp_path / "pitch.md"
    f.write_text(SAMPLE, encoding="utf-8")
    out = tmp_path / "proposal.json"
    assert mod.main(["--input", str(f), "--out", str(out)]) == 0
    assert out.exists()
