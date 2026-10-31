from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime import security_review
from agent_runtime.security_review import CHECKS, SCHEMA, check_report, main
from agent_runtime.template_profiles import selected_paths

HEAD, BASE = "a" * 40, "b" * 40
TEMPLATE = Path(__file__).resolve().parents[1] / "src/agent_runtime/templates/project"


@pytest.fixture
def evidence(tmp_path):
    if not security_review.SAFE_OPEN_SUPPORTED:
        pytest.skip("safe descriptor-relative evidence reads unavailable on this platform")
    data = b"synthetic test evidence\n"
    (tmp_path / "test.txt").write_bytes(data)
    ref = {"path": "test.txt", "sha256": hashlib.sha256(data).hexdigest()}
    return {
        "schema_version": SCHEMA, "goal_id": "test-security-review",
        "source": {"head": HEAD, "base": BASE},
        "reviewer": "independent-instance", "contributors": ["original-author", "fix-author"],
        "environment": {"kind": "synthetic", "target": "local-handlers", "authorization_ref": "test-only"},
        "checks": [{"id": kind, "status": "passed", "evidence_refs": [ref]} for kind in sorted(CHECKS)],
        "findings": [],
    }


def result(report, tmp_path):
    return check_report(report, evidence_root=tmp_path, head=HEAD, base=BASE)


def test_scoped_evidence_can_pass_without_claiming_live_security(evidence, tmp_path):
    checked = result(evidence, tmp_path)
    assert checked["status"] == "pass"
    assert checked["assurance"] == "declared-scope-evidence-only"


@pytest.mark.parametrize("reviewer", ["original-author", "fix-author"])
def test_every_contributor_is_excluded_from_independent_review(evidence, tmp_path, reviewer):
    evidence["reviewer"] = reviewer
    assert "reviewer:self-review" in result(evidence, tmp_path)["errors"]


@pytest.mark.parametrize("reviewer", ["original-author ", " original-author", "original-author\n", "original-author\t"])
def test_noncanonical_identities_cannot_bypass_independence(evidence, tmp_path, reviewer):
    evidence["reviewer"] = reviewer
    assert result(evidence, tmp_path)["status"] == "block"


