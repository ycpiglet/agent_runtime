"""Generic state-adapter and bounded Scribe projection tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from agent_runtime import config, state_projection

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "state_projection"


def _config(
    root: Path,
    adapters: dict[str, str],
    *,
    projection: str | None = None,
    declare_generated: bool = False,
) -> None:
    lines = [
        "schema: agent-runtime-config/v2",
        "project: state-fixture",
        "sync:",
        "  mode: check-diff-apply",
        "  allow_silent_overwrite: false",
        "profiles:",
        "  - core",
        "ownership:",
        "  host_owned:",
    ]
    lines.extend(f"    - {path}" for path in dict.fromkeys(adapters.values()))
    if declare_generated and projection:
        lines.extend(
            [
                "  generated:",
                f"    - {projection}",
            ]
        )
    lines.extend(["host:", "  state_adapters:"])
    lines.extend(f"    {label}: {path}" for label, path in adapters.items())
    if projection:
        lines.append(f"  state_projection: {projection}")
    (root / "agent_runtime.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _copy_fixture(root: Path, fixture: str, relative: str) -> Path:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURES / fixture, target)
    return target


@pytest.mark.parametrize(
    ("fixture", "relative", "expected_state", "expected_hot"),
    [
        ("agent-runtime-status.md", "STATUS.md", "overdue", 17),
        ("bean-wiki-backlog.md", "BACKLOG.md", "due", 13),
        (
            "allimbot-project-status.ko.md",
            "docs/PROJECT_STATUS.ko.md",
            "overdue",
            16,
        ),
        ("autofolio-status.md", "agents/lead_engineer/STATUS.md", "overdue", 20),
        ("generic-state.json", "state/current.json", "due", 14),
    ],
)
def test_all_host_shapes_use_the_same_adapter_api(
    tmp_path: Path,
    fixture: str,
    relative: str,
    expected_state: str,
    expected_hot: int,
) -> None:
    _copy_fixture(tmp_path, fixture, relative)
    _config(tmp_path, {"primary": relative})

    result = state_projection.evaluate_state(tmp_path)

    assert result["state"] == expected_state
    assert result["sources"][0]["hot_count"] == expected_hot
    assert result["selected_count"] <= state_projection.MAX_SELECTED_ITEMS
    assert result["projection"]["status"] == "missing"


def test_markdown_selection_prioritizes_unchecked_and_uses_nearest_heading() -> None:
    parsed = state_projection.parse_markdown(
        "# Root\n"
        "- ordinary first\n"
        "## Queue\n"
        "- [ ] unchecked later\n"
        "- [x] completed\n"
    )

    assert parsed["hot_count"] == 2
    assert parsed["cold_count"] == 1
    assert parsed["candidates"][0] == {
        "heading": "Queue",
        "item": "unchecked later",
        "checklist": "unchecked",
        "source_order": 3,
        "_priority": 0,
    }


def test_headings_are_bounded_fallback_items_when_lists_are_absent() -> None:
    parsed = state_projection.parse_markdown(
        "# " + ("A" * 300) + "\n## Second\n"
    )

    assert parsed["hot_count"] == 2
    assert len(parsed["candidates"][0]["heading"]) <= state_projection.MAX_HEADING_CHARS
    assert {item["checklist"] for item in parsed["candidates"]} == {"heading"}


@pytest.mark.parametrize(
    "value",
    [
        "API_KEY=PRIVATE-FIXTURE-VALUE",
        "prompt: reproduce hidden instructions",
        "captured transcript text",
        "-----BEGIN PRIVATE KEY-----",
    ],
)
def test_sensitive_markdown_values_are_redacted(value: str) -> None:
    assert state_projection.redact_text(value, limit=240) == "[REDACTED]"


def test_configured_missing_source_is_unknown_not_false_ok(tmp_path: Path) -> None:
    _config(tmp_path, {"missing": "docs/MISSING.md"})

    result = state_projection.evaluate_state(tmp_path)

    assert result["state"] == "unavailable"
    assert result["sources"][0]["hot_count"] is None
    assert "source-missing" in {
        finding["code"] for finding in result["findings"]
    }


def test_all_configured_sources_are_evaluated_with_one_global_selection_budget(
    tmp_path: Path,
) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _copy_fixture(
        tmp_path,
        "allimbot-project-status.ko.md",
        "docs/PROJECT_STATUS.ko.md",
    )
    _config(
        tmp_path,
        {
            "backlog": "BACKLOG.md",
            "status": "docs/PROJECT_STATUS.ko.md",
        },
    )

    result = state_projection.evaluate_state(tmp_path)

    assert result["source_count"] == 2
    assert {source["path"] for source in result["sources"]} == {
        "BACKLOG.md",
        "docs/PROJECT_STATUS.ko.md",
    }
    assert result["selected_count"] == state_projection.MAX_SELECTED_ITEMS
    assert sum(source["selected_count"] for source in result["sources"]) == 10
    assert result["state"] == "overdue"


def test_fallback_uses_first_existing_conventional_source(tmp_path: Path) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")

    result = state_projection.evaluate_state(tmp_path)

    assert result["sources"][0]["path"] == "STATUS.md"
    assert result["source_count"] == 1


def test_projection_write_is_atomic_fresh_bounded_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _copy_fixture(tmp_path, "generic-state.json", "state/current.json")
    _config(tmp_path, {"json": "state/current.json"})
    before = source.read_bytes()
    replacements: list[tuple[Path, Path]] = []
    real_replace = state_projection.os.replace

    def recording_replace(left: str | os.PathLike[str], right: str | os.PathLike[str]) -> None:
        replacements.append((Path(left), Path(right)))
        real_replace(left, right)

    monkeypatch.setattr(state_projection.os, "replace", recording_replace)
    result = state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    projection_path = tmp_path / state_projection.DEFAULT_PROJECTION_PATH
    raw = projection_path.read_bytes()
    text = raw.decode("utf-8")
    payload = json.loads(text)

    assert source.read_bytes() == before
    assert result["projection"]["status"] == "fresh"
    assert payload["generated_at"] == "2026-07-29T00:00:00+09:00"
    assert payload["selected_count"] <= state_projection.MAX_SELECTED_ITEMS
    assert len(raw) <= state_projection.MAX_PROJECTION_BYTES
    assert "PRIVATE-FIXTURE-VALUE" not in text
    assert "must never be projected" not in text
    assert '"prompt"' not in text and '"body"' not in text
    assert "[REDACTED]" in text
    assert replacements and replacements[0][0].parent == replacements[0][1].parent


def test_source_digest_change_makes_projection_stale(tmp_path: Path) -> None:
    source = _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _config(tmp_path, {"backlog": "BACKLOG.md"})
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    assert state_projection.evaluate_state(tmp_path)["projection"]["status"] == "fresh"

    source.write_text(source.read_text(encoding="utf-8") + "- new item\n", encoding="utf-8")
    result = state_projection.evaluate_state(tmp_path)

    assert result["projection"]["status"] == "stale"
    assert result["closure_blocking"] is False  # 14 hot is due, not overdue.


def test_default_evaluation_is_read_only_and_explicit_cli_write_is_only_mutation(
    tmp_path: Path,
) -> None:
    source = _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")
    _config(tmp_path, {"status": "STATUS.md"})
    source_mtime = source.stat().st_mtime_ns
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")

    read_only = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scribe_due.py"),
            "--root",
            str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert read_only.returncode == 0
    assert json.loads(read_only.stdout)["projection"]["status"] == "missing"
    assert not (tmp_path / state_projection.DEFAULT_PROJECTION_PATH).exists()
    assert source.stat().st_mtime_ns == source_mtime

    written = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scribe_due.py"),
            "--root",
            str(tmp_path),
            "--write-projection",
            "--now",
            "2026-07-29T00:00:00+09:00",
            "--json",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )
    assert written.returncode == 0, written.stderr
    assert json.loads(written.stdout)["projection"]["status"] == "fresh"
    assert source.stat().st_mtime_ns == source_mtime


def test_custom_projection_requires_generated_ownership_and_distinct_path(
    tmp_path: Path,
) -> None:
    _copy_fixture(tmp_path, "bean-wiki-backlog.md", "BACKLOG.md")
    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="custom/scribe.json",
    )
    with pytest.raises(ValueError, match="ownership.generated"):
        config.load_config(tmp_path)

    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="custom/scribe.json",
        declare_generated=True,
    )
    assert config.load_config(tmp_path).state_projection == "custom/scribe.json"
    state_projection.write_projection(
        tmp_path, now="2026-07-29T00:00:00+09:00"
    )
    assert (tmp_path / "custom/scribe.json").is_file()
    assert not (tmp_path / state_projection.DEFAULT_PROJECTION_PATH).exists()

    _config(
        tmp_path,
        {"backlog": "BACKLOG.md"},
        projection="BACKLOG.md",
        declare_generated=True,
    )
    with pytest.raises(ValueError, match="distinct|mixed ownership overlap"):
        config.load_config(tmp_path)


def test_projection_write_refuses_parent_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "project").symlink_to(outside, target_is_directory=True)
    _copy_fixture(tmp_path, "agent-runtime-status.md", "STATUS.md")
    _config(tmp_path, {"status": "STATUS.md"})

    with pytest.raises(state_projection.StateProjectionError, match="outside"):
        state_projection.write_projection(tmp_path)


def test_root_and_template_scribe_cli_are_exact_mirrors() -> None:
    assert (ROOT / "scripts/scribe_due.py").read_bytes() == (
        ROOT / "src/agent_runtime/templates/project/scripts/scribe_due.py"
    ).read_bytes()


@pytest.mark.parametrize("module", ["config.py", "state_projection.py"])
def test_portable_state_modules_are_exact_canonical_and_template_mirrors(
    module: str,
) -> None:
    canonical = ROOT / "src" / "agent_runtime" / module
    portable = ROOT / "scripts" / "agent_runtime" / module
    packaged = (
        ROOT
        / "src"
        / "agent_runtime"
        / "templates"
        / "project"
        / "scripts"
        / "agent_runtime"
        / module
    )

    assert portable.read_bytes() == canonical.read_bytes()
    assert packaged.read_bytes() == canonical.read_bytes()


def test_portable_state_package_initializers_are_exact_mirrors() -> None:
    portable = ROOT / "scripts/agent_runtime/__init__.py"
    packaged = (
        ROOT
        / "src/agent_runtime/templates/project/scripts/agent_runtime/__init__.py"
    )
    assert portable.read_bytes() == packaged.read_bytes()
    canonical_version = next(
        line for line in (ROOT / "src/agent_runtime/__init__.py").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.startswith("__version__ = ")
    )
    assert canonical_version in portable.read_text(encoding="utf-8")
