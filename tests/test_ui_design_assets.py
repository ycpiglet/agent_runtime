from pathlib import Path

from agent_runtime import ui_console
from agent_runtime import ui_console_assets
from agent_runtime import ui_design_assets


ROOT = Path(__file__).resolve().parent.parent


def test_ui_design_assets_classify_token_component_and_pattern_layers():
    classes = ui_design_assets.ASSETIZATION_CLASSES

    assert classes["UI_TOKEN_SCALE_CSS"] == "design_token"
    assert classes["componentButton"] == "ui_component"
    assert classes["componentTable"] == "ui_component"
    assert classes["componentModalShell"] == "ui_component"
    assert classes["componentProgressBar"] == "ui_component"
    assert classes["componentEmptyState"] == "ui_component"
    assert classes["patternTaskLane"] == "pattern_component"
    assert classes["patternClaimCard"] == "pattern_component"
    assert classes["patternEvidencePanel"] == "pattern_component"
    assert classes["patternCommandBar"] == "pattern_component"
    assert classes["patternStateMachinePanelLegend"] == "pattern_component"
    assert classes["patternAuditMeta"] == "pattern_component"
    assert classes["patternSurfaceMeta"] == "pattern_component"


def test_ui_design_token_scale_is_served_in_console_css(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert "Design-system token scale (TASK-AR-579" in css
    assert "--font-size-ui-sm" in css
    assert "--font-size-ui-12" in css
    assert "--space-6" in css
    # Semantic scale tokens (TASK-AR-583): px-aliases replaced by named tokens
    assert "--space-2xl" in css
    assert "--radius-sm" in css
    assert "--radius-hairline" in css


def test_ui_component_bundle_is_served_in_console_js(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    assert "UI component assets (TASK-AR-579)" in js
    assert "function componentCard" in js
    assert "function componentButton" in js
    assert "function componentTable" in js
    assert "function componentModalShell" in js
    assert "function componentMetaGrid" in js
    assert "function progressBar(value)" in js
    assert "function patternClaimCard" in js
    assert "function patternTaskLane" in js
    assert "function patternEvidencePanel" in js
    assert "function patternCommandBar" in js
    assert "function patternStateMachinePanelLegend" in js
    assert "function renderAuditMeta(content)" in js
    assert "function renderSurfaceMeta(content)" in js


def test_selected_helpers_are_not_redefined_inside_ui_console_source():
    source = (ROOT / "src" / "agent_runtime" / "ui_console.py").read_text(encoding="utf-8")
    asset_source = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")

    assert "function progressBar(value) {" not in source
    assert "function emptyState(title, hint) {" not in source
    assert "function renderAuditMeta(content) {" not in source
    assert "function renderSurfaceMeta(content) {" not in source
    assert "ui_design_assets.UI_COMPONENTS_JS" not in source
    assert "ui_design_assets.UI_COMPONENTS_JS" in asset_source


def test_console_serves_assets_from_asset_module_boundary():
    source = (ROOT / "src" / "agent_runtime" / "ui_console.py").read_text(encoding="utf-8")
    asset_source = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")

    assert "HTML = ui_console_assets.HTML" in source
    assert "CSS = ui_console_assets.CSS" in source
    assert "JS = ui_console_assets.JS" in source
    assert 'HTML = """<!doctype html>' not in source
    assert 'CSS = """/*' not in source
    assert 'JS = """// --- Theme system' not in source
    assert 'HTML = """<!doctype html>' in asset_source
    assert 'CSS = """/*' in asset_source
    assert 'JS = """// --- Theme system' in asset_source
    assert ui_console.HTML == ui_console_assets.HTML
    assert ui_console.CSS == ui_console_assets.CSS
    assert ui_console.JS == ui_console_assets.JS


def test_promoted_pattern_helpers_are_called_by_console_renderers():
    source = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")

    assert "return patternClaimCard(task" in source
    assert "return patternTaskLane({" in source
    assert "patternEvidencePanel(errors" in source
    assert "host.innerHTML = patternCommandBar(rows);" in source
    assert "legend.innerHTML = patternStateMachinePanelLegend();" in source
