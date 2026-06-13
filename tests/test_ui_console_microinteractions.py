"""TASK-AR-340: microinteractions + gamification policy layer.

These tests pin the acceptance-critical behaviour:

* Animations are gated BOTH by ``prefers-reduced-motion`` AND a global
  ``data-motion="off"`` toggle (calm serious mode is the default).
* Gamification (confetti / XP emphasis / streak / sound) is OPT-IN and leaves no
  residue when off (default ``data-gamify="off"``, sound default off).
* The experience-settings policy persists via ``localStorage``.
* Confetti / celebration colors are tokens (no raw hex).
* Onboarding tour, illustrated empty state, and contextual help are present.
"""

import re
import shutil
import subprocess
from pathlib import Path

from agent_runtime import ui_console


def _css(tmp_path: Path) -> str:
    return ui_console.build_response("/app.css", tmp_path).body.decode("utf-8")


def _js(tmp_path: Path) -> str:
    return ui_console.build_response("/app.js", tmp_path).body.decode("utf-8")


def _html(tmp_path: Path) -> str:
    return ui_console.build_response("/", tmp_path).body.decode("utf-8")


# ----- Policy attributes + no-flash bootstrap -----


def test_policy_attributes_default_to_calm_serious_mode(tmp_path):
    html = _html(tmp_path)
    # The no-flash bootstrap applies the policy attributes before first paint and
    # defaults to calm-serious: motion on (yields to reduced-motion), gamify off.
    assert 'setAttribute("data-motion"' in html
    assert 'setAttribute("data-gamify"' in html
    assert 'setAttribute("data-quest-mode"' in html
    # Gamify + quest default to off in the bootstrap.
    assert 'var gamify = "off";' in html
    assert 'var quest = "off";' in html
    # Bootstrap honors prefers-reduced-motion when no explicit choice is stored.
    assert 'matchMedia("(prefers-reduced-motion: reduce)")' in html


def test_keyframes_and_animation_classes_present(tmp_path):
    css = _css(tmp_path)
    for keyframe in [
        "@keyframes ar-fade-in-up",
        "@keyframes ar-pop-in",
        "@keyframes ar-skeleton-shimmer",
        "@keyframes ar-confetti-fall",
        "@keyframes ar-xp-bump",
    ]:
        assert keyframe in css, keyframe
    for cls in [".ar-anim-enter", ".ar-anim-pop", ".ar-skeleton", ".ar-dragging", ".is-optimistic"]:
        assert cls in css, cls


# ----- ACCESSIBILITY (acceptance-critical): dual gating -----


def test_animations_disabled_under_prefers_reduced_motion(tmp_path):
    css = _css(tmp_path)
    assert "@media (prefers-reduced-motion: reduce)" in css
    # Within the reduced-motion block, animations/transitions are neutralized.
    block = css.split("@media (prefers-reduced-motion: reduce)", 1)[1]
    assert "animation-duration: 0.001ms !important;" in block
    assert "transition-duration: 0.001ms !important;" in block
    assert "animation: none !important;" in block


def test_animations_disabled_under_global_motion_off_toggle(tmp_path):
    css = _css(tmp_path)
    # The global off toggle keys off data-motion="off" and kills animations.
    assert ':root[data-motion="off"]' in css
    off_rules = [line for line in css.splitlines() if 'data-motion="off"' in line]
    assert off_rules, "expected data-motion=off gating rules"
    # The off block must neutralize both animation and transition.
    assert ':root[data-motion="off"] .ar-anim-enter' in css
    assert "animation: none !important;" in css
    # Confetti animates ONLY when BOTH gamify and motion are on.
    assert ':root[data-gamify="on"][data-motion="on"] .confetti-piece' in css


# ----- Gamification opt-in (default off, no residue) -----


def test_gamification_is_opt_in_and_gated(tmp_path):
    css = _css(tmp_path)
    js = _js(tmp_path)
    # Confetti only animates under data-gamify="on" (default is off -> no residue).
    assert ':root[data-gamify="on"]' in css
    # The celebrate() helper guards on gamify + motion before doing anything.
    celebrate = js.split("function celebrate(", 1)[1].split("\n}", 1)[0]
    assert "if (!gamifyEnabled() || !motionEnabled()) return;" in celebrate
    # XP/streak emphasis is gated behind the gamify attribute.
    assert ':root[data-gamify="on"] .agent-character-streak' in css


def test_completion_sound_default_off(tmp_path):
    css = _css(tmp_path)
    js = _js(tmp_path)
    html = _html(tmp_path)
    # No "checked" on the sound toggle (default off); gamify also unchecked.
    assert '<input id="setting-sound" type="checkbox">' in html
    assert '<input id="setting-gamify" type="checkbox">' in html
    # Motion defaults checked (on) but is reduced-motion aware.
    assert '<input id="setting-motion" type="checkbox" checked>' in html
    # playCompletionSound() returns early unless explicitly enabled.
    sound = js.split("function playCompletionSound(", 1)[1].split("\n}", 1)[0]
    assert "if (!soundEnabled()) return;" in sound
    assert 'SOUND_KEY = "agent-runtime-completion-sound"' in js
    # CSS keeps streak hidden until gamify is on (no residue).
    assert ".agent-character-streak {" in css


