from __future__ import annotations

import pytest
from pathlib import Path

from agent_runtime import cli as cli_module
from agent_runtime import release_preflight


def test_release_preflight_run_preflight_prefers_cli_input_over_env(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}

    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["warning_summary_gate_strict_refs"] = warning_summary_gate_strict_refs
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)
    monkeypatch.setenv("PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS", "refs/heads/env")

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=True,
        warning_summary_gate_strict_refs="refs/heads/main",
    )
    assert code == 0
    assert captured["warning_summary_gate_strict_refs"] == "refs/heads/main"


def test_release_preflight_run_preflight_falls_back_to_env(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}

    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["warning_summary_gate_strict_refs"] = warning_summary_gate_strict_refs
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)
    monkeypatch.setenv("PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS", "refs/heads/fallback")

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=True,
    )
    assert code == 0
    assert captured["warning_summary_gate_strict_refs"] == "refs/heads/fallback"


def test_release_preflight_cli_empty_string_disables_env_fallback(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}

    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["warning_summary_gate_strict_refs"] = warning_summary_gate_strict_refs
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)
    monkeypatch.setenv("PASS_39_WARNING_SUMMARY_GATE_STRICT_REFS", "refs/heads/fallback")

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=True,
        warning_summary_gate_strict_refs="",
    )
    assert code == 0
    assert captured["warning_summary_gate_strict_refs"] == ""


def test_release_preflight_run_preflight_returns_success_without_findings(monkeypatch, tmp_path):
    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(release_preflight.PreflightCheck("sanitize", "ok", "no findings", ()),),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=True,
    )
    assert code == 0


def test_release_preflight_run_preflight_returns_failure_when_findings_present(monkeypatch, tmp_path):
    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(
                release_preflight.PreflightCheck(
                    "sanitize",
                    "blocked",
                    "blocked",
                    (release_preflight.PublishFinding("agent_runtime.yml", "preflight-blocked", "blocking finding"),),
                ),
            ),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=True,
    )
    assert code == 1


def test_release_preflight_run_preflight_returns_zero_when_check_is_disabled(monkeypatch, tmp_path):
    def fake_build_preflight_plan(
        *,
        source_root: Path,
        host_root: Path,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        remote_url: str,
        tag: str,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        return release_preflight.PreflightPlan(
            source_root=source_root,
            host_root=host_root,
            remote_url=remote_url,
            tag=tag,
            checks=(
                release_preflight.PreflightCheck(
                    "sanitize",
                    "blocked",
                    "blocked",
                    (release_preflight.PublishFinding("agent_runtime.yml", "preflight-blocked", "blocking finding"),),
                ),
            ),
        )

    monkeypatch.setattr(release_preflight, "build_preflight_plan", fake_build_preflight_plan)

    code = release_preflight.run_preflight(
        source_root=tmp_path / "source",
        host_root=tmp_path / "host",
        remote_url="https://github.com/example/agent_runtime.git",
        bundle_dir=tmp_path / "bundle",
        tag_repo_dir=tmp_path / "tag-repo",
        tag_install_dir=tmp_path / "tag-install",
        github_install_dir=tmp_path / ".tmp" / "github-install",
        host_install_dir=tmp_path / ".tmp" / "host-install",
        tag="v0.1.6",
        check=False,
    )
    assert code == 0


def test_release_preflight_cli_parser_exposes_warning_summary_gate_strict_refs_option():
    parser = cli_module.build_parser()
    parsed = parser.parse_args(
        [
            "release-preflight",
            "--remote-url",
            "https://github.com/example/agent_runtime.git",
            "--warning-summary-gate-strict-refs",
            "refs/heads/main",
        ]
    )
    assert parsed.warning_summary_gate_strict_refs == "refs/heads/main"


def test_release_preflight_cli_default_check_is_non_blocking(monkeypatch, tmp_path):
    captured: dict[str, bool] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["check"] = check
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--bundle-dir",
                str(tmp_path / "bundle"),
                "--tag-repo-dir",
                str(tmp_path / "tag-repo"),
                "--tag-install-dir",
                str(tmp_path / "tag-install"),
                "--github-install-dir",
                str(tmp_path / ".tmp" / "github-install"),
                "--host-install-dir",
                str(tmp_path / ".tmp" / "host-install"),
            ]
        )
        == 7
    )
    assert captured["check"] is False


def test_release_preflight_cli_check_flag_forwards_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, bool] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["check"] = check
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--bundle-dir",
                str(tmp_path / "bundle"),
                "--tag-repo-dir",
                str(tmp_path / "tag-repo"),
                "--tag-install-dir",
                str(tmp_path / "tag-install"),
                "--github-install-dir",
                str(tmp_path / ".tmp" / "github-install"),
                "--host-install-dir",
                str(tmp_path / ".tmp" / "host-install"),
                "--check",
            ]
        )
        == 7
    )
    assert captured["check"] is True


def test_release_preflight_cli_default_strict_refs_is_none(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["warning_summary_gate_strict_refs"] = warning_summary_gate_strict_refs
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--bundle-dir",
                str(tmp_path / "bundle"),
                "--tag-repo-dir",
                str(tmp_path / "tag-repo"),
                "--tag-install-dir",
                str(tmp_path / "tag-install"),
                "--github-install-dir",
                str(tmp_path / ".tmp" / "github-install"),
                "--host-install-dir",
                str(tmp_path / ".tmp" / "host-install"),
            ]
        )
        == 7
    )
    assert captured["warning_summary_gate_strict_refs"] is None


