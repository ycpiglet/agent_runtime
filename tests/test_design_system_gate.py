from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "scripts" / "design_system_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("design_system_gate", SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_required_artifacts_exist_and_roles_resolve():
    mod = _load()
    findings = mod.artifact_findings(ROOT) + mod.role_findings(ROOT)
    assert findings == []


def test_gate_detects_raw_literals_in_explicit_path(tmp_path):
    mod = _load()
    ui = tmp_path / "raw.css"
    ui.write_text(".x { color: #fff; padding: 12px; }\n", encoding="utf-8")
    findings = mod.scan_raw_literals([ui], ROOT)
    assert {finding.code for finding in findings} == {"raw-color", "raw-size"}


def test_gate_allows_token_definitions_and_vars(tmp_path):
    mod = _load()
    ui = tmp_path / "tokens.css"
    ui.write_text(
        ":root {\n"
        "  --panel: #fff;\n"
        "  --space-3: 12px;\n"
        "}\n"
        ".x { color: var(--panel); padding: var(--space-3); }\n",
        encoding="utf-8",
    )
    assert mod.scan_raw_literals([ui], ROOT) == []


def test_diff_line_scan_detects_added_raw_literals():
    mod = _load()
    diff = "\n".join(
        [
            "diff --git a/src/agent_runtime/ui_console.py b/src/agent_runtime/ui_console.py",
            "--- a/src/agent_runtime/ui_console.py",
            "+++ b/src/agent_runtime/ui_console.py",
            "@@ -10,0 +11,2 @@",
            "+.x { color: #fff; padding: 12px; }",
            "+.y { color: var(--ink); padding: var(--space-4); }",
        ]
    )

    findings = mod.scan_raw_literal_lines(mod.added_ui_lines_from_diff(diff, ROOT))

    assert {finding.code for finding in findings} == {"raw-color", "raw-size"}
    assert {finding.line for finding in findings} == {11}


def test_diff_line_scan_allows_added_token_definitions():
    mod = _load()
    diff = "\n".join(
        [
            "diff --git a/src/agent_runtime/ui_design_assets.py b/src/agent_runtime/ui_design_assets.py",
            "--- a/src/agent_runtime/ui_design_assets.py",
            "+++ b/src/agent_runtime/ui_design_assets.py",
            "@@ -1,0 +2,3 @@",
            "+:root {",
            "+  --space-9: 18px;",
            "+}",
        ]
    )

    assert mod.scan_raw_literal_lines(mod.added_ui_lines_from_diff(diff, ROOT)) == []


def test_gate_ignores_html_numeric_entities(tmp_path):
    """`&#9881;`-style accessibility icon entities must not read as hex colors."""
    mod = _load()
    ui = tmp_path / "icons.html"
    ui.write_text(
        '<span class="icon" aria-hidden="true">&#9881;</span>\n'
        '<span class="icon" aria-hidden="true">&#9776;</span>\n',
        encoding="utf-8",
    )
    assert mod.scan_raw_literals([ui], ROOT) == []


def test_gate_still_flags_real_hex_color(tmp_path):
    mod = _load()
    ui = tmp_path / "c.css"
    ui.write_text(".x { color: #abc; }\n", encoding="utf-8")
    assert {finding.code for finding in mod.scan_raw_literals([ui], ROOT)} == {"raw-color"}


def test_diff_line_scan_ignores_added_html_entities():
    mod = _load()
    diff = "\n".join(
        [
            "diff --git a/src/agent_runtime/ui_console.py b/src/agent_runtime/ui_console.py",
            "--- a/src/agent_runtime/ui_console.py",
            "+++ b/src/agent_runtime/ui_console.py",
            "@@ -10,0 +11,2 @@",
            '+.icon::before { content: "&#9881;"; }',
            "+.real { color: #fff; }",
        ]
    )

    findings = mod.scan_raw_literal_lines(mod.added_ui_lines_from_diff(diff, ROOT))

    assert {finding.code for finding in findings} == {"raw-color"}
    assert {finding.line for finding in findings} == {12}


def test_missing_artifacts_are_reported(tmp_path):
    mod = _load()
    (tmp_path / "agents" / "project").mkdir(parents=True)
    findings = mod.artifact_findings(tmp_path)
    assert {finding.code for finding in findings} == {"missing-artifact"}


def test_default_check_passes_current_changed_baseline():
    mod = _load()
    assert mod.cmd_check(root=ROOT, paths=[], all_ui=False, json_output=True) == 0


def test_all_ui_check_passes_current_tokenized_baseline():
    mod = _load()
    assert mod.cmd_check(root=ROOT, paths=[], all_ui=True, json_output=True) == 0
