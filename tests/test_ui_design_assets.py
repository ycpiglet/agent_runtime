import re
from pathlib import Path

from agent_runtime import ui_console
from agent_runtime import ui_console_assets
from agent_runtime import ui_design_assets


ROOT = Path(__file__).resolve().parent.parent


def _relative_luminance(hex_color: str) -> float:
    value = hex_color.strip().lstrip("#")
    channels = []
    for index in (0, 2, 4):
        channel = int(value[index : index + 2], 16) / 255
        channels.append(channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    fg = _relative_luminance(foreground)
    bg = _relative_luminance(background)
    high, low = max(fg, bg), min(fg, bg)
    return (high + 0.05) / (low + 0.05)


def test_ui_design_assets_classify_token_component_and_pattern_layers():
    classes = ui_design_assets.ASSETIZATION_CLASSES

    assert classes["UI_TOKEN_SCALE_CSS"] == "design_token"
    assert classes["componentButton"] == "ui_component"
    assert classes["componentTable"] == "ui_component"
    assert classes["componentModalShell"] == "ui_component"
    assert classes["componentProgressBar"] == "ui_component"
    assert classes["componentEmptyState"] == "ui_component"
    assert classes["componentIcon"] == "ui_component"
    assert classes["patternTaskLane"] == "pattern_component"
    assert classes["patternClaimCard"] == "pattern_component"
    assert classes["patternEvidencePanel"] == "pattern_component"
    assert classes["patternCommandBar"] == "pattern_component"
    assert classes["patternStateMachinePanelLegend"] == "pattern_component"
    assert classes["patternSvgLayeredDagreLayout"] == "pattern_component"
    assert classes["patternSvgForceAgentLayout"] == "pattern_component"
    assert classes["patternAgentAvatar"] == "pattern_component"
    assert classes["patternCalendarGrid"] == "pattern_component"
    assert classes["patternCalendarState"] == "pattern_component"
    assert classes["patternOfficeMapPlacement"] == "pattern_component"
    assert classes["graphStatusIconText"] == "ui_component"
    assert classes["patternAuditMeta"] == "pattern_component"
    assert classes["patternSurfaceMeta"] == "pattern_component"


def test_ui_design_token_scale_is_served_in_console_css(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert "@font-face" in css
    assert 'font-family: "Geist"' in css
    assert 'font-family: "Geist Mono"' in css
    assert "/vendor/geist/1.7.2/fonts/geist-sans/Geist-Variable.woff2" in css
    assert "/vendor/geist/1.7.2/fonts/geist-mono/GeistMono-Variable.woff2" in css
    assert "--font-sans" in css
    assert "--font-mono" in css
    assert "--icon-size" in css
    assert "Design-system token scale (TASK-AR-579" in css
    assert "--font-size-ui-sm" in css
    assert "--font-size-ui-12" in css
    assert "--space-6" in css
    # Semantic scale tokens (TASK-AR-583): px-aliases replaced by named tokens
    assert "--space-2xl" in css
    assert "--radius-sm" in css
    assert "--radius-hairline" in css
    assert "--space-px-" not in css
    assert "--radius-px-" not in css


def test_ui_component_bundle_is_served_in_console_js(tmp_path):
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    assert "UI component assets (TASK-AR-579)" in js
    assert "function componentCard" in js
    assert "function componentButton" in js
    assert "function componentTable" in js
    assert "function componentModalShell" in js
    assert "function componentMetaGrid" in js
    assert "function componentIcon" in js
    assert "UI component: Lucide icons (TASK-AR-589)" in js
    assert "function progressBar(value)" in js
    assert "function patternClaimCard" in js
    assert "function patternTaskLane" in js
    assert "function patternEvidencePanel" in js
    assert "function patternCommandBar" in js
    assert "function patternStateMachinePanelLegend" in js
    assert "function patternSvgLayeredDagreLayout" in js
    assert "function patternSvgForceAgentLayout" in js
    assert "function patternAgentAvatar" in js
    assert "function patternCalendarGrid" in js
    assert "function patternCalendarState" in js
    assert "function patternOfficeMapPlacement" in js
    assert "function graphStatusIconText" in js
    assert "function renderAuditMeta(content)" in js
    assert "function renderSurfaceMeta(content)" in js


def test_design_system_contract_lists_agent_avatar_pattern():
    docs = (ROOT / "docs" / "design" / "agent-runtime" / "DESIGN-SYSTEM.md").read_text(encoding="utf-8")

    assert "Promoted pattern usage as of `TASK-AR-587`" in docs
    assert "`patternAgentAvatar`" in docs
    assert "DiceBear Identicon" in docs
    assert "token-driven role accent" in docs


def test_selected_helpers_are_not_redefined_inside_ui_console_source():
    source = (ROOT / "src" / "agent_runtime" / "ui_console.py").read_text(encoding="utf-8")
    asset_source = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")

    assert "function progressBar(value) {" not in source
    assert "function emptyState(title, hint) {" not in source
    assert "function renderAuditMeta(content) {" not in source
    assert "function renderSurfaceMeta(content) {" not in source
    assert "ui_design_assets.UI_COMPONENTS_JS" not in source
    assert "ui_design_assets.UI_COMPONENTS_JS" in asset_source


def test_home_wip_uses_server_derived_claim_liveness_not_raw_status():
    source = (ROOT / "src" / "agent_runtime" / "ui_console_assets.py").read_text(encoding="utf-8")

    render_home = re.search(
        r"function renderHomeSummary\(\) \{(?P<body>.*?)\n\}\n\nfunction renderDashboard",
        source,
        flags=re.DOTALL,
    )
    assert render_home is not None
    claims_filter = re.search(
        r"const claims = .*?\.filter\((?P<body>.*?)\n\s*\);",
        render_home.group("body"),
        flags=re.DOTALL,
    )
    assert claims_filter is not None

    assert "claim.authority_active === true" in claims_filter.group("body")
    assert "claim.status" not in claims_filter.group("body")
    assert "HOME_ACTIVE_CLAIM_STATUSES" not in source


def test_cockpit_freshness_is_null_safe_before_initial_state_load():
    js = ui_console.build_response("/app.js", Path(".")).body.decode("utf-8")
    freshness = re.search(
        r"function stateFreshness\(\) \{(?P<body>.*?)\n\}",
        js,
        flags=re.DOTALL,
    )

    assert freshness is not None
    body = freshness.group("body")
    assert "runtimeState || {}" in body
    assert "runtimeState.built_at" not in body
    assert "runtimeState.generated_at" not in body
    assert "parseIsoDate" in body


def test_cockpit_summary_is_null_safe_before_initial_state_load():
    js = ui_console.build_response("/app.js", Path(".")).body.decode("utf-8")
    summary = re.search(
        r"function renderHomeSummary\(\) \{(?P<body>.*?)\n\}",
        js,
        flags=re.DOTALL,
    )

    assert summary is not None
    body = summary.group("body")
    assert "if (!runtimeState)" in body
    assert 'stripEl.textContent = ""' in body
    assert 'tiles.innerHTML = ""' in body
    assert "return;" in body
    assert "const state = runtimeState;" in body
    assert "runtimeState." not in body
    assert "state.tasks || []" in body
    assert "state.task_claims || []" in body


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


def test_layered_graph_helper_uses_vendored_dagre_and_d3_force_boundary(tmp_path):
    html = ui_console.build_response("/", tmp_path).body.decode("utf-8")
    js = ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")

    assert "/vendor/dagre/3.0.0/dagre.min.js" in html
    assert "/vendor/d3-quadtree/3.0.1/d3-quadtree.min.js" in html
    assert "/vendor/d3-dispatch/3.0.1/d3-dispatch.min.js" in html
    assert "/vendor/d3-timer/3.0.1/d3-timer.min.js" in html
    assert "/vendor/d3-force/3.0.0/d3-force.min.js" in html
    assert html.index("/vendor/dagre/3.0.0/dagre.min.js") < html.index("/app.js")
    assert html.index("/vendor/d3-quadtree/3.0.1/d3-quadtree.min.js") < html.index("/vendor/d3-force/3.0.0/d3-force.min.js")

    assert "@dagrejs/dagre 3.0.0" in js
    assert "function graphDagreRuntime()" in js
    assert "runtime.layout(graph)" in js
    assert "engine: \"@dagrejs/dagre\"" in js
    assert "/vendor/d3-force/3.0.0/d3-force.min.js" in js
    assert "function graphD3ForceRuntime()" in js
    assert "runtime.forceSimulation(simNodes)" in js
    assert "http://unpkg.com" not in js
    assert "https://unpkg.com" not in js


def test_vendored_graph_library_files_are_present_and_licensed():
    vendor = ROOT / "src" / "agent_runtime" / "vendor"
    required = {
        "dagre/3.0.0/dagre.min.js": "var dagre=",
        "dagre/3.0.0/LICENSE": "MIT",
        "d3-quadtree/3.0.1/d3-quadtree.min.js": "quadtree",
        "d3-quadtree/3.0.1/LICENSE": "Copyright",
        "d3-dispatch/3.0.1/d3-dispatch.min.js": "dispatch",
        "d3-dispatch/3.0.1/LICENSE": "Copyright",
        "d3-timer/3.0.1/d3-timer.min.js": "timer",
        "d3-timer/3.0.1/LICENSE": "Copyright",
        "d3-force/3.0.0/d3-force.min.js": "forceSimulation",
        "d3-force/3.0.0/LICENSE": "Copyright",
    }
    for rel_path, marker in required.items():
        body = (vendor / rel_path).read_text(encoding="utf-8")
        assert marker in body, rel_path


# ----- TASK-AR-589: Typography + icon assets (experimental) -----

def test_typography_font_tokens_are_self_hosted_without_cdn(tmp_path):
    css = ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")

    assert "https://fonts.googleapis.com" not in css
    assert "fonts.gstatic.com" not in css
    assert 'font-family: var(--font-sans);' in css
    assert 'font-family: var(--font-mono);' in css
    assert 'url("/vendor/geist/1.7.2/fonts/geist-sans/Geist-Variable.woff2")' in css
    assert 'url("/vendor/geist/1.7.2/fonts/geist-mono/GeistMono-Variable.woff2")' in css


def test_vendored_geist_font_files_are_present_and_licensed():
    vendor = ROOT / "src" / "agent_runtime" / "vendor" / "geist" / "1.7.2"
    license_text = (vendor / "LICENSE.txt").read_text(encoding="utf-8")
    package_text = (vendor / "package.json").read_text(encoding="utf-8")

    assert "SIL OPEN FONT LICENSE" in license_text
    assert '"version": "1.7.2"' in package_text

    # TASK-AR-589: the self-hosted Geist woff2 binaries must be vendored on disk
    # (this is what fixes the AR-588 404). Each referenced font file exists and
    # carries the WOFF2 "wOF2" signature.
    font_files = [
        vendor / "fonts" / "geist-sans" / "Geist-Variable.woff2",
        vendor / "fonts" / "geist-sans" / "Geist-Italic[wght].woff2",
        vendor / "fonts" / "geist-mono" / "GeistMono-Variable.woff2",
        vendor / "fonts" / "geist-mono" / "GeistMono-Italic[wght].woff2",
    ]
    for font_file in font_files:
        assert font_file.is_file(), f"missing vendored font binary: {font_file}"
        assert font_file.read_bytes()[:4] == b"wOF2", f"not a woff2 binary: {font_file}"


def test_vendored_lucide_icon_files_are_present_and_licensed():
    vendor = ROOT / "src" / "agent_runtime" / "vendor" / "lucide-static" / "1.21.0"
    license_text = (vendor / "LICENSE").read_text(encoding="utf-8")
    package_text = (vendor / "package.json").read_text(encoding="utf-8")

    assert "ISC License" in license_text
    assert '"version": "1.21.0"' in package_text
    for icon_name in ["menu", "settings", "home", "search", "users", "check-circle", "bar-chart", "zap"]:
        body = (vendor / "icons" / f"{icon_name}.svg").read_text(encoding="utf-8")
        assert "@license lucide-static v1.21.0 - ISC" in body
        assert 'stroke="currentColor"' in body


def test_component_icon_returns_token_safe_inline_svg():
    svg = ui_design_assets.componentIcon("menu", label="<Menu>")

    assert svg.startswith("<svg")
    assert 'class="icon"' in svg
    assert 'stroke="currentColor"' in svg
    assert 'width="var(--icon-size)"' in svg
    assert 'height="var(--icon-size)"' in svg
    assert "&lt;Menu&gt;" in svg
    assert "<Menu>" not in svg
    assert "#000" not in svg
    assert "M4 5h16" in svg


def test_component_icon_unknown_name_uses_safe_default():
    svg = ui_design_assets.componentIcon('"><script>alert(1)</script>', label="Unknown")

    assert "<script>" not in svg
    assert '"><script>' not in svg
    assert '<circle cx="12" cy="12" r="10"/>' in svg
    assert "Unknown" in svg


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
    assert 'data-dicebear-style="identicon"' in svg
    assert 'data-dicebear-version="9.4.2"' in svg


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


def test_pattern_agent_avatar_role_accents_meet_non_text_contrast():
    """Role accent rings meet WCAG AA non-text contrast in light and dark themes."""
    light_tokens = {
        "var(--primary)": "#2e6fdb",
        "var(--success)": "#0f7b55",
        "var(--warning)": "#cb7509",
        "var(--danger)": "#e03e3e",
        "var(--teal)": "#0f7b55",
        "var(--amber)": "#cb7509",
        "var(--violet)": "#6a48c9",
        "var(--muted)": "#787774",
    }
    dark_tokens = {
        "var(--primary)": "#5e6ad2",
        "var(--success)": "#27a644",
        "var(--warning)": "#d99a2b",
        "var(--danger)": "#f04438",
        "var(--teal)": "#31d0aa",
        "var(--amber)": "#d99a2b",
        "var(--violet)": "#5e6ad2",
        "var(--muted)": "#a2a8b3",
    }
    backgrounds = {
        "light": ("#ffffff", "#f1f1ef"),
        "dark": ("#010102", "#15171a"),
    }
    from agent_runtime.ui_design_assets import _AVATAR_ROLE_ACCENT_PY

    for role, token in _AVATAR_ROLE_ACCENT_PY.items():
      for theme_name, theme_tokens in (("light", light_tokens), ("dark", dark_tokens)):
          for bg in backgrounds[theme_name]:
              ratio = _contrast_ratio(theme_tokens[token], bg)
              assert ratio >= 3.0, f"{role} {token} fails {theme_name} non-text contrast: {ratio:.2f}"


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


def test_pattern_agent_avatar_uses_vendored_dicebear_identicon_boundary():
    """Avatar helper records and consumes a local DiceBear Identicon CC0 boundary."""
    assert ui_design_assets.DICEBEAR_IDENTICON_STYLE == "identicon"
    assert ui_design_assets.DICEBEAR_IDENTICON_VERSION == "9.4.2"
    assert ui_design_assets.DICEBEAR_IDENTICON_DESIGN_LICENSE == "CC0 1.0"
    assert ui_design_assets.DICEBEAR_IDENTICON_CODE_LICENSE == "MIT"
    assert ui_design_assets.DICEBEAR_IDENTICON_ROWS == (
        "xooox",
        "xxoxx",
        "xoxox",
        "oxxxo",
        "xxxxx",
        "oxoxo",
        "ooxoo",
    )

    source = (ROOT / "src" / "agent_runtime" / "ui_design_assets.py").read_text(encoding="utf-8")
    assert "src/agent_runtime/vendor/dicebear/identicon/9.4.2" in source
    assert "data-dicebear-style" in source
    assert "DICEBEAR_IDENTICON_ROWS" in source


def test_vendored_dicebear_identicon_files_are_present_and_licensed():
    """@dicebear/identicon is vendored locally with CC0 design and MIT code license."""
    vendor = ROOT / "src" / "agent_runtime" / "vendor" / "dicebear" / "identicon" / "9.4.2"
    required = {
        "package.json": "\"name\": \"@dicebear/identicon\"",
        "LICENSE": "License: CC0 1.0",
        "lib/index.js": "title: 'Identicon'",
        "lib/schema.js": "xooox",
        "lib/components/row1.js": "export const row1",
        "lib/components/row5.js": "export const row5",
    }
    for rel_path, marker in required.items():
        body = (vendor / rel_path).read_text(encoding="utf-8")
        assert marker in body, rel_path


# ----- TASK-AR-592: A11y + responsive pass -----

def test_task_ar_592_visual_responsive_tokens_exist():
    """New visual-system responsive constants are promoted into token assets."""
    css = ui_design_assets.UI_TOKEN_SCALE_CSS
    for token in (
        "--visual-sparkline-mobile-w",
        "--visual-graph-mobile-min-width",
        "--visual-graph-mobile-height",
        "--visual-state-machine-mobile-height",
    ):
        assert token in css


def test_task_ar_592_sparkline_accessibility_modes():
    """Informative sparklines get img semantics; decorative sparklines stay hidden."""
    informative = ui_design_assets.componentSparkline([1, 3, 2], label="Load trend")
    assert 'role="img"' in informative
    assert 'aria-label="Load trend"' in informative
    assert "<title>Load trend</title>" in informative

    decorative = ui_design_assets.componentSparkline([1, 3, 2])
    assert 'aria-hidden="true"' in decorative
    assert 'role="img"' not in decorative


def test_task_ar_592_empty_state_has_role_status():
    """componentEmptyState must carry role=status for screen-reader announcement."""
    html = ui_design_assets.componentEmptyState("Nothing here", "Try later")
    assert 'role="status"' in html
    assert 'aria-hidden="true"' in html   # decorative SVG inside


def test_task_ar_592_error_state_has_role_alert():
    """componentErrorState must carry role=alert for assertive announcement."""
    html = ui_design_assets.componentErrorState("Error", "Retry")
    assert 'role="alert"' in html
    assert 'aria-hidden="true"' in html   # decorative SVG inside


def test_task_ar_592_loading_state_has_role_status_and_live():
    """componentLoadingState must carry role=status and aria-live=polite."""
    html = ui_design_assets.componentLoadingState("Loading...")
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-hidden="true"' in html   # decorative spinner SVG inside


def test_task_ar_592_avatar_is_decorative_by_default():
    """patternAgentAvatar is aria-hidden when used as a decorative glyph (no explicit label)."""
    svg = ui_design_assets.patternAgentAvatar("agent-01", role="lead-engineer")
    assert 'aria-hidden="true"' in svg


def test_task_ar_592_avatar_label_uses_title_element():
    """patternAgentAvatar with a label inserts <title> for screen readers."""
    svg = ui_design_assets.patternAgentAvatar("agent-02", label="Lead Engineer bot")
    assert "<title>Lead Engineer bot</title>" in svg


def test_task_ar_592_icon_decorative_has_aria_hidden():
    """componentIcon without a label is aria-hidden (decorative)."""
    svg = ui_design_assets.componentIcon("menu")
    assert 'aria-hidden="true"' in svg
    assert 'role=' not in svg


def test_task_ar_592_icon_informative_has_role_and_label():
    """componentIcon with a label carries aria-label and no aria-hidden."""
    svg = ui_design_assets.componentIcon("settings", label="Open settings")
    assert 'aria-label="Open settings"' in svg
    assert 'aria-hidden' not in svg
    assert "<title>Open settings</title>" in svg


# ----- TASK-AR-590: data-viz palette + sparklines + state illustrations -----

import re


_THEME_BLOCK_RE = re.compile(r"(:root\b[^{]*\{[^}]*\}|\.theme-dark\b[^{]*\{[^}]*\})", re.DOTALL)


def _theme_blocks():
    """Return {'light': css_block, 'dark': css_block} for the console theme roots.

    The light theme lives on ``:root`` and the dark theme on a ``.theme-dark``
    (or equivalent) selector inside the served CSS.
    """
    css = ui_console.build_response("/app.css", Path(".")).body.decode("utf-8")
    blocks = {}
    # CSS rule bodies have no nested braces, so a body is everything up to the
    # next '}'. Capture the selector preceding each '{ ... }' block and keep the
    # ones that define the data-viz tokens: ':root' is the light theme root and
    # an attribute selector containing 'dark' (e.g. [data-theme="dark"]) is dark.
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        selector, body = match.group(1).strip(), match.group(2)
        if "--dv-cat-1" not in body:
            continue
        selector_tail = selector.splitlines()[-1].strip() if selector else ""
        if selector_tail == ":root":
            blocks["light"] = body
        elif "dark" in selector_tail:
            blocks["dark"] = body
    return blocks


def _token_value(block: str, token: str) -> str:
    match = re.search(rf"{re.escape(token)}\s*:\s*([^;]+);", block)
    assert match is not None, f"{token} not defined"
    return match.group(1).strip()


def test_task_ar_590_dataviz_palette_tokens_present_in_both_themes():
    """Categorical (8) + sequential (5) data-viz tokens exist for light and dark."""
    blocks = _theme_blocks()
    assert "light" in blocks, "light theme data-viz tokens missing"
    assert "dark" in blocks, "dark theme data-viz tokens missing"
    for theme, block in blocks.items():
        for i in range(1, 9):
            assert f"--dv-cat-{i}" in block, f"{theme}: --dv-cat-{i} missing"
        for i in range(1, 6):
            assert f"--dv-seq-{i}" in block, f"{theme}: --dv-seq-{i} missing"
        assert "--dv-sparkline" in block, f"{theme}: --dv-sparkline missing"


def test_task_ar_590_categorical_tokens_are_concrete_hex():
    """Categorical tokens resolve to literal hex (so contrast can be verified)."""
    blocks = _theme_blocks()
    for theme, block in blocks.items():
        for i in range(1, 9):
            value = _token_value(block, f"--dv-cat-{i}")
            assert re.fullmatch(r"#[0-9a-fA-F]{6}", value), (
                f"{theme}: --dv-cat-{i}={value!r} is not a 6-digit hex"
            )


def test_task_ar_590_categorical_tokens_meet_wcag_non_text_contrast():
    """Each categorical hue meets the WCAG 1.4.11 >=3:1 graphical threshold vs panel."""
    panels = {"light": "#f7f7f5", "dark": "#0f1011"}
    blocks = _theme_blocks()
    for theme, block in blocks.items():
        panel = panels[theme]
        for i in range(1, 9):
            value = _token_value(block, f"--dv-cat-{i}")
            ratio = _contrast_ratio(value, panel)
            assert ratio >= 3.0, (
                f"{theme}: --dv-cat-{i}={value} contrast {ratio:.2f}:1 vs panel "
                f"{panel} below WCAG non-text 3:1"
            )


def test_task_ar_590_sequential_scale_is_monotonic_progression():
    """Sequential steps progress monotonically in luminance (clear visual order)."""
    blocks = _theme_blocks()
    for theme, block in blocks.items():
        lums = [
            _relative_luminance(_token_value(block, f"--dv-seq-{i}"))
            for i in range(1, 6)
        ]
        # Strictly ordered (light->dark or dark->light); no two adjacent equal.
        ascending = all(a < b for a, b in zip(lums, lums[1:]))
        descending = all(a > b for a, b in zip(lums, lums[1:]))
        assert ascending or descending, f"{theme}: sequential scale not monotonic: {lums}"


def test_task_ar_590_graph_consumes_categorical_tokens():
    """Dependency/knowledge graph node styling consumes the categorical tokens."""
    css = ui_console.build_response("/app.css", Path(".")).body.decode("utf-8")
    assert "var(--dv-cat-1" in css, "graph nodes do not consume --dv-cat-1"


def test_task_ar_590_sparkline_renders_polyline_and_uses_token():
    """componentSparkline emits an SVG polyline whose stroke is the dv-sparkline token."""
    svg = ui_design_assets.componentSparkline([1, 5, 2, 8, 3])
    assert svg.startswith("<svg")
    assert "<polyline" in svg
    assert "var(--dv-sparkline" in svg
    # No raw color literal in the rendered output.
    assert not re.search(r"#[0-9a-fA-F]{3,6}", svg), "sparkline leaked a raw hex literal"


def test_task_ar_590_sparkline_excludes_non_numeric_values():
    """Non-numeric / non-finite data is excluded, never interpolated into the path."""
    svg = ui_design_assets.componentSparkline([1, "x", 2, None, 3, float("inf")])
    # 3 valid numeric points -> 3 coordinate pairs in the polyline.
    points = re.search(r'<polyline points="([^"]+)"', svg)
    assert points is not None
    assert len(points.group(1).split()) == 3
    assert "x" not in points.group(1)
    assert "inf" not in svg.lower()


def test_task_ar_590_sparkline_empty_for_too_few_points():
    """Fewer than two numeric points yields a safe empty span, not a broken SVG."""
    assert "sparkline--empty" in ui_design_assets.componentSparkline([])
    assert "sparkline--empty" in ui_design_assets.componentSparkline([7])
    assert "sparkline--empty" in ui_design_assets.componentSparkline(["only-text"])


def test_task_ar_590_sparkline_coordinates_within_viewbox():
    """Generated coordinates stay inside the SVG viewBox bounds."""
    width, height = 64, 24
    svg = ui_design_assets.componentSparkline([0, 100, 50, 75], width=width, height=height)
    coords = re.search(r'<polyline points="([^"]+)"', svg).group(1)
    for pair in coords.split():
        x, y = (float(v) for v in pair.split(","))
        assert 0 <= x <= width
        assert 0 <= y <= height


def _no_raw_color_literal(markup: str) -> bool:
    """True when markup carries no raw hex/rgb color literal (token-only tinting)."""
    if re.search(r"#[0-9a-fA-F]{3,6}\b", markup):
        return False
    if re.search(r"\brgba?\(", markup):
        return False
    return True


def test_task_ar_590_empty_state_illustration_is_accent_tinted_no_raw_color():
    """Empty-state illustration tints via the accent token with no raw color literal."""
    html = ui_design_assets.componentEmptyState("Nothing here", "Add something")
    assert "<svg" in html
    assert "var(--accent" in html or "var(--dv-sparkline" in html
    assert "currentColor" in html
    assert _no_raw_color_literal(html), html


def test_task_ar_590_error_state_illustration_uses_danger_token_no_raw_color():
    """Error-state illustration tints via the danger token with no raw color literal."""
    html = ui_design_assets.componentErrorState("Boom", "Retry")
    assert "<svg" in html
    assert "var(--danger" in html
    assert _no_raw_color_literal(html), html


def test_task_ar_590_loading_state_illustration_is_accent_tinted_no_raw_color():
    """Loading-state illustration tints via the accent token with no raw color literal."""
    html = ui_design_assets.componentLoadingState("Loading...")
    assert "<svg" in html
    assert "var(--accent" in html or "var(--dv-sparkline" in html
    assert "currentColor" in html
    assert _no_raw_color_literal(html), html


def test_task_ar_590_sparkline_classified_as_ui_component():
    """The sparkline component is registered in the assetization classes."""
    assert ui_design_assets.ASSETIZATION_CLASSES["componentSparkline"] == "ui_component"
