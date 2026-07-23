import hashlib
import json
import subprocess
import sys

from pathlib import Path

import pytest

from agent_runtime import __version__
from agent_runtime import cli as cli_module
from agent_runtime.cli import main
from agent_runtime.config import load_config
from agent_runtime.exporter import build_export_plan
from agent_runtime.host_update import _template_check_step
from agent_runtime.host_update import build_update_execution
from agent_runtime.host_update import build_update_plan
from agent_runtime.host_update import default_install_dir
from agent_runtime.host_update import run_update
from agent_runtime.inventory import classify_path
from agent_runtime.lock import build_lock_plan
from agent_runtime.lock import build_lock_record
from agent_runtime.publish_bundle import build_bundle_plan
from agent_runtime.publish_check import analyze as analyze_publish
from agent_runtime.publish_github_plan import build_github_plan
from agent_runtime.publish_github_status import CommandResult
from agent_runtime.publish_github_status import build_github_status
from agent_runtime.publish_github_execute import build_github_execution
from agent_runtime.publish_github_execute import run_github_publish
from agent_runtime.release_preflight import build_preflight_plan
from agent_runtime import release_preflight
from agent_runtime.publish_tag_smoke import build_tag_smoke_plan
from agent_runtime.sanitize import analyze as analyze_sanitize
from agent_runtime.sync import _template_files
from agent_runtime.sync import build_sync_plan
from agent_runtime.sync import run_sync

CURRENT_RELEASE_VERSION = "0.7.0"
CURRENT_RELEASE_TAG = f"v{CURRENT_RELEASE_VERSION}"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def _extract_workflow_step(workflow_text: str, step_name: str) -> str:
    lines = workflow_text.splitlines()
    start_prefix = f"      - name: {step_name}"
    next_prefix = "      - name: "
    for i, line in enumerate(lines):
        if line.startswith(start_prefix):
            start = i
            break
    else:
        raise AssertionError(f"workflow step not found: {step_name}")

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith(next_prefix):
            end = i
            break

    return "\n".join(lines[start:end])


def _write(path: Path, text: str = ""):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _digest(text: str) -> str:
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _write_host_config(root: Path, *, remote_url: str = "https://github.com/example/agent_runtime.git", ref: str = "v0.1.0", package: str = "agent_runtime"):
    _write(
        root / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                f"  package: {package}",
                f"  remote_url: {remote_url}",
                f"  ref: {ref}",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )


def _write_public_source(root: Path):
    _write(root / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(root / "README.md", "# agent_runtime\n")
    _write(
        root / ".github" / "workflows" / "test.yml",
        "\n".join(
            [
                "python -m pytest tests -q",
                "python -m agent_runtime.cli sanitize --root . --check",
                "python scripts/owner_governance_gate.py",
            ]
        )
        + "\n",
    )
    _write(root / ".codex" / "hooks.json", "{}\n")
    _write(root / ".githooks" / "pre-commit", "#!/usr/bin/env sh\npython scripts/owner_governance_gate.py\n")
    _write(
        root / "BACKLOG-BOARD.md",
        "\n".join(
            [
                "---",
                "signal: pass",
                "score: 90",
                "---",
                "# Backlog Board",
                "",
                "## Bottom Line",
                "Fixture owner board is ready.",
                "",
                "## Signal",
                "",
                "| Item | Status |",
                "|------|--------|",
                "| fixture | pass |",
                "",
                "## Action Board",
                "No action needed.",
                "",
                "## Risks / Blockers",
                "None.",
                "",
                "## Decision",
                "Use this fixture as the owner doc.",
                "",
                "## Next Steps",
                "Continue.",
            ]
        )
        + "\n",
    )
    _write(root / "owner-docs.yml", "owner_docs:\n  - BACKLOG-BOARD.md\n")
    _write(root / "schemas" / "state-machines.schema.json", '{"type":"object"}\n')
    state_machines = "\n".join(
        [
            "states: [pass, watch, block]",
            "machines:",
            "  - id: health_signal",
            "  - id: cycle",
            "  - id: task",
            "  - id: task_claim",
            "  - id: agent_job",
            "  - id: gate",
            "  - id: review",
            "  - id: release",
            "  - id: owner_decision",
            "  - id: hook_enforcement",
            "  - id: ci",
            "  - id: document",
        ]
    ) + "\n"
    _write(root / "scripts" / "owner_governance_gate.py", "raise SystemExit(0)\n")
    _write(root / "scripts" / "owner_doc_format_gate.py", "raise SystemExit(0)\n")
    _write(root / "scripts" / "continuity_contract_gate.py", "raise SystemExit(0)\n")
    _write(root / "scripts" / "response_contract_gate.py", "raise SystemExit(0)\n")
    _write(root / "scripts" / "state_machine_gate.py", "raise SystemExit(0)\n")
    _write(root / "scripts" / "task_claim_dispatcher.py", "raise SystemExit(0)\n")
    _write(
        root / "scripts" / "stop_hook_owner_governance.py",
        "import json\nprint(json.dumps({'decision':'approve','reason':'owner governance gate passed','systemMessage':'findings=0'}))\n",
    )
    _write(
        root / "scripts" / "stop_hook_owner_governance.cmd",
        "@echo off\npython \"%~dp0stop_hook_owner_governance.py\"\n",
    )
    _write(root / "src" / "agent_runtime" / "__init__.py", "")
    _write(root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(root / "src" / "agent_runtime" / "templates" / "project" / ".codex" / "hooks.json", "{}\n")
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "agents" / "project" / "NEXT-SESSION-POINTER.yml",
        "schema: agent-runtime-next-session-pointer/v1\nupdated_at: 2026-01-01T00:00:00+09:00\ncurrent_state: {}\nactive_work: {}\nresume: {}\nroles: {}\npointers: {}\nrules: {}\nverification: {}\n",
    )
    _write(root / "src" / "agent_runtime" / "templates" / "project" / "agents" / "project" / "STATE-MACHINES.yml", state_machines)
    _write(root / "src" / "agent_runtime" / "templates" / "project" / "schemas" / "state-machines.schema.json", '{"type":"object"}\n')
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "task_claim_dispatcher.py",
        "raise SystemExit(0)\n",
    )
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "response_contract_gate.py",
        "raise SystemExit(0)\n",
    )
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "continuity_contract_gate.py",
        "raise SystemExit(0)\n",
    )
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "stop_hook_owner_governance.py",
        "import json\nprint(json.dumps({'decision':'approve','reason':'owner governance gate passed','systemMessage':'findings=0'}))\n",
    )
    _write(
        root / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "stop_hook_owner_governance.cmd",
        "@echo off\npython \"%~dp0stop_hook_owner_governance.py\"\n",
    )
    _write(root / ".gitignore", "/templates/\n")


def test_inventory_keeps_product_and_host_state_out_of_core():
    assert classify_path("scripts/agent_worker.py")[0] == "core"
    assert classify_path("public/index.html")[0] == "product"
    assert classify_path("supabase/schema.sql")[0] == "product"
    assert classify_path("agents/lead_engineer/tasks/TASK-001-demo.md")[0] == "host-state"
    assert classify_path("agent_runtime.yml")[0] == "host-state"
    assert classify_path("agent_runtime.lock.json")[0] == "host-state"


def test_sync_check_reads_host_config_without_writing(tmp_path, capsys):
    config = tmp_path / "agent_runtime.yml"
    config.write_text(
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
        encoding="utf-8",
    )

    assert main(["sync", "--root", str(tmp_path), "--check"]) == 0
    out = capsys.readouterr().out

    assert "project=demo" in out
    assert "allow_silent_overwrite=false" in out
    assert config.read_text(encoding="utf-8").startswith("project: demo")


def test_sync_diff_replaces_unencodable_stdout_characters(tmp_path, monkeypatch):
    class Cp949Stdout:
        encoding = "cp949"

        def __init__(self):
            self.output = ""

        def write(self, text):
            safe = text.encode(self.encoding, errors="replace").decode(self.encoding)
            self.output += safe
            if safe != text:
                raise UnicodeEncodeError(self.encoding, text, 0, len(text), "cannot encode")
            return len(text)

        def flush(self):
            return None

    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write_host_config(host)
    _write(templates / "docs" / "NOTE.md", "new — template\n")
    _write(host / "docs" / "NOTE.md", "old host\n")
    stdout = Cp949Stdout()
    monkeypatch.setattr(sys, "stdout", stdout)

    assert run_sync(host, "diff", template_root=templates) == 0

    assert "new ? template" in stdout.output