# ----- Settings persistence (localStorage) -----


def test_settings_persist_via_localstorage(tmp_path):
    js = _js(tmp_path)
    assert 'MOTION_KEY = "agent-runtime-motion"' in js
    assert 'GAMIFY_KEY = "agent-runtime-gamify"' in js
    assert 'QUEST_KEY = "agent-runtime-quest-mode"' in js
    # writePref persists to localStorage; the change handlers call it.
    assert "window.localStorage.setItem(key, value)" in js
    assert "writePref(MOTION_KEY," in js
    assert "writePref(GAMIFY_KEY," in js
    assert "writePref(SOUND_KEY," in js


# ----- Confetti colors are tokens (no raw hex) -----


def test_confetti_colors_are_tokens_not_raw_hex(tmp_path):
    css = _css(tmp_path)
    # Confetti tones are derived from existing semantic tokens.
    for token in ["--confetti-1", "--confetti-2", "--confetti-3", "--confetti-4", "--confetti-5"]:
        assert token in css, token
    # The confetti-piece tone rules must reference var(--token), never raw hex.
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in css.splitlines():
        if ".confetti-piece" in line and "tone-" in line:
            assert not hex_pattern.search(line), line
            assert not rgba_pattern.search(line), line
            assert "var(--confetti" in line
    # The JS confetti generator never injects raw colors (only token classes).
    celebrate = js = _js(tmp_path).split("function celebrate(", 1)[1].split("\n}", 1)[0]
    assert "#" not in celebrate.replace("--confetti-dx", "")  # no hex colors
    assert "rgb" not in celebrate
    assert "confetti-piece tone-" in celebrate


# ----- Onboarding / empty-state / contextual help present -----


def test_onboarding_tour_present(tmp_path):
    html = _html(tmp_path)
    js = _js(tmp_path)
    assert 'id="onboarding-tour"' in html
    assert 'id="onboarding-tour-next"' in html
    assert "function startOnboardingTour" in js
    # First-run gating persists a "seen" flag in localStorage.
    assert 'TOUR_KEY = "agent-runtime-tour-seen"' in js


def test_empty_state_illustration_present(tmp_path):
    css = _css(tmp_path)
    js = _js(tmp_path)
    assert "function emptyState(" in js
    assert ".empty-illustration" in css
    assert ".empty-illustration-art" in css
    # The illustration SVG uses tokenized fill/stroke (no raw hex).
    art_rules = css.split(".empty-illustration-art {", 1)[1].split("}", 1)[0]
    assert "var(--" in art_rules
    assert "#" not in art_rules


def test_contextual_help_present(tmp_path):
    html = _html(tmp_path)
    js = _js(tmp_path)
    assert 'id="contextual-help"' in html
    assert "function showContextualHelp" in js
    assert "function initContextualHelp" in js


def test_experience_settings_control_and_dialog_served(tmp_path):
    html = _html(tmp_path)
    js = _js(tmp_path)
    assert 'id="experience-settings-toggle"' in html
    assert 'id="experience-settings"' in html
    assert 'role="dialog"' in html.split('id="experience-settings"', 1)[1][:200]
    assert "function initExperienceSettings" in js
    assert "function applyExperiencePolicy" in js


def test_quest_mode_terminology_swap_present(tmp_path):
    html = _html(tmp_path)
    css = _css(tmp_path)
    js = _js(tmp_path)
    # Static label swap via data-default-label / data-quest-label.
    assert "data-default-label" in html
    assert "data-quest-label" in html
    assert ":root:not([data-quest-mode=\"on\"]) [data-quest-label]" in css
    assert ':root[data-quest-mode="on"] [data-default-label]' in css
    # Dynamic JS labels go through questTerm().
    assert "function questTerm(" in js


# ----- Tokenization-safe: new CSS adds no raw hex outside token blocks -----


def test_microinteraction_css_uses_tokens_not_raw_hex(tmp_path):
    css = _css(tmp_path)
    # Scan only the TASK-AR-340 section (after the deep-link highlight marker).
    marker = "TASK-AR-340: Microinteractions + gamification policy layer."
    assert marker in css
    section = css.split(marker, 1)[1]
    hex_pattern = re.compile(r"#[0-9a-fA-F]{3,8}\b")
    rgba_pattern = re.compile(r"rgba?\(")
    for line in section.splitlines():
        assert not hex_pattern.search(line), f"raw hex in AR-340 CSS: {line.strip()}"
        assert not rgba_pattern.search(line), f"raw rgba in AR-340 CSS: {line.strip()}"


# ----- ASCII-only + node --check (cp949 node-check guard) -----


def test_microinteraction_js_ascii_only_and_node_check(tmp_path):
    js = _js(tmp_path)
    start = js.index("// --- Experience policy")
    end = js.index("const lanes =", start)
    block = js[start:end]
    non_ascii = [ch for ch in block if ord(ch) > 127]
    assert not non_ascii, f"AR-340 JS must be ASCII-only, found: {non_ascii[:5]}"

    if shutil.which("node") is None:
        import pytest

        pytest.skip("node not available")
    proc = subprocess.run(["node", "--check", "-"], input=js, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