@pytest.mark.parametrize("swap", ["file-link", "directory-link", "fifo"])
def test_atomic_open_rejects_file_and_parent_swaps(evidence, tmp_path, monkeypatch, swap):
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (outside / "test.txt").write_bytes((tmp_path / "test.txt").read_bytes())
    victim = tmp_path / "test.txt"
    if swap == "directory-link":
        (tmp_path / "nested").mkdir()
        shutil.copy2(victim, tmp_path / "nested/test.txt")
        evidence["checks"][0]["evidence_refs"][0]["path"] = "nested/test.txt"
    opened = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if not swapped and dir_fd is not None and path == ("nested" if swap == "directory-link" else "test.txt"):
            swapped = True
            if swap == "directory-link":
                (tmp_path / "nested").rename(tmp_path / "old-nested")
                (tmp_path / "nested").symlink_to(outside, target_is_directory=True)
            else:
                victim.unlink()
                if swap == "file-link": victim.symlink_to(outside / "test.txt")
                else: os.mkfifo(victim)
        return opened(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", racing_open)
    assert result(evidence, tmp_path)["status"] == "block"
    assert swapped


def test_invalid_root_and_revision_types_fail_closed(evidence, tmp_path):
    loop = tmp_path / "loop"
    loop.symlink_to(loop)
    assert check_report(evidence, evidence_root=loop, head=HEAD, base=BASE)["status"] == "block"
    assert check_report(evidence, evidence_root=tmp_path, head=7, base=None)["status"] == "block"


def test_root_ancestor_swap_cannot_redirect_evidence(evidence, tmp_path, monkeypatch):
    parent = tmp_path / "parent"
    evidence_root = parent / "evidence"
    evidence_root.mkdir(parents=True)
    shutil.copy2(tmp_path / "test.txt", evidence_root / "test.txt")
    outside = tmp_path / "outside"
    (outside / "evidence").mkdir(parents=True)
    shutil.copy2(tmp_path / "test.txt", outside / "evidence/test.txt")
    opened = os.open
    swapped = False

    def racing_open(path, flags, mode=0o777, *, dir_fd=None):
        nonlocal swapped
        if not swapped and path == "parent" and dir_fd is not None:
            swapped = True
            parent.rename(tmp_path / "previous-parent")
            parent.symlink_to(outside, target_is_directory=True)
        return opened(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", racing_open)
    assert check_report(evidence, evidence_root=evidence_root, head=HEAD, base=BASE)["status"] == "block"
    assert swapped


def test_cli_rejects_fifo_report_without_blocking(evidence, tmp_path, capsys):
    report = tmp_path / "pipe"
    os.mkfifo(report)
    assert main(["--report", str(report), "--evidence-root", str(tmp_path), "--head", HEAD, "--base", BASE]) == 1
    assert "report:unavailable-or-invalid" in capsys.readouterr().out


def test_missing_or_explicit_unknown_coverage_cannot_pass(evidence, tmp_path):
    evidence["checks"].pop()
    assert result(evidence, tmp_path)["status"] == "unknown"
    evidence["checks"][0].update(status="unknown", reason="No authorized staging access")
    assert result(evidence, tmp_path)["status"] == "unknown"


def test_failed_boundary_blocks_even_without_a_finding(evidence, tmp_path):
    evidence["checks"][0]["status"] = "failed"
    assert result(evidence, tmp_path)["status"] == "block"


def test_verified_finding_requires_original_reproduction_fix_retest_and_regression(evidence, tmp_path):
    ref = evidence["checks"][0]["evidence_refs"][0]
    finding = {"id": "test-defect", "state": "verified", "reproduction": ref,
               "verified_by": evidence["reviewer"], "verified_head": HEAD,
               "fix_refs": [ref], "retest_refs": [ref], "regression_refs": [ref]}
    evidence["findings"] = [finding]
    assert result(evidence, tmp_path)["status"] == "pass"
    for field in ("reproduction", "fix_refs", "retest_refs", "regression_refs", "verified_by", "verified_head"):
        changed = copy.deepcopy(evidence)
        del changed["findings"][0][field]
        assert result(changed, tmp_path)["status"] == "block", field
    for state in ("open", "fixed"):
        finding["state"] = state
        assert result(evidence, tmp_path)["status"] == "block"


def test_source_mismatch_and_changed_evidence_block(evidence, tmp_path):
    evidence["source"]["head"] = BASE
    assert "source:revision-mismatch" in result(evidence, tmp_path)["errors"]
    evidence["source"]["head"] = HEAD
    (tmp_path / "test.txt").write_text("changed evidence")
    assert any("evidence-changed" in error for error in result(evidence, tmp_path)["errors"])


@pytest.mark.parametrize("path", ["../outside", "/etc/passwd", "https://example.test/file", "./test.txt", "test.txt/../test.txt", "a\\test.txt"])
def test_references_cannot_escape_local_evidence_root(evidence, tmp_path, path):
    evidence["checks"][0]["evidence_refs"][0]["path"] = path
    assert result(evidence, tmp_path)["status"] == "block"


def test_symlink_and_empty_evidence_are_rejected(evidence, tmp_path):
    (tmp_path / "link.txt").symlink_to(tmp_path / "test.txt")
    evidence["checks"][0]["evidence_refs"][0]["path"] = "link.txt"
    assert result(evidence, tmp_path)["status"] == "block"
    (tmp_path / "test.txt").write_bytes(b"")
    evidence["checks"][0]["evidence_refs"][0]["path"] = "test.txt"
    assert result(evidence, tmp_path)["status"] == "block"


@pytest.mark.parametrize("value", [[], {}, None, True, 7])
def test_malformed_json_field_types_block_without_crashing(evidence, tmp_path, value):
    for section, field in (("environment", "kind"), ("checks", "id"), ("checks", "status")):
        changed = copy.deepcopy(evidence)
        target = changed[section][0] if isinstance(changed[section], list) else changed[section]
        target[field] = value
        assert result(changed, tmp_path)["status"] == "block"


def test_cli_fails_closed_on_invalid_report(evidence, tmp_path, capsys):
    path = tmp_path / "review.json"
    path.write_text(json.dumps(evidence))
    args = ["--report", str(path), "--evidence-root", str(tmp_path), "--head", HEAD, "--base", BASE]
    assert main(args) == 0
    path.write_text("{bad")
    assert main(args) == 1
    assert "report:unavailable-or-invalid" in capsys.readouterr().out


def test_managed_role_is_in_core_and_context_aliases_resolve():
    paths = {p.relative_to(TEMPLATE).as_posix() for p in selected_paths(TEMPLATE, ("core",))}
    assert "agents/security_reviewer/SKILL.md" in paths
    script = TEMPLATE / "scripts/agent_context_packet.py"
    for role in ("security", "security-reviewer", "resilience"):
        run = subprocess.run([sys.executable, str(script), "--role", role, "--format", "json"], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        packet = json.loads(run.stdout)
        assert packet["role_id"] == "security-reviewer"
        assert "agents/security_reviewer/SKILL.md" in packet["required_inputs"]


def test_orchestrator_accepts_security_aliases(monkeypatch):
    script = TEMPLATE / "scripts/agent_orchestrator.py"
    spec = importlib.util.spec_from_file_location("security_review_orchestrator", script)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    for role in ("security", "security-reviewer", "resilience"):
        assert module.normalize_role(role) == "security-reviewer"


def test_generated_host_worker_and_terminal_accept_the_role(tmp_path):
    host = tmp_path / "host"
    shutil.copytree(TEMPLATE, host)
    for alias in ("security", "security-reviewer", "resilience"):
        worker = subprocess.run([sys.executable, str(host / "scripts/agent_worker.py"), "--role", alias, "--once", "--timeout", "0.05", "--poll-interval", "0.01"], capture_output=True, text=True, timeout=10)
        assert worker.returncode == 0, worker.stderr
        terminal = subprocess.run([sys.executable, str(host / "scripts/agent_terminal.py"), "preview", "--role", alias, "--task", "none", "--adapter", "manual"], capture_output=True, text=True, timeout=10)
        assert terminal.returncode == 0, terminal.stderr
        assert "security-reviewer" in terminal.stdout