def test_build_sync_plan_rejects_config_object_as_template_root(tmp_path):
    _write_host_config(tmp_path)
    config = load_config(tmp_path)

    with pytest.raises(TypeError, match="template_root must be path-like"):
        build_sync_plan(tmp_path, template_root=config)


def test_config_reads_upstream_dependency_contract(tmp_path):
    config = tmp_path / "agent_runtime.yml"
    config.write_text(
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    loaded = load_config(tmp_path)

    assert loaded.upstream_package == "agent_runtime"
    assert loaded.upstream_remote_url == "https://github.com/example/agent_runtime.git"
    assert loaded.upstream_ref == "v0.1.0"


def test_config_reads_unmanaged_sync_paths(tmp_path):
    _write(
        tmp_path / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "  unmanaged:",
                "    - AGENTS.md",
                "    - scripts/check_agent_docs.py",
            ]
        )
        + "\n",
    )

    loaded = load_config(tmp_path)

    assert loaded.unmanaged_paths == ("AGENTS.md", "scripts/check_agent_docs.py")


def test_update_plan_uses_host_upstream_for_install_and_sync_commands(tmp_path):
    _write(
        tmp_path / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    install_dir = tmp_path / ".agent_runtime" / "vendor"

    plan = build_update_plan(tmp_path, install_dir)
    command_text = "\n".join(plan.commands)

    assert plan.findings == ()
    assert plan.install_spec == "git+https://github.com/example/agent_runtime.git@v0.1.0"
    assert "python -m pip install --target" in command_text
    assert "--no-build-isolation" not in command_text
    assert str(install_dir.resolve()) in command_text
    assert "sys.path.insert(0," in command_text
    assert "from agent_runtime.cli import main" in command_text
    assert "template_sentinel" in command_text
    assert "raise SystemExit(0 if sentinel else 1)" in command_text
    assert "sync" in command_text
    assert "--check" in command_text
    assert "--diff" in command_text
    assert "--apply" in command_text
    assert "lock" in command_text
    assert "--write" in command_text


def test_update_plan_cli_defaults_install_dir_to_host_tmp(tmp_path, capsys):
    _write_host_config(tmp_path)

    assert main(["update-plan", "--root", str(tmp_path), "--check"]) == 0
    out = capsys.readouterr().out

    assert f"install_dir={default_install_dir(tmp_path).resolve()}" in out


def test_update_cli_defaults_install_dir_to_host_tmp(tmp_path, monkeypatch):
    captured = {}

    def fake_run_update(root, install_dir, *, mode):
        captured["root"] = root
        captured["install_dir"] = install_dir
        captured["mode"] = mode
        return 0

    monkeypatch.setattr(cli_module.host_update, "run_update", fake_run_update)

    assert main(["update", "--root", str(tmp_path), "--check"]) == 0

    assert captured == {
        "root": tmp_path,
        "install_dir": default_install_dir(tmp_path),
        "mode": "check",
    }


def test_update_execution_check_runs_install_and_installed_sync_check(tmp_path):
    _write(
        tmp_path / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )

    execution = build_update_execution(tmp_path, tmp_path / ".agent_runtime" / "vendor", mode="check")

    assert [step.name for step in execution.steps] == ["install-upstream", "verify-templates", "sync-check"]
    assert "git+https://github.com/example/agent_runtime.git@v0.1.0" in execution.steps[0].args
    assert "--no-build-isolation" not in execution.steps[0].args
    assert "sync" in execution.steps[2].args[-1]
    assert "--check" in execution.steps[2].args[-1]


def test_update_template_sentinel_fails_when_installed_templates_are_missing(tmp_path):
    install_dir = tmp_path / "install"
    _write(
        install_dir / "agent_runtime" / "sync.py",
        "from pathlib import Path\n"
        "def default_template_root():\n"
        "    return Path(__file__).resolve().parent / 'templates' / 'project'\n",
    )
    _write(install_dir / "agent_runtime" / "__init__.py", "")

    step = _template_check_step(install_dir)
    result = subprocess.run(step.args, check=False, capture_output=True, text=True)

    assert result.returncode == 1
    assert "template_sentinel=False" in result.stdout


def test_update_template_sentinel_passes_when_installed_templates_exist(tmp_path):
    install_dir = tmp_path / "install"
    _write(
        install_dir / "agent_runtime" / "sync.py",
        "from pathlib import Path\n"
        "def default_template_root():\n"
        "    return Path(__file__).resolve().parent / 'templates' / 'project'\n",
    )
    _write(install_dir / "agent_runtime" / "__init__.py", "")
    _write(install_dir / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")

    step = _template_check_step(install_dir)
    result = subprocess.run(step.args, check=False, capture_output=True, text=True)

    assert result.returncode == 0
    assert "template_sentinel=True" in result.stdout


def test_update_execution_apply_runs_sync_apply_and_lock_write(tmp_path):
    _write(
        tmp_path / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )

    execution = build_update_execution(tmp_path, tmp_path / ".agent_runtime" / "vendor", mode="apply")

    assert [step.name for step in execution.steps] == [
        "install-upstream",
        "verify-templates",
        "sync-check",
        "sync-diff",
        "sync-apply",
        "sync-check",
        "lock-write",
    ]
    assert "--apply" in execution.steps[4].args[-1]
    assert "--check" in execution.steps[5].args[-1]
    assert "lock" in execution.steps[6].args[-1]
    assert "--write" in execution.steps[6].args[-1]


def test_update_execution_blocks_unsafe_install_dir(tmp_path):
    _write_host_config(tmp_path)

    root_execution = build_update_execution(tmp_path, tmp_path, mode="check")
    scripts_execution = build_update_execution(tmp_path, tmp_path / "scripts" / "vendor", mode="check")

    assert "unsafe-install-dir" in {finding.kind for finding in root_execution.findings}
    assert "unsafe-install-dir" in {finding.kind for finding in scripts_execution.findings}


def test_update_execution_blocks_non_empty_install_dir(tmp_path):
    _write_host_config(tmp_path)
    install_dir = tmp_path / ".tmp" / "agent_runtime-upstream"
    _write(install_dir / "old.txt", "stale\n")

    execution = build_update_execution(tmp_path, install_dir, mode="check")

    assert "install-dir-not-empty" in {finding.kind for finding in execution.findings}


def test_update_execution_requires_trusted_upstream_contract(tmp_path):
    _write_host_config(tmp_path, remote_url="https://gitlab.com/example/agent_runtime.git", ref="main", package="other")

    execution = build_update_execution(tmp_path, tmp_path / ".tmp" / "agent_runtime-upstream", mode="check")
    kinds = {finding.kind for finding in execution.findings}

    assert "unexpected-upstream-package" in kinds
    assert "non-github-upstream-remote-url" in kinds
    assert "mutable-upstream-ref" in kinds


def test_update_plan_check_uses_same_trust_findings_as_execution(tmp_path):
    _write_host_config(tmp_path, remote_url="https://gitlab.com/example/agent_runtime.git", ref="main", package="other")

    plan = build_update_plan(tmp_path, tmp_path)
    kinds = {finding.kind for finding in plan.findings}

    assert "unexpected-upstream-package" in kinds
    assert "non-github-upstream-remote-url" in kinds
    assert "mutable-upstream-ref" in kinds
    assert "unsafe-install-dir" in kinds
    assert main(["update-plan", "--root", str(tmp_path), "--install-dir", str(tmp_path), "--check"]) == 1


def test_update_plan_rejects_v_prefixed_non_semver_branch_refs(tmp_path):
    _write_host_config(tmp_path, ref="v-main")

    plan = build_update_plan(tmp_path, tmp_path / ".tmp" / "agent_runtime-upstream")

    assert "mutable-upstream-ref" in {finding.kind for finding in plan.findings}


def test_run_update_stops_on_first_failed_step(tmp_path, capsys):
    _write(
        tmp_path / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 7 if step.name == "verify-templates" else 0

    assert run_update(tmp_path, tmp_path / ".agent_runtime" / "vendor", mode="apply", runner=fake_runner) == 7

    out = capsys.readouterr().out
    assert calls == ["install-upstream", "verify-templates"]
    assert "failed_step=verify-templates" in out
    assert "sync-apply" not in calls


def test_lock_plan_tracks_host_upstream_version_and_template_digest(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    _write(templates / "scripts" / "agent_worker.py", "print('worker')\n")
    _write(templates / "docs" / "agent_runtime" / "README.md", "# agent_runtime\n")

    plan = build_lock_plan(host, template_root=templates)

    assert {finding.kind for finding in plan.findings} == {"missing-lock-file"}
    assert plan.record["project"] == "demo"
    assert plan.record["upstream"]["package"] == "agent_runtime"
    assert plan.record["upstream"]["remote_url"] == "https://github.com/example/agent_runtime.git"
    assert plan.record["upstream"]["ref"] == "v0.1.0"
    assert plan.record["installed"]["package_version"] == CURRENT_RELEASE_VERSION
    assert plan.record["installed"]["template_files"] == 2
    assert plan.record["installed"]["template_digest"].startswith("sha256:")
    assert plan.record["installed"]["managed_files"]["scripts/agent_worker.py"].startswith("sha256:")


def test_lock_plan_ignores_installed_template_pycache(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    _write(templates / "scripts" / "agent_worker.py", "print('worker')\n")
    (templates / "scripts" / "__pycache__").mkdir(parents=True)
    (templates / "scripts" / "__pycache__" / "agent_worker.cpython-310.pyc").write_bytes(b"compiled")

    plan = build_lock_plan(host, template_root=templates)

    assert plan.record["installed"]["template_files"] == 1


def test_lock_digest_is_stable_across_template_line_endings(tmp_path):
    host = tmp_path / "host"
    lf_templates = tmp_path / "lf"
    crlf_templates = tmp_path / "crlf"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    (lf_templates / "scripts").mkdir(parents=True)
    (crlf_templates / "scripts").mkdir(parents=True)
    (lf_templates / "scripts" / "agent_worker.py").write_bytes(b"line1\nline2\n")
    (crlf_templates / "scripts" / "agent_worker.py").write_bytes(b"line1\r\nline2\r\n")

    lf_plan = build_lock_plan(host, template_root=lf_templates)
    crlf_plan = build_lock_plan(host, template_root=crlf_templates)

    assert lf_plan.record["installed"]["template_digest"] == crlf_plan.record["installed"]["template_digest"]


def test_lock_write_then_check_is_current(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    _write(templates / "scripts" / "agent_worker.py", "print('worker')\n")

    assert main(["lock", "--root", str(host), "--template-root", str(templates), "--write"]) == 0
    assert main(["lock", "--root", str(host), "--template-root", str(templates), "--check"]) == 0


def test_sync_ignores_installed_template_pycache(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
    )
    _write(templates / "scripts" / "agent_worker.py", "print('worker')\n")
    (templates / "scripts" / "__pycache__").mkdir(parents=True)
    (templates / "scripts" / "__pycache__" / "agent_worker.cpython-310.pyc").write_bytes(b"compiled")

    plan = build_sync_plan(host, template_root=templates)

    assert [update.path for update in plan.updates] == ["scripts/agent_worker.py"]


def test_sync_updates_managed_file_when_host_matches_lock(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    old = "print('old')\n"
    new = "print('new')\n"
    _write(
        host / "agent_runtime.yml",
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
    )
    _write(host / "scripts" / "agent_worker.py", old)
    _write(templates / "scripts" / "agent_worker.py", new)
    _write(
        host / "agent_runtime.lock.json",
        json.dumps(
            {
                "schema": "agent-runtime-lock/v1",
                "project": "demo",
                "upstream": {"package": "agent_runtime", "remote_url": "", "ref": ""},
                "installed": {
                    "package_version": "0.1.0",
                    "template_digest": "sha256:old",
                    "template_files": 1,
                    "managed_files": {"scripts/agent_worker.py": _digest(old)},
                },
            }
        )
        + "\n",
    )

    plan = build_sync_plan(host, template_root=templates)

    assert [(update.action, update.path) for update in plan.updates] == [("update", "scripts/agent_worker.py")]
    assert plan.conflicts == ()
    assert main(["sync", "--root", str(host), "--template-root", str(templates), "--apply"]) == 0
    assert (host / "scripts" / "agent_worker.py").read_text(encoding="utf-8") == new


def test_sync_conflicts_when_host_modified_from_locked_managed_file(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    old = "print('old')\n"
    modified = "print('host edit')\n"
    new = "print('new')\n"
    _write(
        host / "agent_runtime.yml",
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
    )
    _write(host / "scripts" / "agent_worker.py", modified)
    _write(templates / "scripts" / "agent_worker.py", new)
    _write(
        host / "agent_runtime.lock.json",
        json.dumps(
            {
                "schema": "agent-runtime-lock/v1",
                "project": "demo",
                "upstream": {"package": "agent_runtime", "remote_url": "", "ref": ""},
                "installed": {
                    "package_version": "0.1.0",
                    "template_digest": "sha256:old",
                    "template_files": 1,
                    "managed_files": {"scripts/agent_worker.py": _digest(old)},
                },
            }
        )
        + "\n",
    )

    plan = build_sync_plan(host, template_root=templates)

    assert plan.updates == ()
    assert [(conflict.action, conflict.path) for conflict in plan.conflicts] == [("conflict", "scripts/agent_worker.py")]


def test_sync_ignores_configured_unmanaged_paths(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "  unmanaged:",
                "    - AGENTS.md",
            ]
        )
        + "\n",
    )
    _write(host / "AGENTS.md", "host policy\n")
    _write(templates / "AGENTS.md", "generic template\n")

    plan = build_sync_plan(host, template_root=templates)

    assert plan.updates == ()
    assert plan.conflicts == ()


def test_lock_record_excludes_configured_unmanaged_paths(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
                "  unmanaged:",
                "    - AGENTS.md",
            ]
        )
        + "\n",
    )
    _write(templates / "AGENTS.md", "generic template\n")
    _write(templates / "scripts" / "agent_loop.py", "print('loop')\n")

    record = build_lock_record(host, template_root=templates)

    assert "AGENTS.md" not in record["installed"]["managed_files"]
    assert "scripts/agent_loop.py" in record["installed"]["managed_files"]


def test_sync_check_fails_when_conflicts_exist(tmp_path):
    host = tmp_path / "host"
    templates = tmp_path / "templates"
    _write(
        host / "agent_runtime.yml",
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
    )
    _write(host / "scripts" / "agent_worker.py", "print('host edit')\n")
    _write(templates / "scripts" / "agent_worker.py", "print('upstream')\n")

    assert main(["sync", "--root", str(host), "--template-root", str(templates), "--check"]) == 1


def test_template_files_use_stable_posix_relative_order(tmp_path):
    _write(tmp_path / "AGENT_RUNTIME.md", "runtime\n")
    _write(tmp_path / "AGENTS.md", "agents\n")
    _write(tmp_path / "agents" / "alpha.md", "alpha\n")

    files = [path.relative_to(tmp_path).as_posix() for path in _template_files(tmp_path)]

    assert files == ["AGENT_RUNTIME.md", "AGENTS.md", "agents/alpha.md"]


def test_update_plan_requires_upstream_contract(tmp_path):
    _write(
        tmp_path / "agent_runtime.yml",
        "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n",
    )

    plan = build_update_plan(tmp_path, tmp_path / ".agent_runtime" / "vendor")
    kinds = {finding.kind for finding in plan.findings}

    assert "missing-upstream-remote-url" in kinds
    assert "missing-upstream-ref" in kinds


def test_update_plan_blocks_placeholder_upstream_remote(tmp_path):
    _write_host_config(tmp_path, remote_url="https://github.com/OWNER/agent_runtime.git")

    plan = build_update_plan(tmp_path, tmp_path / ".tmp" / "agent_runtime-upstream")

    assert "placeholder-remote-url" in {finding.kind for finding in plan.findings}


def test_release_preflight_aggregates_public_and_host_readiness(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write(
        host / "agent_runtime.yml",
        "\n".join(
            [
                "project: demo",
                "upstream:",
                "  package: agent_runtime",
                "  remote_url: https://github.com/example/agent_runtime.git",
                "  ref: v0.1.0",
                "sync:",
                "  mode: check-diff-apply",
                "  allow_silent_overwrite: false",
            ]
        )
        + "\n",
    )
    assert main(
        [
            "lock",
            "--root",
            str(host),
            "--template-root",
            str(source / "src" / "agent_runtime" / "templates" / "project"),
            "--write",
        ]
    ) == 0

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )

    checks = {check.name: check for check in plan.checks}

    assert plan.findings_count == 0
    assert checks["host-upstream-match"].status == "ok"
    assert checks["sanitize"].status == "ok"
    assert checks["publish-check"].status == "ok"
    assert checks["publish-bundle"].detail == "files=28"
    assert checks["local-tag-smoke-plan"].status == "ok"
    assert checks["github-publish-plan"].status == "ok"
    assert checks["host-update-plan"].status == "ok"
    assert checks["host-update-command"].status == "ok"
    assert checks["host-update-command"].detail == "steps=3"
    assert checks["host-lock"].status == "ok"


def test_release_preflight_resolves_relative_work_dirs_under_source_root(tmp_path, monkeypatch):
    checkout = tmp_path / "checkout"
    source = checkout / ".tmp" / "public-source"
    host = source / "tests" / "fixtures" / "host"
    _write_public_source(source)
    _write_host_config(host, remote_url="https://github.com/example/agent_runtime.git")
    assert main(
        [
            "lock",
            "--root",
            str(host),
            "--template-root",
            str(source / "src" / "agent_runtime" / "templates" / "project"),
            "--write",
        ]
    ) == 0
    monkeypatch.chdir(checkout)

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=Path(".tmp/public-source"),
        tag_repo_dir=Path(".tmp/tag-repo"),
        tag_install_dir=Path(".tmp/tag-install"),
        github_install_dir=Path(".tmp/github-install"),
        host_install_dir=Path(".tmp/agent_runtime-upstream"),
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )
    checks = {check.name: check for check in plan.checks}

    assert plan.findings_count == 0
    assert checks["publish-bundle"].status == "ok"
    assert checks["host-lock"].status == "ok"
    expected_tag_repo_uri = (source / ".tmp" / "tag-repo").resolve().as_uri()
    assert checks["local-tag-smoke-plan"].detail == f"install_spec=git+{expected_tag_repo_uri}@v0.1.0"


def test_release_preflight_blocks_host_sync_conflicts(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "print('upstream')\n")
    _write_host_config(host, remote_url="https://github.com/example/agent_runtime.git")
    _write(host / "scripts" / "agent_worker.py", "print('upstream')\n")
    assert main(
        [
            "lock",
            "--root",
            str(host),
            "--template-root",
            str(source / "src" / "agent_runtime" / "templates" / "project"),
            "--write",
        ]
    ) == 0
    _write(host / "scripts" / "agent_worker.py", "print('host edit')\n")

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )
    checks = {check.name: check for check in plan.checks}

    assert checks["host-lock"].status == "ok"
    assert checks["host-sync-check"].status == "blocked"
    assert "host-sync-conflict" in {finding.kind for finding in checks["host-sync-check"].findings}


def test_release_preflight_blocks_host_upstream_mismatch(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write_host_config(host, remote_url="https://github.com/example/other.git", ref="v0.2.0")

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )
    checks = {check.name: check for check in plan.checks}
    kinds = {finding.kind for finding in checks["host-upstream-match"].findings}

    assert checks["host-upstream-match"].status == "blocked"
    assert "upstream-remote-url-mismatch" in kinds
    assert "upstream-ref-mismatch" in kinds


def test_release_preflight_reports_executable_host_update_findings(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write_host_config(host)
    _write(host / ".tmp" / "host-install" / "old.txt", "stale\n")

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )
    checks = {check.name: check for check in plan.checks}

    assert checks["host-update-plan"].status == "blocked"
    assert "install-dir-not-empty" in {finding.kind for finding in checks["host-update-plan"].findings}
    assert checks["host-update-command"].status == "skipped"


def test_release_preflight_reports_missing_host_upstream(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write(host / "agent_runtime.yml", "project: demo\nsync:\n  mode: check-diff-apply\n  allow_silent_overwrite: false\n")

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
    )

    checks = {check.name: check for check in plan.checks}

    assert plan.findings_count == 2
    assert checks["host-upstream-match"].status == "skipped"
    assert checks["host-update-plan"].status == "blocked"
    assert checks["host-update-command"].status == "skipped"
    assert checks["host-lock"].status == "skipped"


def test_release_preflight_reports_warning_summary_gate_strict_refs_in_render_and_checks(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write_host_config(host)
    strict_refs = "refs/heads/main\nrefs/tags/\n"
    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
        warning_summary_gate_strict_refs=strict_refs,
    )

    checks = {check.name: check for check in plan.checks}

    assert checks["warning-summary-gate-strict-refs"].status == "ok"
    assert checks["warning-summary-gate-strict-refs"].detail == "refs=refs/heads/main;refs/tags/"

    rendered = release_preflight.render(plan)
    assert "| warning-summary-gate-strict-refs | ok | refs=refs/heads/main;refs/tags/ | 0 |" in rendered


def test_release_preflight_blocks_invalid_warning_summary_gate_strict_refs(tmp_path):
    source = tmp_path / "source"
    host = tmp_path / "host"
    _write_public_source(source)
    _write_host_config(host)
    strict_refs = "main\nrefs/heads/main\n"

    plan = build_preflight_plan(
        source_root=source,
        host_root=host,
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=source / ".tmp" / "github-install",
        host_install_dir=host / ".tmp" / "host-install",
        remote_url="https://github.com/example/agent_runtime.git",
        tag="v0.1.0",
        warning_summary_gate_strict_refs=strict_refs,
    )

    checks = {check.name: check for check in plan.checks}
    check = checks["warning-summary-gate-strict-refs"]
    assert check.status == "blocked"
    assert check.findings[0].kind == "invalid-warning-summary-gate-strict-ref"

    rendered = release_preflight.render(plan)
    assert "| warning-summary-gate-strict-refs | blocked | refs=main;refs/heads/main | 1 |" in rendered


def test_sanitize_blocks_forbidden_public_content(tmp_path):
    local_path = "C:" + "\\Us" + "ers\\someone\\private"
    _write(tmp_path / ".env")
    _write(tmp_path / "public" / "index.html")
    _write(tmp_path / "README.md", local_path + "\n")

    findings = analyze_sanitize(tmp_path)
    kinds = {(finding.path, finding.kind) for finding in findings}

    assert (".env", "forbidden-path") in kinds
    assert ("public/index.html", "forbidden-path") in kinds
    assert ("README.md", "absolute-local-path") in kinds


def test_sanitize_allows_vendored_woff2_font_binaries(tmp_path):
    # TASK-AR-589: self-hosted Geist woff2 binaries are a legitimate vendored
    # asset (like .png/.ico). They must not be flagged "binary-or-undecodable",
    # otherwise the sanitize gate forces the 404 workaround instead of fonts.
    woff2 = tmp_path / "src" / "agent_runtime" / "vendor" / "geist" / "1.7.2" / "fonts" / "geist-sans" / "Geist-Variable.woff2"
    woff2.parent.mkdir(parents=True, exist_ok=True)
    woff2.write_bytes(b"wOF2" + b"\x00\x01\x02\x03not utf-8 decodable \xff\xfe")

    findings = analyze_sanitize(tmp_path)
    kinds = {(finding.path, finding.kind) for finding in findings}

    rel = woff2.relative_to(tmp_path).as_posix()
    assert (rel, "binary-or-undecodable") not in kinds


def test_sanitize_blocks_forward_slash_windows_absolute_paths(tmp_path):
    local_path = "C:" + "/Us" + "ers/someone/private"
    _write(tmp_path / "README.md", f"Local path: {local_path}\n")

    findings = analyze_sanitize(tmp_path)
    kinds = {(finding.path, finding.kind) for finding in findings}

    assert ("README.md", "absolute-local-path") in kinds


def test_sanitize_ignores_generated_local_work_dirs(tmp_path):
    slash_path = "C:" + "/Us" + "ers/someone/private"
    backslash_path = "C:" + "\\Us" + "ers\\someone\\private"
    _write(tmp_path / "README.md", "# public package\n")
    _write(tmp_path / ".tmp" / "pip-install" / "direct_url.json", f'{{"url":"file:///{slash_path}"}}\n')
    _write(tmp_path / "build" / "lib" / "README.md", backslash_path + "\n")
    _write(tmp_path / "dist" / "metadata.txt", backslash_path + "\n")
    _write(tmp_path / ".pytest_cache" / "README.md", backslash_path + "\n")

    findings = analyze_sanitize(tmp_path)

    assert findings == []


def test_sanitize_ignores_review_artifacts(tmp_path):
    local_path = "C" + ":/Us" + "ers/you/private"
    _write(tmp_path / "reviews" / "REVIEW-999.md", f"Local path: {local_path}\n")

    findings = analyze_sanitize(tmp_path)
    assert findings == []


def test_sanitize_ignores_top_level_host_agents_artifacts(tmp_path):
    local_path = "C" + ":/Us" + "ers/you/private"
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-001.md", f"Local path: {local_path}\n")

    findings = analyze_sanitize(tmp_path)
    assert findings == []


def test_sanitize_blocks_forbidden_paths_nested_under_project_templates(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    nested_task = source / "src" / "agent_runtime" / "templates" / "project" / "agents" / "lead_engineer" / "tasks" / "TASK-private.md"
    _write(nested_task, "# private task\n")
    allowed_unit_template = (
        source
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "agents"
        / "lead_engineer"
        / "tasks"
        / "units"
        / "README.md"
    )
    _write(allowed_unit_template, "# Worker-ready unit template\n")

    sanitize_findings = {(finding.path, finding.kind) for finding in analyze_sanitize(source)}
    github_plan = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert (nested_task.relative_to(source).as_posix(), "forbidden-template-path") in sanitize_findings
    assert (allowed_unit_template.relative_to(source).as_posix(), "forbidden-template-path") not in sanitize_findings
    assert "sanitize:forbidden-template-path" in {finding.kind for finding in github_plan.findings}


def test_sanitize_blocks_host_history_references_in_project_template_docs(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    template_doc = source / "src" / "agent_runtime" / "templates" / "project" / "AGENTS.md"
    _write(template_doc, "Reusable rules.\nHistorical fix: TASK-027 for Supabase RLS.\n")

    sanitize_findings = {(finding.path, finding.kind) for finding in analyze_sanitize(source)}
    github_plan = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert (template_doc.relative_to(source).as_posix(), "host-history-reference") in sanitize_findings
    assert "sanitize:host-history-reference" in {finding.kind for finding in github_plan.findings}


def test_sanitize_blocks_host_history_references_in_nested_project_templates(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    template_doc = source / "src" / "agent_runtime" / "templates" / "project" / "agents" / "backend_engineer" / "SKILL.md"
    _write(template_doc, "Reusable role.\nDo not carry TASK-027 Supabase RLS history.\n")

    sanitize_findings = {(finding.path, finding.kind) for finding in analyze_sanitize(source)}

    assert (template_doc.relative_to(source).as_posix(), "host-history-reference") in sanitize_findings


def test_sanitize_blocks_host_specific_history_in_project_template_scripts(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    template_script = source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "test_history.py"
    _write(
        template_script,
        "\n".join(
            [
                'assert "agents/lead_engineer/tasks/TASK-250-agent_runtime-github-sync.md"',
                'assert "agents/lead_engineer/CYCLE-091.md"',
                'assert "docs/superpowers/plans/2026-06-07-agent_runtime-github-sync.md"',
                'example = "ANTHROPIC_API_KEY_KETI"',
            ]
        )
        + "\n",
    )

    sanitize_findings = {(finding.path, finding.kind) for finding in analyze_sanitize(source)}

    assert (template_script.relative_to(source).as_posix(), "host-history-reference") in sanitize_findings


def test_export_plan_selects_only_public_core_candidates(tmp_path):
    package_root = tmp_path / "packages" / "agent_runtime"
    _write(package_root / "templates" / "project" / ".gitkeep")
    _write(tmp_path / "scripts" / "agent_worker.py", "print('worker')\n")
    _write(tmp_path / "AGENTS.md", "# reusable operating rules\n")
    _write(tmp_path / "public" / "index.html", "<main>product app</main>\n")
    _write(tmp_path / "agents" / "lead_engineer" / "tasks" / "TASK-001.md", "private task\n")

    plan = build_export_plan(tmp_path, package_root)
    creates = {item.source for item in plan.creates}

    assert "scripts/agent_worker.py" in creates
    assert "AGENTS.md" in creates
    assert "public/index.html" not in creates
    assert "agents/lead_engineer/tasks/TASK-001.md" not in creates


def test_export_apply_copies_missing_templates_and_blocks_unsafe_content(tmp_path):
    package_root = tmp_path / "packages" / "agent_runtime"
    _write(package_root / "templates" / "project" / ".gitkeep")
    _write(tmp_path / "scripts" / "agent_worker.py", "print('worker')\n")
    _write(tmp_path / "scripts" / "auto_runner.py", "OPENAI_API_" + "KEY=unsafe\n")

    assert main(["export", "--host-root", str(tmp_path), "--package-root", str(package_root), "--apply"]) == 1

    template_root = package_root / "src" / "agent_runtime" / "templates" / "project"
    assert (template_root / "scripts" / "agent_worker.py").exists() is False
    (tmp_path / "scripts" / "auto_runner.py").write_text("print('safe')\n", encoding="utf-8")

    assert main(["export", "--host-root", str(tmp_path), "--package-root", str(package_root), "--apply"]) == 0
    assert (template_root / "scripts" / "agent_worker.py").read_text(encoding="utf-8") == "print('worker')\n"
    assert (template_root / "scripts" / "auto_runner.py").read_text(encoding="utf-8") == "print('safe')\n"


def test_publish_check_requires_public_github_source_contract(tmp_path):
    _write_public_source(tmp_path)

    findings = analyze_publish(tmp_path)

    assert findings == []


def test_github_workflow_runs_publish_gates_against_clean_bundle():
    workflow = (PACKAGE_ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "publish-bundle --source . --dest .tmp/public-source --apply" in workflow
    assert "publish-github-plan --source .tmp/public-source" in workflow
    assert "PYTHONPATH=.tmp/public-source/src python -m agent_runtime.cli release-preflight" in workflow
    assert "--warning-summary-gate-strict-refs" in workflow
    assert "--warning-summary-gate-strict-refs \"${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}\"" in workflow
    check_step = _extract_workflow_step(workflow, "Check release preflight")
    assert "--warning-summary-gate-strict-refs \"${{ steps.resolve_warning_summary_strict_refs.outputs.strict_refs }}\"" in check_step
    assert "PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS" not in check_step
    assert "PYTHONPATH=.tmp/public-source/src python -m agent_runtime.cli release-preflight" in check_step
    assert f"--tag {CURRENT_RELEASE_TAG}" in workflow
    assert "--host-root .tmp/public-source/tests/fixtures/host" in workflow
    assert "publish-github-plan --source . --remote-url" not in workflow
    assert "release-preflight --source . --host-root" not in workflow


def test_release_metadata_and_cli_defaults_track_current_public_tag():
    parser = cli_module.build_parser()

    assert __version__ == CURRENT_RELEASE_VERSION
    assert parser.parse_args(["publish-tag-smoke", "--repo-dir", "repo", "--install-dir", "install", "--check"]).tag == CURRENT_RELEASE_TAG
    assert parser.parse_args(["publish-github-plan", "--remote-url", "https://github.com/example/agent_runtime.git", "--install-dir", "install", "--check"]).tag == CURRENT_RELEASE_TAG
    assert parser.parse_args(["publish-github-execute", "--remote-url", "https://github.com/example/agent_runtime.git", "--install-dir", "install"]).tag == CURRENT_RELEASE_TAG
    assert parser.parse_args(["release-preflight", "--remote-url", "https://github.com/example/agent_runtime.git", "--check"]).tag == CURRENT_RELEASE_TAG


def test_publish_check_blocks_duplicate_top_level_templates_without_ignore(tmp_path):
    _write(tmp_path / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(tmp_path / "README.md", "# agent_runtime\n")
    _write(tmp_path / "src" / "agent_runtime" / "__init__.py", "")
    _write(tmp_path / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(tmp_path / ".github" / "workflows" / "test.yml", "python -m agent_runtime.cli sanitize --root . --check\n")
    _write(tmp_path / "templates" / "project" / "scripts" / "agent_worker.py", "")

    findings = analyze_publish(tmp_path)
    details = {(finding.kind, finding.path) for finding in findings}

    assert ("duplicate-template-tree", "templates") in details


def test_publish_bundle_copies_clean_public_source_only(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_public_source(source)
    _write(source / "tests" / "test_smoke.py", "def test_smoke():\n    assert True\n")
    _write(source / "build" / "lib" / "generated.py", "stale\n")
    _write(source / "templates" / "project" / "legacy.md", "duplicate\n")

    plan = build_bundle_plan(source, dest)
    rels = {item.path for item in plan.files}

    assert "src/agent_runtime/templates/project/scripts/agent_worker.py" in rels
    assert "tests/test_smoke.py" in rels
    assert "build/lib/generated.py" not in rels
    assert "templates/project/legacy.md" not in rels

    assert main(["publish-bundle", "--source", str(source), "--dest", str(dest), "--apply"]) == 0
    assert (dest / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py").exists()
    assert (dest / "templates").exists() is False
    assert (dest / "build").exists() is False
    assert analyze_publish(dest) == []


def test_publish_bundle_includes_owner_docs_manifest_entries(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write_public_source(source)
    _write(
        source / "AGENT_RUNTIME_CUSTOM_BRIEF.md",
        "\n".join(
            [
                "---",
                "signal: pass",
                "score: 90",
                "---",
                "# Custom Brief",
                "",
                "## Bottom Line",
                "Included through owner-docs manifest.",
                "",
                "## Signal",
                "",
                "| Item | Status |",
                "| --- | --- |",
                "| include | pass |",
                "",
                "## Action Board",
                "No action needed.",
                "",
                "## Risks / Blockers",
                "None.",
                "",
                "## Decision",
                "Include manifest docs.",
                "",
                "## Next Steps",
                "Continue.",
            ]
        )
        + "\n",
    )
    _write(
        source / "owner-docs.yml",
        "owner_docs:\n  - BACKLOG-BOARD.md\n  - AGENT_RUNTIME_CUSTOM_BRIEF.md\n",
    )

    plan = build_bundle_plan(source, dest)
    rels = {item.path for item in plan.files}

    assert "AGENT_RUNTIME_CUSTOM_BRIEF.md" in rels


def test_publish_bundle_refuses_non_empty_destination(tmp_path):
    source = tmp_path / "source"
    dest = tmp_path / "dest"
    _write(source / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(source / "README.md", "# agent_runtime\n")
    _write(source / ".github" / "workflows" / "test.yml", "python -m pytest tests -q\npython -m agent_runtime.cli sanitize --root . --check\n")
    _write(source / "src" / "agent_runtime" / "__init__.py", "")
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(source / ".gitignore", "/templates/\n")
    _write(dest / "keep.txt", "do not overwrite\n")

    assert main(["publish-bundle", "--source", str(source), "--dest", str(dest), "--apply"]) == 1
    assert (dest / "keep.txt").read_text(encoding="utf-8") == "do not overwrite\n"


def test_publish_tag_smoke_plan_uses_file_git_tag(tmp_path):
    source = tmp_path / "source"
    repo_dir = tmp_path / "repo"
    install_dir = tmp_path / "install"
    _write_public_source(source)

    plan = build_tag_smoke_plan(source, repo_dir, install_dir, "v0.1.0")

    assert plan.findings == ()
    assert plan.install_spec.startswith("git+file:")
    assert plan.install_spec.endswith("@v0.1.0")


def test_publish_tag_smoke_refuses_non_empty_work_dirs(tmp_path):
    source = tmp_path / "source"
    repo_dir = tmp_path / "repo"
    install_dir = tmp_path / "install"
    _write(source / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(source / "README.md", "# agent_runtime\n")
    _write(source / ".github" / "workflows" / "test.yml", "python -m pytest tests -q\npython -m agent_runtime.cli sanitize --root . --check\n")
    _write(source / "src" / "agent_runtime" / "__init__.py", "")
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(source / ".gitignore", "/templates/\n")
    _write(repo_dir / "keep.txt", "do not overwrite\n")
    _write(install_dir / "keep.txt", "do not overwrite\n")

    plan = build_tag_smoke_plan(source, repo_dir, install_dir, "v0.1.0")
    kinds = {finding.kind for finding in plan.findings}

    assert "repo-dir-not-empty" in kinds
    assert "install-dir-not-empty" in kinds


def test_publish_github_plan_builds_owner_approved_remote_commands(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write_public_source(source)

    plan = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        install_dir,
        tag="v0.1.0",
        branch="main",
    )

    command_text = "\n".join(plan.commands)
    work_dir = source.resolve() / ".tmp" / "github-worktree"

    assert plan.findings == ()
    assert plan.repository == "example/agent_runtime"
    assert plan.work_dir == work_dir
    assert "gh repo create example/agent_runtime --public" not in plan.commands
    repo_command_index = next(index for index, command in enumerate(plan.commands) if "gh','repo','create'" in command)
    repo_command = plan.commands[repo_command_index]
    assert "gh','repo','view'" in repo_command
    assert "gh','repo','create'" in repo_command
    assert "github-repo-not-public" in repo_command
    assert "not found" in repo_command
    assert "could not resolve to a repository" in repo_command
    assert plan.commands.index(f'cd "{work_dir}" && git tag "v0.1.0"') < repo_command_index
    assert repo_command_index < plan.commands.index(f'cd "{work_dir}" && git push -u origin "main"')
    assert f'publish-bundle --source "{source.resolve()}" --dest "{work_dir}" --apply' in command_text
    assert plan.install_spec == "git+https://github.com/example/agent_runtime.git@v0.1.0"
    assert f'cd "{work_dir}" && git -c user.name="Agent Runtime Release" -c user.email=agent-runtime-release@example.invalid commit -m "release v0.1.0"' in command_text
    assert f'cd "{work_dir}" && git remote add origin "https://github.com/example/agent_runtime.git"' in command_text
    assert f'cd "{work_dir}" && git push -u origin "main"' in command_text
    assert f'cd "{work_dir}" && git push origin "v0.1.0"' in command_text
    assert "python -m pip install --target" in command_text
    assert str(install_dir.resolve()) in command_text
    assert "sys.path.insert(0," in command_text
    assert "from agent_runtime.sync import default_template_root" in command_text
    assert "template_sentinel" in command_text
    assert "raise SystemExit(0 if sentinel else 1)" in command_text
    assert "'publish-github-status'" in command_text
    assert "'--remote-url','https://github.com/example/agent_runtime.git'" in command_text
    assert "'--branch','main'" in command_text
    assert "'--require-workflow','--wait-workflow','--workflow-head-sha',sha,'--check'" in command_text
    assert "subprocess.check_output" in command_text
    assert "rev-parse" in command_text
    assert "$(" not in command_text


def test_publish_github_plan_quotes_paths_with_spaces(tmp_path):
    source = tmp_path / "source with spaces"
    install_dir = source / ".tmp" / "install dir"
    _write_public_source(source)

    plan = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        install_dir,
    )

    command_text = "\n".join(plan.commands)
    work_dir = source.resolve() / ".tmp" / "github-worktree"

    assert f'--source "{source.resolve()}"' in command_text
    assert f'--dest "{work_dir}"' in command_text
    assert f'cd "{work_dir}" && git init' in command_text
    assert f'--target "{install_dir.resolve()}"' in command_text


def test_publish_github_plan_blocks_unsafe_branch_and_tag_refs(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    plan = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        tag="v0.1.0;rm",
        branch="main;rm",
    )

    kinds = {finding.kind for finding in plan.findings}

    assert "unsafe-git-branch" in kinds
    assert "unsafe-git-tag" in kinds


def test_publish_github_plan_parses_ssh_remote_repository(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write(source / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(source / "README.md", "# agent_runtime\n")
    _write(source / ".github" / "workflows" / "test.yml", "python -m pytest tests -q\npython -m agent_runtime.cli sanitize --root . --check\n")
    _write(source / "src" / "agent_runtime" / "__init__.py", "")
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(source / ".gitignore", "/templates/\n")

    plan = build_github_plan(source, "git@github.com:example/agent_runtime.git", install_dir)

    assert plan.repository == "example/agent_runtime"
    assert plan.install_spec == f"git+ssh://git@github.com/example/agent_runtime.git@{CURRENT_RELEASE_TAG}"


def test_publish_github_plan_reports_malformed_github_remote(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write(source / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(source / "README.md", "# agent_runtime\n")
    _write(source / ".github" / "workflows" / "test.yml", "python -m pytest tests -q\npython -m agent_runtime.cli sanitize --root . --check\n")
    _write(source / "src" / "agent_runtime" / "__init__.py", "")
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(source / ".gitignore", "/templates/\n")

    plan = build_github_plan(source, "https://github.com/example", install_dir)
    kinds = {finding.kind for finding in plan.findings}

    assert "malformed-github-remote-url" in kinds


def test_publish_github_plan_blocks_placeholder_remote_owner(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    plan = build_github_plan(
        source,
        "https://github.com/OWNER/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert "placeholder-remote-url" in {finding.kind for finding in plan.findings}


def test_publish_github_plan_requires_github_remote(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write(source / "pyproject.toml", "[tool.setuptools.package-data]\nagent_runtime=['templates/project/**/*']\n")
    _write(source / "README.md", "# agent_runtime\n")
    _write(source / ".github" / "workflows" / "test.yml", "python -m pytest tests -q\npython -m agent_runtime.cli sanitize --root . --check\n")
    _write(source / "src" / "agent_runtime" / "__init__.py", "")
    _write(source / "src" / "agent_runtime" / "templates" / "project" / "scripts" / "agent_worker.py", "")
    _write(source / ".gitignore", "/templates/\n")

    plan = build_github_plan(source, "https://gitlab.com/example/agent_runtime.git", install_dir)
    kinds = {finding.kind for finding in plan.findings}

    assert "non-github-remote-url" in kinds


def test_publish_github_plan_blocks_files_outside_clean_bundle_contract(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write_public_source(source)
    _write(source / "docs" / "private-note.md", "not part of the public bundle\n")

    plan = build_github_plan(source, "https://github.com/example/agent_runtime.git", install_dir)
    findings = {(finding.path, finding.kind) for finding in plan.findings}

    assert ("docs/private-note.md", "unexpected-source-file") in findings


def test_publish_github_plan_blocks_nested_build_files_git_would_add(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write_public_source(source)
    _write(source / "src" / "agent_runtime" / "build" / "private.txt", "host-only\n")

    plan = build_github_plan(source, "https://github.com/example/agent_runtime.git", install_dir)
    findings = {(finding.path, finding.kind) for finding in plan.findings}

    assert ("src/agent_runtime/build/private.txt", "unexpected-source-file") in findings


def test_publish_github_plan_blocks_existing_git_repository_source(tmp_path):
    source = tmp_path / "source"
    install_dir = source / ".tmp" / "install"
    _write_public_source(source)
    _write(source / ".git" / "config", "[core]\n")

    plan = build_github_plan(source, "https://github.com/example/agent_runtime.git", install_dir)
    kinds = {finding.kind for finding in plan.findings}

    assert "source-git-repo-exists" in kinds


def test_publish_github_plan_requires_safe_empty_install_dir(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    _write(source / ".tmp" / "install" / "old.txt", "stale\n")

    root_install = build_github_plan(source, "https://github.com/example/agent_runtime.git", source)
    outside_install = build_github_plan(source, "https://github.com/example/agent_runtime.git", tmp_path / "outside")
    non_empty_install = build_github_plan(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert "unsafe-github-install-dir" in {finding.kind for finding in root_install.findings}
    assert "unsafe-github-install-dir" in {finding.kind for finding in outside_install.findings}
    assert "github-install-dir-not-empty" in {finding.kind for finding in non_empty_install.findings}


def test_publish_github_status_reports_invalid_auth_without_repo_probe():
    calls = []

    def fake_runner(args):
        calls.append(args)
        return CommandResult(args=args, returncode=1, stdout="", stderr="token is invalid\n")

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)

    kinds = {finding.kind for finding in status.findings}
    assert status.repository == "example/agent_runtime"
    assert "gh-auth-unavailable" in kinds
    assert calls == [("gh", "auth", "status")]


def test_publish_github_status_prefers_diagnostic_auth_line():
    def fake_runner(args):
        return CommandResult(
            args=args,
            returncode=1,
            stdout="github.com\n  X Failed to log in to github.com account user\n  - The token in default is invalid.\n",
            stderr="",
        )

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)
    checks = {check.name: check for check in status.checks}

    assert "Failed to log in" in checks["auth"].detail


def test_publish_github_status_checks_user_and_repo_when_auth_ok():
    calls = []

    def fake_runner(args):
        calls.append(args)
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\nToken scopes: 'repo', 'workflow'\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC","url":"https://github.com/example/agent_runtime"}\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)
    checks = {check.name: check for check in status.checks}

    assert status.findings == ()
    assert checks["auth"].status == "ok"
    assert checks["user"].detail == "login=example"
    assert checks["repo"].detail == "available"
    assert calls[-1] == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url")


def test_publish_github_status_blocks_missing_workflow_scope_when_auth_ok():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\nToken scopes: 'repo'\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        raise AssertionError(args)

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)
    kinds = {finding.kind for finding in status.findings}
    checks = {check.name: check for check in status.checks}

    assert "gh-workflow-scope-missing" in kinds
    assert checks["scope"].status == "blocked"


def test_publish_github_status_blocks_private_repo_when_auth_ok():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PRIVATE","url":"https://github.com/example/agent_runtime"}\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)
    kinds = {finding.kind for finding in status.findings}
    checks = {check.name: check for check in status.checks}

    assert "github-repo-not-public" in kinds
    assert checks["repo"].status == "blocked"


def test_publish_github_status_blocks_repo_with_missing_visibility():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime"}\n', stderr="")
        raise AssertionError(args)

    status = build_github_status("https://github.com/example/agent_runtime.git", runner=fake_runner)
    kinds = {finding.kind for finding in status.findings}
    checks = {check.name: check for check in status.checks}

    assert "github-repo-visibility-missing" in kinds
    assert checks["repo"].status == "blocked"


def test_publish_github_status_requires_workflow_success_when_requested():
    calls = []

    def fake_runner(args):
        calls.append(args)
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args == (
            "gh",
            "run",
            "list",
            "--repo",
            "example/agent_runtime",
            "--branch",
            "main",
            "--workflow",
            "test",
            "--limit",
            "1",
            "--json",
            "status,conclusion,headSha,url,workflowName",
        ):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"success","headSha":"abc123","url":"https://github.com/example/agent_runtime/actions/runs/1","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        runner=fake_runner,
    )
    checks = {check.name: check for check in status.checks}

    assert status.findings == ()
    assert checks["workflow"].status == "ok"
    assert "conclusion=success" in checks["workflow"].detail
    assert calls[-1][0:3] == ("gh", "run", "list")


def test_publish_github_status_blocks_successful_run_from_wrong_workflow():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"success","headSha":"newsha","url":"https://github.com/example/agent_runtime/actions/runs/8","workflowName":"docs"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        workflow_head_sha="newsha",
        runner=fake_runner,
    )
    kinds = {finding.kind for finding in status.findings}

    assert "github-workflow-wrong-name" in kinds


def test_publish_github_status_flags_failed_workflow_when_required():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"failure","headSha":"abc123","url":"https://github.com/example/agent_runtime/actions/runs/2","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        runner=fake_runner,
    )
    kinds = {finding.kind for finding in status.findings}
    checks = {check.name: check for check in status.checks}

    assert "github-workflow-not-success" in kinds
    assert checks["workflow"].status == "blocked"


def test_publish_github_status_waits_until_workflow_success_when_requested():
    workflow_calls = 0

    def fake_runner(args):
        nonlocal workflow_calls
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            workflow_calls += 1
            if workflow_calls == 1:
                return CommandResult(
                    args=args,
                    returncode=0,
                    stdout='[{"status":"in_progress","conclusion":"","headSha":"abc123","url":"https://github.com/example/agent_runtime/actions/runs/3","workflowName":"test"}]\n',
                    stderr="",
                )
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"success","headSha":"abc123","url":"https://github.com/example/agent_runtime/actions/runs/3","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        wait_workflow=True,
        workflow_timeout_seconds=5,
        workflow_poll_seconds=0,
        runner=fake_runner,
    )
    checks = {check.name: check for check in status.checks}

    assert status.findings == ()
    assert workflow_calls == 2
    assert checks["workflow"].status == "ok"


def test_publish_github_status_blocks_successful_workflow_for_different_head_sha():
    def fake_runner(args):
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"success","headSha":"oldsha","url":"https://github.com/example/agent_runtime/actions/runs/5","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        workflow_head_sha="newsha",
        runner=fake_runner,
    )
    kinds = {finding.kind for finding in status.findings}

    assert "github-workflow-head-sha-mismatch" in kinds


def test_publish_github_status_waits_for_matching_head_sha_success():
    workflow_calls = 0

    def fake_runner(args):
        nonlocal workflow_calls
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            workflow_calls += 1
            if workflow_calls == 1:
                return CommandResult(
                    args=args,
                    returncode=0,
                    stdout='[{"status":"completed","conclusion":"success","headSha":"oldsha","url":"https://github.com/example/agent_runtime/actions/runs/5","workflowName":"test"}]\n',
                    stderr="",
                )
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"completed","conclusion":"success","headSha":"newsha","url":"https://github.com/example/agent_runtime/actions/runs/6","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        wait_workflow=True,
        workflow_head_sha="newsha",
        workflow_timeout_seconds=5,
        workflow_poll_seconds=0,
        runner=fake_runner,
    )

    assert status.findings == ()
    assert workflow_calls == 2


def test_publish_github_status_times_out_waiting_for_workflow_success():
    workflow_calls = 0

    def fake_runner(args):
        nonlocal workflow_calls
        if args == ("gh", "auth", "status"):
            return CommandResult(args=args, returncode=0, stdout="Logged in\n", stderr="")
        if args == ("gh", "api", "user", "--jq", ".login"):
            return CommandResult(args=args, returncode=0, stdout="example\n", stderr="")
        if args == ("gh", "repo", "view", "example/agent_runtime", "--json", "nameWithOwner,visibility,url"):
            return CommandResult(args=args, returncode=0, stdout='{"nameWithOwner":"example/agent_runtime","visibility":"PUBLIC"}\n', stderr="")
        if args[0:3] == ("gh", "run", "list"):
            workflow_calls += 1
            return CommandResult(
                args=args,
                returncode=0,
                stdout='[{"status":"queued","conclusion":"","headSha":"abc123","url":"https://github.com/example/agent_runtime/actions/runs/4","workflowName":"test"}]\n',
                stderr="",
            )
        raise AssertionError(args)

    status = build_github_status(
        "https://github.com/example/agent_runtime.git",
        branch="main",
        require_workflow=True,
        wait_workflow=True,
        workflow_timeout_seconds=0,
        workflow_poll_seconds=0,
        runner=fake_runner,
    )
    kinds = {finding.kind for finding in status.findings}

    assert workflow_calls == 1
    assert "github-workflow-timeout" in kinds


def test_publish_github_execution_stops_before_mutation_when_auth_fails(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 1 if step.name == "gh-auth-status" else 0

    exit_code = run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
    )

    assert exit_code == 1
    assert calls == ["gh-auth-status"]


def test_publish_github_execution_stops_before_mutation_when_workflow_scope_missing(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 1 if step.name == "gh-workflow-scope" else 0

    exit_code = run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
    )

    assert exit_code == 1
    assert calls == ["gh-auth-status", "gh-workflow-scope"]


def test_publish_github_execution_skips_create_when_repo_exists(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 0

    assert run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
    ) == 0

    assert "repo-ensure-public" in calls
    assert "repo-view" not in calls
    assert "repo-create" not in calls
    assert calls[-1] == "github-status"


def test_publish_github_execution_creates_repo_when_missing(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 0

    assert run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
    ) == 0

    assert calls.index("git-tag") < calls.index("repo-ensure-public")
    assert "push-tag" in calls
    assert calls[-1] == "github-status"


def test_publish_github_execution_uses_fail_closed_public_repo_ensure_step(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )
    step_names = [step.name for step in execution.steps]
    ensure_step = execution.steps[step_names.index("repo-ensure-public")]
    ensure_command = " ".join(ensure_step.args)

    assert "repo-view" not in step_names
    assert "repo-create" not in step_names
    assert step_names.index("git-tag") < step_names.index("repo-ensure-public")
    assert step_names.index("repo-ensure-public") < step_names.index("push-branch")
    assert "visibility" in ensure_command
    assert "github-repo-not-public" in ensure_command
    assert "could not resolve to a repository" in ensure_command


def test_publish_github_execution_finishes_local_release_before_repo_create(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )
    step_names = [step.name for step in execution.steps]

    assert step_names.index("prepare-worktree") < step_names.index("repo-ensure-public")
    assert step_names.index("git-commit") < step_names.index("repo-ensure-public")
    assert step_names.index("git-tag") < step_names.index("repo-ensure-public")
    assert step_names.index("repo-ensure-public") < step_names.index("push-branch")


def test_publish_github_execution_does_not_create_repo_when_prepare_worktree_fails(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    def fake_runner(step):
        calls.append(step.name)
        return 0

    monkeypatch.setattr(cli_module.publish_github_execute, "_prepare_worktree", lambda source_root, work_dir: 1)

    exit_code = run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
    )

    assert exit_code == 1
    assert calls == ["gh-auth-status", "gh-workflow-scope"]


def test_publish_github_execution_replaces_workflow_head_sha_placeholder(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    status_args = {}

    def fake_runner(step):
        if step.name == "github-status":
            status_args["args"] = step.args
        return 0

    assert run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=True,
        runner=fake_runner,
        release_sha_resolver=lambda work_dir: "newsha",
    ) == 0

    assert "--workflow-head-sha" in status_args["args"]
    assert "newsha" in status_args["args"]
    assert "__AGENT_RUNTIME_RELEASE_SHA__" not in status_args["args"]


def test_publish_github_execution_plan_mode_does_not_run_steps(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    calls = []

    execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )
    exit_code = run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        execute=False,
        runner=lambda step: calls.append(step.name) or 0,
    )

    assert exit_code == 0
    assert calls == []
    assert execution.steps[0].name == "gh-auth-status"


def test_publish_github_execution_checks_workflow_after_install(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert [step.name for step in execution.steps][-2:] == ["verify-installed-templates", "github-status"]
    assert execution.steps[-1].args == (
        sys.executable,
        "-m",
        "agent_runtime.cli",
        "publish-github-status",
        "--remote-url",
        "https://github.com/example/agent_runtime.git",
        "--branch",
        "main",
        "--workflow-name",
        "test",
        "--require-workflow",
        "--wait-workflow",
        "--workflow-head-sha",
        "__AGENT_RUNTIME_RELEASE_SHA__",
        "--check",
    )


def test_publish_github_execution_plan_output_quotes_paths_with_spaces(tmp_path, capsys):
    source = tmp_path / "source with spaces"
    _write_public_source(source)
    install_dir = source / ".tmp" / "install dir"

    exit_code = run_github_publish(
        source,
        "https://github.com/example/agent_runtime.git",
        install_dir,
        execute=False,
    )

    output = capsys.readouterr().out
    work_dir = source.resolve() / ".tmp" / "github-worktree"
    assert exit_code == 0
    assert f'(cd "{work_dir}") git init' in output
    assert f'--target "{install_dir.resolve()}"' in output


def test_publish_github_execution_uses_throwaway_worktree_for_git_steps(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)

    execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    git_steps = [step for step in execution.steps if step.name.startswith("git-") or step.name.startswith("push-")]
    assert git_steps
    assert all(step.cwd == source.resolve() / ".tmp" / "github-worktree" for step in git_steps)
    assert all(step.cwd != source.resolve() for step in git_steps)
    assert execution.steps[1].name == "gh-workflow-scope"
    assert execution.steps[2].name == "prepare-worktree"


def test_publish_github_execution_blocks_unsafe_or_non_empty_worktree(tmp_path):
    source = tmp_path / "source"
    _write_public_source(source)
    outside_worktree = tmp_path / "outside-worktree"
    non_empty_worktree = source / ".tmp" / "github-worktree"
    non_empty_worktree.mkdir(parents=True)
    (non_empty_worktree / "leftover.txt").write_text("stale", encoding="utf-8")

    outside_execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
        work_dir=outside_worktree,
    )
    non_empty_execution = build_github_execution(
        source,
        "https://github.com/example/agent_runtime.git",
        source / ".tmp" / "install",
    )

    assert "unsafe-github-work-dir" in {finding.kind for finding in outside_execution.findings}
    assert "github-work-dir-not-empty" in {finding.kind for finding in non_empty_execution.findings}


def test_publish_github_execute_cli_passes_work_dir(tmp_path, monkeypatch):
    captured = {}

    def fake_run(source, remote_url, install_dir, *, tag, branch, work_dir, execute):
        captured["source"] = source
        captured["remote_url"] = remote_url
        captured["install_dir"] = install_dir
        captured["tag"] = tag
        captured["branch"] = branch
        captured["work_dir"] = work_dir
        captured["execute"] = execute
        return 0

    monkeypatch.setattr(cli_module.publish_github_execute, "run_github_publish", fake_run)

    assert main(
        [
            "publish-github-execute",
            "--source",
            str(tmp_path / "source"),
            "--remote-url",
            "https://github.com/example/agent_runtime.git",
            "--install-dir",
            str(tmp_path / "source" / ".tmp" / "install"),
            "--work-dir",
            str(tmp_path / "source" / ".tmp" / "work"),
            "--execute",
        ]
    ) == 0

    assert captured["work_dir"] == tmp_path / "source" / ".tmp" / "work"
    assert captured["execute"] is True



def test_sanitize_allows_reports_schema_docs_but_blocks_report_records(tmp_path):
    # BUG-004 (#19): REPORTING-FORMAT.md links reports/README.md + reports/INDEX.md,
    # so those structural schema docs ship in the template. Actual BRIEF/PLAN
    # records under reports/ remain host-local and forbidden.
    source = tmp_path / "source"
    _write_public_source(source)
    reports_dir = (
        source / "src" / "agent_runtime" / "templates" / "project" / "agents" / "lead_engineer" / "reports"
    )
    _write(reports_dir / "README.md", "# Reports Archive\n")
    _write(reports_dir / "INDEX.md", "# Reports Index\n")
    _write(reports_dir / "BRIEF-2026-07-04-001.md", "# host-local record\n")

    sanitize_findings = {(finding.path, finding.kind) for finding in analyze_sanitize(source)}

    prefix = "src/agent_runtime/templates/project/agents/lead_engineer/reports"
    assert (f"{prefix}/README.md", "forbidden-template-path") not in sanitize_findings
    assert (f"{prefix}/INDEX.md", "forbidden-template-path") not in sanitize_findings
    assert (f"{prefix}/BRIEF-2026-07-04-001.md", "forbidden-template-path") in sanitize_findings
