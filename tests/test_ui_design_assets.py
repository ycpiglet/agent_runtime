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
    assert classes["patternSvgLayeredDagreLayout"] == "pattern_component"
    assert classes["graphStatusIconText"] == "ui_component"
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
    assert "function patternSvgLayeredDagreLayout" in js
    assert "function graphStatusIconText" in js
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
    assert "patternSvgLayeredDagreLayout(nodes, edges" in source


def test_layered_graph_helper_records_dagre_license_and_local_boundary(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    assert "@dagrejs/dagre 3.0.0, MIT" in js
    assert "dist/dagre.min.js" in js
    assert "single /app.js bundle" in js
    assert "http://unpkg.com" not in js
    assert "https://unpkg.com" not in js


# ----- TASK-AR-587: Agent avatar (experimental) -----

def test_pattern_agent_avatar_is_classified_as_pattern_component():
    """patternAgentAvatar must be registered in ASSETIZATION_CLASSES."""
    classes = ui_design_assets.ASSETIZATION_CLASSES
    assert classes["patternAgentAvatar"] == "pattern_component"


def test_pattern_agent_avatar_determinism():
    """Same seed must always yield byte-identical SVG output (TASK-AR-587)."""
    seed = "same-seed"
    result_a = ui_design_assets.patternAgentAvatar(seed)
    result_b = ui_design_assets.patternAgentAvatar(seed)
    assert result_a == result_b, "patternAgentAvatar is not deterministic for the same seed"


def test_pattern_agent_avatar_different_seeds_differ():
    """Different seeds must produce different SVGs (basic uniqueness check)."""
    svg_a = ui_design_assets.patternAgentAvatar("seed-alpha")
    svg_b = ui_design_assets.patternAgentAvatar("seed-beta")
    assert svg_a != svg_b, "Different seeds should produce different avatars"


def test_pattern_agent_avatar_label_is_html_escaped():
    """A label is escaped into <title> (no XSS); Python must match the JS escapeHtml sibling."""
    svg = ui_design_assets.patternAgentAvatar("a1", role="qa", label="<script>alert(1)</script>")
    assert "<script>alert" not in svg, "label must be HTML-escaped in <title> (XSS sink)"
    assert "&lt;script&gt;" in svg


def test_pattern_agent_avatar_returns_svg_string():
    """Output must be an SVG element string."""
    svg = ui_design_assets.patternAgentAvatar("test-agent-id")
    assert svg.strip().startswith("<svg"), "Avatar output must start with <svg"
    assert "class=\"agent-avatar\"" in svg
    assert "xmlns=\"http://www.w3.org/2000/svg\"" in svg


def test_pattern_agent_avatar_no_raw_color_literals():
    """Avatar SVG must reference only semantic tokens, no raw hex colors."""
    import re
    svg = ui_design_assets.patternAgentAvatar("test-agent-id", role="lead-engineer")
    raw_color = re.compile(r'(?<!&)#[0-9a-fA-F]{3,8}\b')
    assert not raw_color.search(svg), "Avatar SVG must not contain raw color literals"


def test_pattern_agent_avatar_role_accent():
    """Role parameter must produce an accent ring using a semantic token."""
    svg_with_role = ui_design_assets.patternAgentAvatar("agent-x", role="lead-engineer")
    svg_no_role = ui_design_assets.patternAgentAvatar("agent-x", role="")
    # With role: accent ring rendered with stroke
    assert 'stroke="var(--primary)"' in svg_with_role
    # Without role: neutral line-strong ring (or no ring for empty role)
    assert 'stroke="var(--primary)"' not in svg_no_role


def test_pattern_agent_avatar_all_known_roles_resolve():
    """All ORG-MODEL canonical role ids must resolve to a known accent token."""
    from agent_runtime.ui_design_assets import _AVATAR_ROLE_ACCENT_PY, patternAgentAvatar
    known_roles = list(_AVATAR_ROLE_ACCENT_PY.keys())
    for role in known_roles:
        svg = patternAgentAvatar(f"agent-{role}", role=role)
        assert "stroke=" in svg, f"Role {role!r} should produce an accent ring"


def test_no_runtime_dicebear_api_dependency():
    """api.dicebear.com must not appear in any runtime code path."""
    ui_design_src = (ROOT / "src" / "agent_runtime" / "ui_design_assets.py").read_text(encoding="utf-8")
    ui_console_src = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")
    ui_console_py = (ROOT / "src" / "agent_runtime" / "ui_console.py").read_text(encoding="utf-8")
    # api.dicebear.com may appear in comments/docstrings but not in callable code paths
    # We check that it never appears as a fetch/URL string in the JavaScript or Python code
    import re
    url_pattern = re.compile(r"""["']https?://api\.dicebear\.com""")
    assert not url_pattern.search(ui_design_src), "api.dicebear.com must not appear as a runtime URL in ui_design_assets.py"
    assert not url_pattern.search(ui_console_src), "api.dicebear.com must not appear as a runtime URL in ui_console_assets.py"
    assert not url_pattern.search(ui_console_py), "api.dicebear.com must not appear as a runtime URL in ui_console.py"


def test_pattern_agent_avatar_in_console_js(tmp_path):
    """patternAgentAvatar JS function must be served in the console JS bundle."""
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")
    assert "function patternAgentAvatar" in js, "patternAgentAvatar must be present in app.js"
    assert "patternAgentAvatar(avatarSeed" in js, "patternAgentAvatar must be called in agentCardTemplate"


def test_pattern_agent_avatar_label():
    """Label parameter must insert a <title> element in the SVG."""
    svg = ui_design_assets.patternAgentAvatar("agent-id", label="My Agent")
    assert "<title>My Agent</title>" in svg
