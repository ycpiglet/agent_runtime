from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_package_data_enumerates_template_dotpaths() -> None:
    # TASK-AR-531: fast config guard -- the package-data must explicitly enumerate
    # the dot-paths the `**/*` glob drops, so the wheel ships the template wiring.
    # (The full build-and-inspect proof is scripts/verify_wheel_dotfiles.py.)
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for pattern in (
        "templates/project/.gitattributes",
        "templates/project/.githooks/**/*",
        "templates/project/.github/**/*",
        "templates/project/.codex/**/*",
    ):
        assert pattern in text, f"package-data missing dot-path: {pattern}"
