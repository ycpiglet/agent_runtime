"""Tests for closure_gate — require compound/review/retro for substantial work."""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import closure_gate  # noqa: E402
import stop_hook_closure_gate  # noqa: E402

NOW = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone(timedelta(hours=9)))
TODAY = "2026-06-14"


# --- pure decision logic ---

def test_decide_not_substantial_approves():
    d = closure_gate.decide(10, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=10)
    assert d["decision"] == "approve"
    assert d["reason"] == "not-substantial"


def test_decide_substantial_without_record_blocks():
    d = closure_gate.decide(200, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "block"
    assert d["missing"] == ["compound", "review", "retro"]
    assert "200" in d["message"]


@pytest.mark.parametrize("present", ["compound", "review", "retro"])
def test_decide_substantial_with_any_record_approves(present):
    records = {"compound": False, "review": False, "retro": False}
    records[present] = True
    d = closure_gate.decide(200, records, threshold=80, disabled=False, now_lines=200)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-record-present"


def test_decide_disabled_always_approves():
    d = closure_gate.decide(9999, {"compound": False, "review": False, "retro": False},
                            threshold=80, disabled=True, now_lines=9999)
    assert d["decision"] == "approve"
    assert d["reason"] == "closure-gate-disabled"


# --- closure record detection ---

def test_has_closure_record_detects_today(tmp_path):
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        f"## COMPOUND-{TODAY}-001: something\n", encoding="utf-8")
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    (reviews / f"RETRO-{TODAY}-x.md").write_text("retro", encoding="utf-8")
    (reviews / f"REVIEW-{TODAY}-y-closeout.md").write_text("review", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": True, "review": True, "retro": True}


def test_has_closure_record_ignores_other_days(tmp_path):
    (tmp_path / "agents" / "lead_engineer").mkdir(parents=True)
    (tmp_path / "agents" / "lead_engineer" / "compound_log.md").write_text(
        "## COMPOUND-2026-06-10-001: old\n", encoding="utf-8")
    (tmp_path / "reviews").mkdir()
    (tmp_path / "reviews" / "RETRO-2026-06-10-x.md").write_text("old", encoding="utf-8")
    rec = closure_gate.has_closure_record(tmp_path, now=NOW)
    assert rec == {"compound": False, "review": False, "retro": False}


# --- substantial line counting via git ---

def _git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@pytest.fixture
def git_repo(tmp_path):
    _git(tmp_path, "init")
    _git(tmp_path, "config", "user.email", "t@e.com")
    _git(tmp_path, "config", "user.name", "T")
    _git(tmp_path, "config", "commit.gpgsign", "false")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "seed.py").write_text("x = 1\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-m", "seed")
    return tmp_path


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_code_churn(git_repo):
    # a sizeable code commit
    (git_repo / "src" / "feature.py").write_text("\n".join(f"line{i} = {i}" for i in range(120)) + "\n", encoding="utf-8")
    _git(git_repo, "add", "-A")
    _git(git_repo, "commit", "-m", "feat: big")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 120


@pytest.mark.skipif(__import__("shutil").which("git") is None, reason="git not available")
def test_count_substantial_lines_counts_uncommitted(git_repo):
    (git_repo / "scripts").mkdir()
    (git_repo / "scripts" / "wip.py").write_text("\n".join(f"a{i}=1" for i in range(90)) + "\n", encoding="utf-8")
    n = closure_gate.count_substantial_lines(git_repo, now=NOW, window_hours=24)
    assert n >= 90


# --- stop hook wrapper ---

def test_stop_hook_blocks_substantial_without_record(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(closure_gate, "count_substantial_lines", lambda *a, **k: 300)
    monkeypatch.setattr(closure_gate, "has_closure_record",
                        lambda *a, **k: {"compound": False, "review": False, "retro": False})
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    import json
    out = json.loads(capsys.readouterr().out)
    assert out["decision"] == "block"
    assert out["systemMessage"]


def test_stop_hook_best_effort_on_error(monkeypatch, capsys):
    monkeypatch.setattr(closure_gate, "assess", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == {"continue": True}  # never block on gate error


def test_stop_hook_disabled_env_approves(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("AGENT_RUNTIME_CLOSURE_GATE_DISABLE", "1")
    monkeypatch.setattr(stop_hook_closure_gate.Path, "cwd", staticmethod(lambda: tmp_path))
    rc = stop_hook_closure_gate.main([])
    assert rc == 0
    assert json.loads(capsys.readouterr().out) == {"continue": True}
