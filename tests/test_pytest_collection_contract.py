from pathlib import Path


def test_default_pytest_collection_is_root_tests_only():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.pytest.ini_options]" in text
    assert 'testpaths = ["tests"]' in text
    assert 'pythonpath = [".", "src"]' in text


def test_template_tests_are_explicit_suite_only():
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "src/agent_runtime/templates/project/scripts" not in text
