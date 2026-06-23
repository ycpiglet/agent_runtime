"""Tests for the un-keyed-literal i18n gate (scripts/i18n_literal_gate.py).

The gate scans the UI layer for NEW user-facing string literals in the
*targeted categories* (error / toast / empty-state) that bypass the i18n
table (i.e. are not routed through ``t("key")``). It mirrors the
``design_system_gate`` style: ``--check`` exits nonzero on findings.

The detection is deliberately narrow: it only inspects a fixed set of render
*sinks* (toast helpers, empty/error-state helpers, the status-line error
assignment) so it cannot false-positive on already-keyed strings or on
non-user-facing literals (CSS, ids, data identifiers).
"""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "scripts" / "i18n_literal_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("i18n_literal_gate", SPEC)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---- sink detection: flags bare literals in the targeted sinks ----------


def test_gate_flags_unkeyed_toast_literal(tmp_path):
    mod = _load()
    js = (
        'function f() {\n'
        '  pushUndoToast("3 tasks edited", undo);\n'
        '}\n'
    )
    findings = mod.scan_js_text("ui_x.py", js)
    assert any(f.category == "toast" for f in findings)


def test_gate_flags_unkeyed_emptystate_literal(tmp_path):
    mod = _load()
    js = 'panel.innerHTML = emptyState("No widgets here");\n'
    findings = mod.scan_js_text("ui_x.py", js)
    assert any(f.category == "empty-state" for f in findings)


def test_gate_flags_unkeyed_errorstate_literal(tmp_path):
    mod = _load()
    js = 'host.innerHTML = errorState("Graph broke", data.error);\n'
    findings = mod.scan_js_text("ui_x.py", js)
    assert any(f.category == "error" for f in findings)


def test_gate_flags_unkeyed_status_line_error(tmp_path):
    mod = _load()
    js = '$("status-line").textContent = "State load failed";\n'
    findings = mod.scan_js_text("ui_x.py", js)
    assert any(f.category == "error" for f in findings)


# ---- precision: keyed sinks must NOT be flagged -------------------------


def test_gate_allows_keyed_toast(tmp_path):
    mod = _load()
    js = 'pushUndoToast(t("toast.tasks_edited"), undo);\n'
    assert mod.scan_js_text("ui_x.py", js) == []


def test_gate_allows_keyed_emptystate(tmp_path):
    mod = _load()
    js = 'panel.innerHTML = emptyState(t("empty.no_items"));\n'
    assert mod.scan_js_text("ui_x.py", js) == []


def test_gate_allows_keyed_status_line_error(tmp_path):
    mod = _load()
    js = '$("status-line").textContent = t("error.state_load_failed");\n'
    assert mod.scan_js_text("ui_x.py", js) == []


def test_gate_allows_keyed_literal_with_dynamic_suffix(tmp_path):
    """A keyed prefix concatenated with interpolated data is allowed."""
    mod = _load()
    js = '$("status-line").textContent = t("error.state_load_failed") + ": " + error.message;\n'
    assert mod.scan_js_text("ui_x.py", js) == []


def test_gate_ignores_non_sink_literals(tmp_path):
    """Plain literals not flowing into a sink are not user-facing copy here."""
    mod = _load()
    js = (
        'const klass = "undo-toast";\n'
        'node.className = "activity-toast kind-message";\n'
        'const status = "active";\n'
    )
    assert mod.scan_js_text("ui_x.py", js) == []


def test_gate_ignores_empty_string_arguments(tmp_path):
    """Empty/whitespace string args (clearing a region) are not copy."""
    mod = _load()
    js = (
        'setText("board-dnd-status", message || "");\n'
        'stateHostClear.innerHTML = "";\n'
    )
    assert mod.scan_js_text("ui_x.py", js) == []


# ---- key-resolution: targeted copy resolves in both locales ------------


def test_targeted_keys_resolve_in_both_locales():
    import importlib

    import agent_runtime.ui_state as ui_state

    importlib.reload(ui_state)
    table = ui_state.I18N_STRINGS
    # Every error/toast/empty/loading copy key must carry both ko + en.
    targeted = [
        key
        for key in table
        if key.split(".", 1)[0] in {"toast", "error", "empty", "loading"}
    ]
    assert targeted, "expected targeted error/toast/empty-state keys in the table"
    for key in targeted:
        assert table[key].get("ko"), f"{key} missing ko"
        assert table[key].get("en"), f"{key} missing en"
        # KO and EN should be distinct (real localization, not a copy).
        assert ui_state.lookup_i18n(key, "en") == table[key]["en"]
        assert ui_state.lookup_i18n(key, "ko") == table[key]["ko"]


def test_representative_copy_is_keyed():
    """A few load-bearing strings from the sweep must be in the table."""
    import agent_runtime.ui_state as ui_state

    for key in (
        "error.state_load_failed",
        "empty.no_items",
        "empty.no_active_sessions",
        "toast.undo",
    ):
        assert key in ui_state.I18N_STRINGS, f"missing keyed copy: {key}"
        assert ui_state.I18N_STRINGS[key]["ko"]
        assert ui_state.I18N_STRINGS[key]["en"]


# ---- whole-tree check: the gate must pass on the current tree ----------


def test_check_passes_on_current_tree():
    mod = _load()
    assert mod.cmd_check(root=ROOT, json_output=True) == 0


# ---- CI wiring ---------------------------------------------------------


def test_ci_workflow_runs_i18n_literal_gate():
    """CI must invoke the i18n literal gate so coverage can't silently regress."""
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
    assert "python scripts/i18n_literal_gate.py --check" in workflow
    step = _extract_workflow_step(workflow, "Check i18n literal gate (error/toast/empty-state coverage)")
    assert "python scripts/i18n_literal_gate.py --check" in step
    # Additive, unconditional, and must not collide with the publish `--tag` steps.
    assert "if:" not in step
    assert "--tag" not in step


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