def test_release_preflight_cli_empty_string_strict_refs_forwards_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, str | None] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["warning_summary_gate_strict_refs"] = warning_summary_gate_strict_refs
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--bundle-dir",
                str(tmp_path / "bundle"),
                "--tag-repo-dir",
                str(tmp_path / "tag-repo"),
                "--tag-install-dir",
                str(tmp_path / "tag-install"),
                "--github-install-dir",
                str(tmp_path / ".tmp" / "github-install"),
                "--host-install-dir",
                str(tmp_path / ".tmp" / "host-install"),
                "--warning-summary-gate-strict-refs",
                "",
            ]
        )
        == 7
    )
    assert captured["warning_summary_gate_strict_refs"] == ""


def test_release_preflight_cli_default_paths_forward_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, Path] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["source_root"] = source_root
        captured["host_root"] = host_root
        captured["bundle_dir"] = bundle_dir
        captured["tag_repo_dir"] = tag_repo_dir
        captured["tag_install_dir"] = tag_install_dir
        captured["github_install_dir"] = github_install_dir
        captured["host_install_dir"] = host_install_dir
        return 7

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
            ]
        )
        == 7
    )
    assert captured["source_root"] == tmp_path
    assert captured["host_root"] == tmp_path
    assert captured["bundle_dir"] == Path(".tmp/public-source")
    assert captured["tag_repo_dir"] == Path(".tmp/tag-repo")
    assert captured["tag_install_dir"] == Path(".tmp/tag-install")
    assert captured["github_install_dir"] == Path(".tmp/github-install")
    assert captured["host_install_dir"] == Path(".tmp/agent_runtime-upstream")


def test_release_preflight_cli_explicit_paths_forward_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, Path] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["source_root"] = source_root
        captured["host_root"] = host_root
        captured["bundle_dir"] = bundle_dir
        captured["tag_repo_dir"] = tag_repo_dir
        captured["tag_install_dir"] = tag_install_dir
        captured["github_install_dir"] = github_install_dir
        captured["host_install_dir"] = host_install_dir
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--bundle-dir",
                str(tmp_path / "custom-public-source"),
                "--tag-repo-dir",
                str(tmp_path / "custom-tag-repo"),
                "--tag-install-dir",
                str(tmp_path / "custom-tag-install"),
                "--github-install-dir",
                str(tmp_path / "custom-github-install"),
                "--host-install-dir",
                str(tmp_path / "custom-host-install"),
            ]
        )
        == 7
    )
    assert captured["source_root"] == tmp_path / "source"
    assert captured["host_root"] == tmp_path / "host"
    assert captured["bundle_dir"] == tmp_path / "custom-public-source"
    assert captured["tag_repo_dir"] == tmp_path / "custom-tag-repo"
    assert captured["tag_install_dir"] == tmp_path / "custom-tag-install"
    assert captured["github_install_dir"] == tmp_path / "custom-github-install"
    assert captured["host_install_dir"] == tmp_path / "custom-host-install"


def test_release_preflight_cli_default_tag_forwards_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, str] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["tag"] = tag
        return 7

    parser = cli_module.build_parser()
    expected_default_tag = parser.parse_args(
        [
            "release-preflight",
            "--source",
            str(tmp_path / "source"),
            "--host-root",
            str(tmp_path / "host"),
            "--remote-url",
            "https://github.com/example/agent_runtime.git",
        ]
    ).tag

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
            ]
        )
        == 7
    )
    assert captured["tag"] == expected_default_tag


def test_release_preflight_cli_explicit_tag_forwards_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, str] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["tag"] = tag
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
                "--tag",
                "v2.0.0",
            ]
        )
        == 7
    )
    assert captured["tag"] == "v2.0.0"


def test_release_preflight_cli_remote_url_forwards_to_preflight(monkeypatch, tmp_path):
    captured: dict[str, str] = {}

    def fake_run_preflight(
        source_root: Path,
        host_root: Path,
        remote_url: str,
        *,
        bundle_dir: Path,
        tag_repo_dir: Path,
        tag_install_dir: Path,
        github_install_dir: Path,
        host_install_dir: Path,
        tag: str,
        check: bool,
        warning_summary_gate_strict_refs: str | None = None,
    ):
        captured["remote_url"] = remote_url
        return 7

    monkeypatch.setattr(cli_module.release_preflight, "run_preflight", fake_run_preflight)
    assert (
        cli_module.main(
            [
                "release-preflight",
                "--source",
                str(tmp_path / "source"),
                "--host-root",
                str(tmp_path / "host"),
                "--remote-url",
                "https://github.com/example/agent_runtime.git",
            ]
        )
        == 7
    )
    assert captured["remote_url"] == "https://github.com/example/agent_runtime.git"


def test_release_preflight_cli_remote_url_required():
    parser = cli_module.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["release-preflight"])


def test_release_preflight_main_exits_when_remote_url_is_missing():
    with pytest.raises(SystemExit) as exc:
        cli_module.main(["release-preflight"])
    assert exc.value.code == 2

