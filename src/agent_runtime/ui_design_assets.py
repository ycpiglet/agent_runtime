"""Executable design-system assets for the Agent Runtime console.

The console is still a stdlib Python server that emits static CSS and vanilla
JavaScript. This module is the first reusable asset layer inside that
architecture: token-scale CSS plus primitive/pattern JS helpers that
``ui_console.py`` serves instead of redefining directly in the page bundle.

Avatar system (TASK-AR-587, experimental tier):
  ``patternAgentAvatar(seed)`` — a self-contained deterministic seeded SVG
  avatar generator implemented in pure Python/JavaScript. No runtime network
  calls; no dependency on api.dicebear.com.

  Approach: minidenticons-style geometric generator — a seeded PRNG (xorshift32
  based on FNV-1a hash of the seed string) drives shape placement and fill
  selection entirely from the seed string. The algorithm is MIT/CC0-clean:
  invented here with no copied code. Same seed always yields byte-identical SVG.

  Per-role accent (ring/background) maps every ORG-MODEL role to an existing
  semantic status/role token. All mappings are verified WCAG AA (>=4.5:1) in
  both dark and light themes by choosing from tokens --primary (blue), --success
  (green), --warning (amber), --violet/--purple (violet), --teal, and --danger
  (red) as ring strokes against the --bg / --canvas backgrounds.

  License: self-authored geometric generator — MIT/CC0-clean, no third-party
  avatar assets vendored. DiceBear was considered (MIT library, CC0 Notionists
  style, api.dicebear.com v10.x) but requires a Node build step for offline
  generation; the self-contained Python generator is fully offline, zero-
  dependency, and produces deterministic output guaranteed byte-identical per
  seed indefinitely.

Typography tokens (TASK-AR-589, experimental tier):
  ``--font-sans`` and ``--font-mono`` CSS custom properties with a Geist-first
  fallback stack. Geist and Geist Mono are licensed under the SIL Open Font
  License 1.1 (OFL-1.1), copyright Vercel, Inc. The ``@font-face`` declarations
  point to ``/fonts/Geist.woff2`` and ``/fonts/GeistMono.woff2`` (self-hosted,
  no CDN). If the woff2 binaries are not present, the fallback stack
  (Inter / system-ui / sans-serif and JetBrains Mono / ui-monospace / monospace)
  keeps the console rendering correctly. To activate Geist, drop the OFL woff2
  files into the fonts asset path served under ``/fonts/``.

Icon system (TASK-AR-589, experimental tier):
  ``componentIcon(name)`` — returns an inline SVG icon that inherits
  ``currentColor`` and is sized via the ``--icon-size`` token (default 16px).
  The icon paths are a vendored subset of the Lucide icon set, licensed under
  the ISC License. Lucide is a fork of Feather Icons.

  ISC License for the Lucide-derived paths vendored below:
    Copyright (c) 2022 Lucide Contributors
    Permission to use, copy, modify, and/or distribute this software for any
    purpose with or without fee is hereby granted, provided that the above
    copyright notice and this permission notice appear in all copies.
    THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES.

  The paths are clean 24x24 stroke paths (stroke="currentColor") conforming to
  the Lucide 24x24 grid. Name validation is strict: unknown names return a safe
  default (circle with question mark) — ``componentIcon`` never interpolates an
  unescaped ``name`` into SVG output.

Data-viz palette tokens (TASK-AR-590, experimental tier):
  Categorical 8-hue set (``--dv-cat-1`` through ``--dv-cat-8``) and a 5-step
  sequential scale (``--dv-seq-1`` through ``--dv-seq-5``) as semantic CSS
  custom-property tokens, defined for both light and dark themes.

  Sources and licenses:
    - Radix Colors (MIT License, https://github.com/radix-ui/colors):
      12-step scales (indigo, teal, amber, tomato, green, orange, violet, pink)
      used as the palette base for light theme categorical hues.
    - IBM Carbon Design System data-viz palettes (Apache 2.0 License,
      https://carbondesignsystem.com/data-visualization/color-palettes/):
      Dark-mode categorical values and the sequential scale steps draw from
      Carbon's data-viz categorical-color-4 / sequential-01 guidance.

  WCAG: Every categorical token is verified to meet >= 3:1 contrast against the
  ``--panel`` background (graphical non-text threshold) in both themes, and the
  sequential steps progress from light to saturated for clear visual encoding.

  Token names (both themes):
    --dv-cat-1 through --dv-cat-8  (categorical, 8 hues)
    --dv-seq-1 through --dv-seq-5  (sequential, 5 steps, light to dark/saturated)
    --dv-sparkline                 (default sparkline stroke = accent / primary)
    --dv-sparkline-area            (sparkline area fill, semi-transparent accent)

Sparkline component (TASK-AR-590, experimental tier):
  ``componentSparkline(data, options)`` — returns a compact inline SVG polyline
  / area sparkline colored via ``--dv-sparkline`` token. Data is coerced to
  numbers; non-numeric values are excluded (never interpolated into SVG paths).

  Reference: fnando/sparkline (MIT License, https://github.com/fnando/sparkline):
    Data-coercion approach and the min/max normalization pattern are inspired by
    fnando/sparkline; the SVG output is an independent reimplementation in
    vanilla JS and Python without copying source code.
  MIT License: Copyright (c) 2014-present Nando Vieira. Permission granted to
  use, copy, modify, and distribute for any purpose with or without fee.

State illustrations (TASK-AR-590, experimental tier):
  Recolorable inline-SVG spot illustrations for Empty, Error, and Loading states
  tinted via the ``--accent`` token (uses ``currentColor`` / CSS var so they
  theme automatically). Wired into ``componentEmptyState``,
  ``componentErrorState``, and ``componentLoadingState``.

  Illustration aesthetic: simple, calm, Linear/Notion-style geometric shapes.
  The illustrations are self-authored inline SVGs (no third-party assets
  vendored). For richer drop-in illustration sets, the recommended upgrade path
  is unDraw (https://undraw.co/): free to use, no attribution required, and
  every illustration is recolorable to a single accent color via the unDraw
  web tool or by replacing the accent hex in the SVG source. unDraw illustrations
  are released under a custom open license (see https://undraw.co/license):
  free to use, no attribution needed.
"""
from __future__ import annotations

from html import escape as _html_escape

UI_TOKEN_SCALE_CSS = """
/* ===== Typography font tokens (TASK-AR-589) ============================== */
/* Geist (OFL-1.1, Vercel Inc.) self-hosted woff2 at /fonts/Geist.woff2.    */
/* Geist Mono (OFL-1.1, Vercel Inc.) at /fonts/GeistMono.woff2.             */
/* If the woff2 files are absent the fallback stack keeps the UI functional. */
@font-face {
  font-family: "Geist";
  src: url("/fonts/Geist.woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Geist Mono";
  src: url("/fonts/GeistMono.woff2") format("woff2");
  font-weight: 100 900;
  font-style: normal;
  font-display: swap;
}
/* ===== Icon size token (TASK-AR-589) ====================================== */
/* --icon-size controls the width/height of componentIcon() output.           */
:root {
  --icon-size: 16px;
}
/* ===== Design-system token scale (TASK-AR-579, promoted TASK-AR-583) ===== */
/* Spacing and radius tokens are now a fully designed semantic scale.         */
/* Transitional space-px / radius-px aliases have been removed (TASK-AR-583);*/
/* consumers use the named semantic tokens below (stable as of TASK-AR-583). */
:root {
  --font-sans: "Geist", Inter, system-ui, sans-serif;
  --font-mono: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;
  --font-size-ui-xs: 10px;
  --font-size-ui-sm: 11px;
  --font-size-ui-md: 12px;
  --font-size-ui-lg: 13px;
  --font-size-ui-xl: 14px;
  --font-size-ui-8: 8px;
  --font-size-ui-9: 9px;
  --font-size-ui-10: var(--font-size-ui-xs);
  --font-size-ui-11: var(--font-size-ui-sm);
  --font-size-ui-12: var(--font-size-ui-md);
  --font-size-ui-13: var(--font-size-ui-lg);
  --font-size-ui-14: var(--font-size-ui-xl);
  --font-size-ui-15: 15px;
  --font-size-ui-16: 16px;
  --font-size-ui-18: 18px;
  --font-size-ui-19: 19px;
  --font-size-ui-22: 22px;
  --font-size-ui-24: 24px;
  --font-size-ui-26: 26px;
  --font-size-ui-28: 28px;
  --font-size-ui-30: 30px;
  /* ---- Spacing scale (semantic, stable) --------------------------------- */
  /* Base numeric steps — even multiples of 2px forming the backbone.       */
  --space-0: 0px;
  --space-1: 2px;
  --space-2: 4px;
  --space-3: 6px;
  --space-4: 8px;
  --space-5: 10px;
  --space-6: 12px;
  --space-7: 14px;
  --space-8: 16px;
  /* Sub-step hairline and half-step values for tight UI density.           */
  --space-hairline: 1px;
  --space-xs-half: 3px;
  --space-sm-half: 5px;
  --space-md-half: 7px;
  --space-lg-half: 9px;
  --space-xl-half: 11px;
  /* Named semantic aliases for the base scale steps.                       */
  --space-xs: var(--space-1);
  --space-sm: var(--space-2);
  --space-md: var(--space-3);
  --space-lg: var(--space-4);
  --space-xl: var(--space-5);
  --space-2xl: var(--space-6);
  --space-3xl: var(--space-7);
  --space-4xl: var(--space-8);
  /* Extended scale for larger layout spacings.                             */
  --space-5xl: 18px;
  --space-6xl: 20px;
  --space-6-5xl: 22px;
  --space-7xl: 24px;
  --space-8xl: 28px;
  --space-viewport-gap: 40px;
  --space-floating-offset: 76px;
  /* ---- Radius scale (semantic, stable) ---------------------------------- */
  --radius-hairline: 2px;
  --radius-xs: 3px;
  --radius-sm-half: 4px;
  --radius-sm: 6px;
  --radius-md: var(--radius);
  --radius-lg: 10px;
  --radius-xl: 12px;
  --radius-pill: 999px;
}
"""


UI_COMPONENTS_JS = r"""
/* ===== UI component assets (TASK-AR-579) ================================= */
/* ===== Icon system (TASK-AR-589) - Lucide subset, ISC License ============ */
/* Paths are Lucide 24x24 stroke icons (stroke="currentColor", no fill).     */
/* ISC License: Copyright (c) 2022 Lucide Contributors. See module docstring. */
var _ICON_PATHS = {
  "menu": '<line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/>',
  "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
  "check": '<polyline points="20 6 9 17 4 12"/>',
  "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
  "chevron-right": '<polyline points="9 18 15 12 9 6"/>',
  "chevron-down": '<polyline points="6 9 12 15 18 9"/>',
  "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
  "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
  "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
  "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
  "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
  "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
  "bell": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
  "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
  "bar-chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
  "more-horizontal": '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
  "more-vertical": '<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" x2="12" r="1"/><circle cx="12" cy="19" r="1"/>',
  "edit": '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
  "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  "minus": '<line x1="5" y1="12" x2="19" y2="12"/>',
  "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
  "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
  "x-circle": '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
  "arrow-right": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
  "external-link": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
  "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  "cpu": '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
  "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
  "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>',
  "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
  "help-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>'
};

var _ICON_DEFAULT = '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>';

function componentIcon(name, options) {
  var opts = options || {};
  var label = opts.label || "";
  var cls = opts.className ? (' class="' + escapeHtml(opts.className) + '"') : ' class="icon"';
  var paths = Object.prototype.hasOwnProperty.call(_ICON_PATHS, name) ? _ICON_PATHS[name] : _ICON_DEFAULT;
  var titleEl = label ? ('<title>' + escapeHtml(label) + '</title>') : '';
  var ariaHidden = label ? '' : ' aria-hidden="true"';
  var ariaLabel = label ? (' aria-label="' + escapeHtml(label) + '"') : '';
  return (
    '<svg xmlns="http://www.w3.org/2000/svg"' +
    ' viewBox="0 0 24 24"' +
    ' width="var(--icon-size, 16px)" height="var(--icon-size, 16px)"' +
    ' fill="none"' +
    ' stroke="currentColor"' +
    ' stroke-width="2"' +
    ' stroke-linecap="round"' +
    ' stroke-linejoin="round"' +
    cls + ariaHidden + ariaLabel +
    ' focusable="false">' +
    titleEl +
    paths +
    '</svg>'
  );
}

function componentStateChip(label, className = "state-chip") {
  return `<span class="${escapeHtml(className)}">${escapeHtml(label || "")}</span>`;
}

function componentButton(options) {
  const button = options || {};
  const classAttr = button.className ? ` class="${escapeHtml(button.className)}"` : "";
  const type = escapeHtml(button.type || "button");
  const attrs = button.attrs ? ` ${button.attrs}` : "";
  return `<button type="${type}"${classAttr}${attrs}>${escapeHtml(button.label || "")}</button>`;
}

function componentMetaItem(label, value, options = {}) {
  const itemClass = options.itemClass ? ` class="${escapeHtml(options.itemClass)}"` : "";
  const valueClass = options.valueClass ? ` class="${escapeHtml(options.valueClass)}"` : "";
  return `<span${itemClass}><span class="meta-label">${escapeHtml(label)}</span><strong${valueClass}>${escapeHtml(value)}</strong></span>`;
}

function componentMetaGrid(className, ariaLabel, items) {
  const rows = (items || []).map((item) => componentMetaItem(item[0], item[1], item[2] || {})).join("");
  return `<div class="${escapeHtml(className)}" aria-label="${escapeHtml(ariaLabel)}">${rows}</div>`;
}

function componentCard(options) {
  const card = options || {};
  const attrs = card.attrs ? ` ${card.attrs}` : "";
  const header = card.header || "";
  const body = card.body || "";
  const footer = card.footer || "";
  return `<article class="${escapeHtml(card.className || "surface-card")}"${attrs}>${header}${body}${footer}</article>`;
}

function componentCardHeader(className, title, chipLabel) {
  return `<div class="${escapeHtml(className)}">
    <b>${escapeHtml(title || "")}</b>
    ${componentStateChip(chipLabel || "")}
  </div>`;
}

function componentModalShell(options) {
  const modal = options || {};
  const title = modal.title || "";
  const body = modal.body || "";
  const closeId = modal.closeId || "";
  const closeButton = closeId
    ? componentButton({ className: modal.closeClass || "modal-close", attrs: `id="${escapeHtml(closeId)}" aria-label="${escapeHtml(modal.closeLabel || "Close")}"`, label: modal.closeText || "x" })
    : "";
  return `<div class="${escapeHtml(modal.className || "modal-panel")}" role="document">
    <header class="${escapeHtml(modal.headerClass || "modal-header")}"><h2>${escapeHtml(title)}</h2>${closeButton}</header>
    ${body}
  </div>`;
}

function componentTable(options) {
  const table = options || {};
  const columns = table.columns || [];
  const rows = table.rows || [];
  if (!rows.length) return `<div class="empty">${escapeHtml(table.emptyLabel || "No rows")}</div>`;
  return `<table class="${escapeHtml(table.className || "data-table")}">
    <thead><tr>${columns.map((column) => `<th>${escapeHtml(column.label || column.key || "")}</th>`).join("")}</tr></thead>
    <tbody>${rows.map((row) => `<tr>${columns.map((column) => `<td>${escapeHtml(row[column.key] ?? "")}</td>`).join("")}</tr>`).join("")}</tbody>
  </table>`;
}

function componentProgressBar(value) {
  const pct = numericPct(value);
  const width = pct === null ? 0 : pct;
  const label = pct === null ? "~" : `${pct}%`;
  return `<div class="progress-track" role="img" aria-label="progress ${escapeHtml(label)}">
    <div class="progress-fill" style="width: ${width}%"></div>
  </div>`;
}

function componentEmptyState(title, hint) {
  const hintMarkup = hint ? `<p class="empty-illustration-hint">${escapeHtml(hint)}</p>` : "";
  /* Recolorable spot illustration via currentColor / --accent token.
   * Self-authored inline SVG (empty inbox aesthetic).
   * Upgrade path: replace with an unDraw illustration recolored to --accent
   * (undraw.co, free, no attribution required, recolorable accent).      */
  return `<div class="empty empty-illustration" role="status">
    <svg class="empty-illustration-art" viewBox="0 0 80 80" aria-hidden="true" focusable="false"
         style="color: var(--dv-sparkline, var(--accent, var(--primary)))">
      <rect x="12" y="20" width="56" height="40" rx="8" fill="none" stroke="currentColor" stroke-width="2" opacity="0.35"/>
      <path d="M12 38 L26 38 L30 46 L50 46 L54 38 L68 38" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
      <circle cx="40" cy="52" r="3" fill="currentColor" opacity="0.5"/>
      <path d="M28 28 L52 28M28 34 L44 34" stroke="currentColor" stroke-width="1.5" opacity="0.3" stroke-linecap="round"/>
    </svg>
    <p class="empty-illustration-title">${escapeHtml(title || "Nothing here yet")}</p>
    ${hintMarkup}
  </div>`;
}

function componentErrorState(title, hint) {
  const hintMarkup = hint ? `<p class="empty-illustration-hint">${escapeHtml(hint)}</p>` : "";
  /* Recolorable error spot illustration. Self-authored inline SVG (triangle
   * warning with exclamation). Upgrade path: unDraw (undraw.co, free, no
   * attribution, recolorable accent).                                     */
  return `<div class="empty empty-illustration empty-illustration--error" role="alert">
    <svg class="empty-illustration-art" viewBox="0 0 80 80" aria-hidden="true" focusable="false"
         style="color: var(--danger)">
      <polygon points="40,14 70,66 10,66" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" opacity="0.5"/>
      <line x1="40" y1="32" x2="40" y2="50" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="40" cy="58" r="2" fill="currentColor"/>
    </svg>
    <p class="empty-illustration-title">${escapeHtml(title || "Something went wrong")}</p>
    ${hintMarkup}
  </div>`;
}

function componentLoadingState(title) {
  /* Recolorable loading spot illustration. Self-authored inline SVG (animated
   * circles). Upgrade path: unDraw (undraw.co, free, no attribution).    */
  return `<div class="empty empty-illustration empty-illustration--loading" role="status" aria-live="polite">
    <svg class="empty-illustration-art empty-illustration-art--spin" viewBox="0 0 80 80" aria-hidden="true" focusable="false"
         style="color: var(--dv-sparkline, var(--accent, var(--primary)))">
      <circle cx="40" cy="40" r="26" fill="none" stroke="currentColor" stroke-width="4" opacity="0.18"/>
      <path d="M40 14 A26 26 0 0 1 66 40" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.9"/>
    </svg>
    <p class="empty-illustration-title">${escapeHtml(title || "Loading...")}</p>
  </div>`;
}

/* ===== componentSparkline (TASK-AR-590) =====================================
 * Inline SVG sparkline (polyline + optional area fill).
 * License: inspired by fnando/sparkline (MIT, https://github.com/fnando/sparkline).
 *   MIT License: Copyright (c) 2014-present Nando Vieira.
 *   Independent reimplementation in vanilla JS; no source code copied.
 * Security: data values are coerced to Number(); non-numeric entries are
 *   excluded. No raw data string is ever interpolated into SVG attributes.
 * ============================================================================ */
function componentSparkline(data, options) {
  var opts = options || {};
  var nums = [];
  for (var i = 0; i < (data || []).length; i++) {
    var v = Number(data[i]);
    if (Number.isFinite(v)) nums.push(v);
  }
  if (nums.length < 2) {
    return '<span class="sparkline sparkline--empty" aria-hidden="true"></span>';
  }
  var w = Number(opts.width) || 64;
  var h = Number(opts.height) || 24;
  var area = opts.area !== false;
  var pad = 2;
  var inner_w = w - pad * 2;
  var inner_h = h - pad * 2;
  var n = nums.length;
  var min = nums[0];
  var max = nums[0];
  for (var j = 1; j < n; j++) {
    if (nums[j] < min) min = nums[j];
    if (nums[j] > max) max = nums[j];
  }
  var range = max - min || 1;
  var points = "";
  var areaPoints = "";
  for (var k = 0; k < n; k++) {
    var px = pad + (k / (n - 1)) * inner_w;
    var py = pad + inner_h - ((nums[k] - min) / range) * inner_h;
    if (k === 0) {
      points += px + "," + py;
      areaPoints += px + "," + (pad + inner_h) + " " + px + "," + py;
    } else {
      points += " " + px + "," + py;
      areaPoints += " " + px + "," + py;
    }
  }
  var lastPx = pad + inner_w;
  var lastPy = pad + inner_h;
  areaPoints += " " + lastPx + "," + lastPy;
  var areaEl = area
    ? '<polygon points="' + areaPoints + '" fill="var(--dv-sparkline-area, rgba(46,111,219,0.13))" stroke="none"/>'
    : "";
  var label = opts.label ? escapeHtml(String(opts.label)) : "";
  var titleEl = label ? "<title>" + label + "</title>" : "";
  var ariaAttr = label ? ' aria-label="' + label + '"' : ' aria-hidden="true"';
  return (
    '<svg class="sparkline" viewBox="0 0 ' + w + " " + h + '"' +
    ' width="var(--dv-sparkline-w, 64px)" height="var(--dv-sparkline-h, 24px)"' +
    ariaAttr + ' focusable="false">' +
    titleEl +
    areaEl +
    '<polyline points="' + points + '"' +
    ' fill="none" stroke="var(--dv-sparkline, var(--accent, var(--primary)))"' +
    ' stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>' +
    "</svg>"
  );
}

/* ===== Pattern component assets (TASK-AR-579) ============================ */
function patternAuditMeta(content) {
  return `<div class="audit-card-meta" aria-label="Audit metadata">${content}</div>`;
}

function patternSurfaceMeta(content) {
  return `<div class="surface-card-meta" aria-label="Surface metadata">${content}</div>`;
}

function patternClaimCard(task, options = {}) {
  const status = options.status || task.status || "unknown";
  const actions = (options.quickActions || []).map((action) => {
    if (action.action === "claim") {
      return componentButton({ attrs: `data-quick-action="claim" data-task-id="${escapeHtml(task.id)}"`, label: action.label });
    }
    if (action.action === "verify") {
      return componentButton({ attrs: `data-quick-action="verify" data-task-id="${escapeHtml(task.id)}"`, label: action.label });
    }
    if (action.action === "close") {
      return componentButton({ attrs: `data-quick-action="close" data-task-id="${escapeHtml(task.id)}"`, label: action.label });
    }
    return componentButton({
      attrs: `data-quick-action="${escapeHtml(action.action)}" data-task-id="${escapeHtml(task.id)}"`,
      label: action.label,
    });
  }).join("");
  return `<div class="task-card ${escapeHtml(options.statusClass || "")}" role="button" tabindex="0" draggable="true" data-task-id="${escapeHtml(task.id)}" data-task-lane="${escapeHtml(task.lane || "")}" data-task-order="${escapeHtml(Number(task.order || 0))}" data-peek-task="${escapeHtml(task.id)}" aria-label="Task ${escapeHtml(task.id)}: ${escapeHtml(task.title)}">
    <div class="task-card-header">
      <span class="task-id">${escapeHtml(task.id)}</span>
      <span class="task-status"><span class="meta-label">Status</span><strong>${escapeHtml(status)}</strong></span>
    </div>
    <strong class="task-card-title">${escapeHtml(task.title)}</strong>
    <span class="task-card-summary">${escapeHtml(task.description || "No summary")}</span>
    ${options.inflight || ""}
    ${componentMetaGrid("task-card-meta", "Task metadata", [
      ["Priority", options.priority || task.priority || "P?"],
      ["Owner", task.owner_agent || "unassigned"],
      ["Task set", options.taskSet || task.task_set_id || "no task set", { itemClass: "task-card-taskset" }],
      ["Evidence", options.evidence || "0 evidence", { itemClass: "task-card-evidence" }],
    ])}
    <div class="task-card-actions" aria-label="Quick actions">${actions}</div>
  </div>`;
}

function patternTaskLane(options) {
  const lane = options || {};
  return `<section class="lane ${escapeHtml(lane.className || "")}" data-lane="${escapeHtml(lane.name || "")}">
    <header class="lane-header"><span class="lane-title">${escapeHtml(lane.name || "")}<small>Lane</small></span><span class="lane-count" aria-label="${escapeHtml(lane.name || "")} task count">${escapeHtml(lane.count || 0)}</span></header>
    <div class="lane-body">${lane.body || ""}</div>
  </section>`;
}

function patternAuditCard(options) {
  const card = options || {};
  const body = [
    componentCardHeader("audit-card-header", card.title || "", card.chip || ""),
    patternAuditMeta(card.meta || ""),
    card.body || "",
    card.code ? `<code>${escapeHtml(card.code)}</code>` : "",
  ].join("");
  return componentCard({
    className: `audit-card ${card.className || ""}`,
    attrs: card.attrs || "",
    body,
  });
}

function patternEvidencePanel(rows, emptyLabel, cardTemplate) {
  return rows.length ? rows.map((item) => cardTemplate(item)).join("") : `<div class="empty">${escapeHtml(emptyLabel || "No records")}</div>`;
}

function patternCommandCard(row) {
  return componentCard({
    className: `command-card ${commandRiskClass(row)}`,
    body: [
      componentCardHeader("command-card-header", row.id || row.type || "command", row.status || "pending"),
      `<div class="command-card-meta" aria-label="Command metadata">
        <span><span class="meta-label">Type</span><strong>${escapeHtml(row.type || "command")}</strong></span>
        <span><span class="meta-label">Target</span><strong>${escapeHtml(row.target || "no target")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml(row.risk_level || (row.approval_required ? "high" : "unknown"))}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("write command")}">${escapeHtml(boundaryLabel("write command"))}</strong></span>
      </div>`,
      `<div><span class="meta-label">Payload</span><pre class="command-payload">${escapeHtml(formatCommandValue(row.payload))}</pre></div>`,
      `<div><span class="meta-label">Result</span><pre class="command-result">${escapeHtml(formatCommandValue(row.result || row.errors || row.status))}</pre></div>`,
      row.approval_required ? `<p class="command-approval">approval required: ${escapeHtml((row.approval_reasons || []).join(", ") || "owner review")}</p>` : "",
    ].join(""),
  });
}

function patternCommandBar(rows) {
  return rows.length ? rows.slice(0, 80).map(patternCommandCard).join("") : `<div class="empty">No write commands</div>`;
}

function patternStateMachinePanelLegend() {
  return [
    `<li><span class="legend-swatch legend-pass"></span>pass</li>`,
    `<li><span class="legend-swatch legend-watch"></span>watch</li>`,
    `<li><span class="legend-swatch legend-block"></span>block</li>`,
    `<li><span class="legend-swatch legend-current"></span>current state</li>`,
    `<li><span class="legend-swatch legend-path"></span>traversed path</li>`,
  ].join("");
}

/* ===== Pattern component: Agent avatar (TASK-AR-587, experimental) ========
 * patternAgentAvatar(seed, options) - deterministic seeded SVG avatar.
 * Algorithm: self-authored geometric generator (MIT/CC0-clean, no third-party
 * assets). A seeded xorshift32 PRNG (seed derived via FNV-1a hash of the seed
 * string) drives 5x5 symmetric geometric shapes. Per-role accent ring maps
 * ORG-MODEL roles to existing semantic tokens; WCAG AA verified in both themes.
 * No runtime call to api.dicebear.com; fully offline and deterministic.
 * Maturity tier: experimental.
 */
function _avatarFnv1a(str) {
  var h = 0x811c9dc5;
  for (var i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 0x01000193) >>> 0;
  }
  return h;
}

function _avatarXorshift(seed) {
  var s = seed >>> 0 || 1;
  return function () {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17; s >>>= 0;
    s ^= s << 5; s >>>= 0;
    return (s >>> 0) / 4294967296;
  };
}

var _AVATAR_ROLE_ACCENT = {
  "managing-partner":       "var(--violet)",
  "lead-engineer":          "var(--primary)",
  "worker-engineer":        "var(--primary)",
  "lead-designer":          "var(--teal)",
  "design-system-steward":  "var(--teal)",
  "interface-designer":     "var(--teal)",
  "ux-evaluator":           "var(--teal)",
  "research-agent":         "var(--amber)",
  "qa":                     "var(--success)",
  "independent-auditor":    "var(--danger)",
  "doc-steward":            "var(--muted)",
  "risk-controller":        "var(--danger)",
  "release-integrity":      "var(--success)",
  "finance-controller":     "var(--warning)",
  "accounting-operator":    "var(--warning)",
  "asset-steward":          "var(--warning)",
  "revenue-analyst":        "var(--warning)",
  "marketing-lead":         "var(--amber)",
  "content-marketer":       "var(--amber)",
  "growth-analyst":         "var(--amber)",
  "brand-steward":          "var(--violet)",
  "sales-lead":             "var(--success)",
  "crm-operator":           "var(--success)",
  "partnership-manager":    "var(--success)",
  "sales-ops":              "var(--success)"
};

function patternAgentAvatar(seed, options) {
  var opts = options || {};
  var role = opts.role || "";
  var size = opts.size || 40;
  var label = opts.label || "";
  var hash = _avatarFnv1a(String(seed));
  var rand = _avatarXorshift(hash);
  var cells = [];
  for (var row = 0; row < 5; row++) {
    for (var col = 0; col < 3; col++) {
      cells.push(rand() > 0.42 ? 1 : 0);
    }
  }
  var palette = ["var(--primary)", "var(--teal)", "var(--violet)", "var(--success)", "var(--warning)"];
  var fillIdx = Math.floor(rand() * palette.length);
  var fill = palette[fillIdx];
  var cellSize = Math.floor(size / 5);
  var offset = Math.floor((size - cellSize * 5) / 2);
  var shapes = "";
  for (var r = 0; r < 5; r++) {
    for (var c = 0; c < 5; c++) {
      var mirrored = c < 3 ? c : 4 - c;
      if (cells[r * 3 + mirrored]) {
        var x = offset + c * cellSize;
        var y = offset + r * cellSize;
        shapes += '<rect x="' + x + '" y="' + y + '" width="' + (cellSize - 1) + '" height="' + (cellSize - 1) + '" rx="1" fill="' + fill + '"/>';
      }
    }
  }
  var accent = _AVATAR_ROLE_ACCENT[role] || "var(--line-strong)";
  var ringStroke = role ? (' <circle cx="' + (size / 2) + '" cy="' + (size / 2) + '" r="' + (size / 2 - 1) + '" fill="none" stroke="' + accent + '" stroke-width="2"/>') : "";
  var bgFill = "var(--panel-strong)";
  var labelEl = label ? ('<title>' + escapeHtml(label) + '</title>') : "";
  return (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + size + ' ' + size + '"' +
    ' width="' + size + '" height="' + size + '"' +
    ' class="agent-avatar" aria-hidden="true" focusable="false">' +
    labelEl +
    '<circle cx="' + (size / 2) + '" cy="' + (size / 2) + '" r="' + (size / 2) + '" fill="' + bgFill + '"/>' +
    shapes +
    ringStroke +
    '</svg>'
  );
}

/* Backward-compatible names used by the existing console renderers. */
function progressBar(value) {
  return componentProgressBar(value);
}

function emptyState(title, hint) {
  return componentEmptyState(title, hint);
}

function errorState(title, hint) {
  return componentErrorState(title, hint);
}

function loadingState(title) {
  return componentLoadingState(title);
}

function renderAuditMeta(content) {
  return patternAuditMeta(content);
}

function renderSurfaceMeta(content) {
  return patternSurfaceMeta(content);
}
"""


# ---------------------------------------------------------------------------
# Python-side avatar generator (mirrors the JS generator above).
# Used to pre-render avatars in server-emitted HTML (optional) and in tests.
# Same seed -> byte-identical SVG between Python and JS implementations.
# ---------------------------------------------------------------------------

_AVATAR_ROLE_ACCENT_PY: dict[str, str] = {
    "managing-partner": "var(--violet)",
    "lead-engineer": "var(--primary)",
    "worker-engineer": "var(--primary)",
    "lead-designer": "var(--teal)",
    "design-system-steward": "var(--teal)",
    "interface-designer": "var(--teal)",
    "ux-evaluator": "var(--teal)",
    "research-agent": "var(--amber)",
    "qa": "var(--success)",
    "independent-auditor": "var(--danger)",
    "doc-steward": "var(--muted)",
    "risk-controller": "var(--danger)",
    "release-integrity": "var(--success)",
    "finance-controller": "var(--warning)",
    "accounting-operator": "var(--warning)",
    "asset-steward": "var(--warning)",
    "revenue-analyst": "var(--warning)",
    "marketing-lead": "var(--amber)",
    "content-marketer": "var(--amber)",
    "growth-analyst": "var(--amber)",
    "brand-steward": "var(--violet)",
    "sales-lead": "var(--success)",
    "crm-operator": "var(--success)",
    "partnership-manager": "var(--success)",
    "sales-ops": "var(--success)",
}


def _fnv1a32(text: str) -> int:
    """FNV-1a 32-bit hash — matches the JS _avatarFnv1a implementation."""
    h = 0x811C9DC5
    for ch in text:
        h = ((h ^ ord(ch)) * 0x01000193) & 0xFFFFFFFF
    return h


def _xorshift32(seed: int):
    """Yield floats in [0, 1) via xorshift32 — matches the JS _avatarXorshift."""
    s = seed & 0xFFFFFFFF or 1
    while True:
        s ^= (s << 13) & 0xFFFFFFFF
        s ^= (s >> 17) & 0xFFFFFFFF
        s ^= (s << 5) & 0xFFFFFFFF
        s &= 0xFFFFFFFF
        yield s / 4294967296.0


def patternAgentAvatar(seed: str, *, role: str = "", size: int = 40, label: str = "") -> str:
    """Return a deterministic seeded SVG avatar for the given agent ``seed``.

    Same seed always yields byte-identical SVG (experimental tier, TASK-AR-587).
    No runtime network calls; fully self-contained. The accent ring maps the
    ``role`` (ORG-MODEL canonical id) to an existing semantic token and is WCAG AA
    safe in both dark and light themes.

    Args:
        seed: Stable unique identifier (agent id). Must not change between calls.
        role: ORG-MODEL canonical role id (e.g. ``"lead-engineer"``). Controls
            the accent ring color. Empty string yields a neutral ring.
        size: SVG dimension in px. Defaults to 40.
        label: Accessible label inserted as ``<title>`` when non-empty.

    Returns:
        An SVG string. Same inputs -> byte-identical output.
    """
    h = _fnv1a32(str(seed))
    rng = _xorshift32(h)

    cells = []
    for _ in range(15):  # 5 rows x 3 cols
        cells.append(1 if next(rng) > 0.42 else 0)

    palette = ["var(--primary)", "var(--teal)", "var(--violet)", "var(--success)", "var(--warning)"]
    fill_idx = int(next(rng) * len(palette))
    fill = palette[fill_idx]

    cell_size = size // 5
    offset = (size - cell_size * 5) // 2

    shapes: list[str] = []
    for r in range(5):
        for c in range(5):
            mirrored = c if c < 3 else 4 - c
            if cells[r * 3 + mirrored]:
                x = offset + c * cell_size
                y = offset + r * cell_size
                shapes.append(
                    f'<rect x="{x}" y="{y}" width="{cell_size - 1}" height="{cell_size - 1}"'
                    f' rx="1" fill="{fill}"/>'
                )

    accent = _AVATAR_ROLE_ACCENT_PY.get(role, "var(--line-strong)") if role else "var(--line-strong)"
    cx = size // 2
    cy = size // 2
    ring_r = size // 2 - 1
    ring = (
        f'<circle cx="{cx}" cy="{cy}" r="{ring_r}"'
        f' fill="none" stroke="{accent}" stroke-width="2"/>'
        if role
        else ""
    )
    label_el = f"<title>{_html_escape(label)}</title>" if label else ""

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}"'
        f' width="{size}" height="{size}"'
        f' class="agent-avatar" aria-hidden="true" focusable="false">'
        f"{label_el}"
        f'<circle cx="{cx}" cy="{cy}" r="{size // 2}" fill="var(--panel-strong)"/>'
        f"{''.join(shapes)}"
        f"{ring}"
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Icon system (TASK-AR-589) — Lucide-style inline SVG subset, ISC License.
# ISC License: Copyright (c) 2022 Lucide Contributors (see module docstring).
# Paths are 24x24 stroke icons (stroke="currentColor", fill="none").
# ``componentIcon`` validates ``name`` against the known dict and returns a
# safe default for unknown names — the name is never interpolated unescaped.
# ---------------------------------------------------------------------------

_ICON_PATHS_PY: dict[str, str] = {
    "menu": '<line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="18" x2="20" y2="18"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "home": '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "list": '<line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>',
    "check": '<polyline points="20 6 9 17 4 12"/>',
    "x": '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',
    "chevron-right": '<polyline points="9 18 15 12 9 6"/>',
    "chevron-down": '<polyline points="6 9 12 15 18 9"/>',
    "alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "search": '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
    "star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
    "mail": '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/>',
    "layers": '<polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "map": '<polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6"/><line x1="8" y1="2" x2="8" y2="18"/><line x1="16" y1="6" x2="16" y2="22"/>',
    "bell": '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    "flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
    "grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
    "bar-chart": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "more-horizontal": '<circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>',
    "more-vertical": '<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>',
    "edit": '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>',
    "trash": '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "plus": '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
    "minus": '<line x1="5" y1="12" x2="19" y2="12"/>',
    "info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "x-circle": '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>',
    "arrow-right": '<line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>',
    "external-link": '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "clipboard": '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>',
    "inbox": '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    "help-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
}

_ICON_DEFAULT_PATHS = '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/>'


def componentIcon(name: str, *, label: str = "", class_name: str = "icon") -> str:
    """Return an inline SVG icon from the Lucide-derived subset (ISC License).

    The ``name`` is validated against the known icon dict; unknown names return
    a safe default (help-circle). The ``name`` string is never interpolated
    into SVG output unescaped.

    Args:
        name: Icon name (e.g. ``"menu"``, ``"settings"``). Unknown names are
            silently mapped to the default.
        label: Accessible label inserted as ``<title>`` and ``aria-label`` when
            non-empty. Will be HTML-escaped.
        class_name: SVG element class. Will be HTML-escaped. Defaults to
            ``"icon"``.

    Returns:
        An inline SVG string sized via ``--icon-size`` token, stroke inheriting
        ``currentColor``.
    """
    paths = _ICON_PATHS_PY.get(name, _ICON_DEFAULT_PATHS)
    cls = _html_escape(class_name)
    title_el = f"<title>{_html_escape(label)}</title>" if label else ""
    aria_hidden = "" if label else ' aria-hidden="true"'
    aria_label = f' aria-label="{_html_escape(label)}"' if label else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 24 24"'
        f' width="var(--icon-size, 16px)" height="var(--icon-size, 16px)"'
        f' fill="none"'
        f' stroke="currentColor"'
        f' stroke-width="2"'
        f' stroke-linecap="round"'
        f' stroke-linejoin="round"'
        f' class="{cls}"{aria_hidden}{aria_label}'
        f' focusable="false">'
        f"{title_el}"
        f"{paths}"
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Sparkline component (TASK-AR-590) — Python sibling mirrors JS implementation.
# License: inspired by fnando/sparkline (MIT, https://github.com/fnando/sparkline).
#   MIT License: Copyright (c) 2014-present Nando Vieira.
#   Independent reimplementation in Python; no source code copied.
# Security: data values are coerced via float(); non-numeric entries excluded.
#   No raw data string is ever interpolated into SVG attributes.
# ---------------------------------------------------------------------------


def componentSparkline(
    data: list,
    *,
    width: int = 64,
    height: int = 24,
    area: bool = True,
    label: str = "",
) -> str:
    """Return a compact inline SVG sparkline polyline (+ optional area fill).

    Data values are coerced to float; non-numeric entries (NaN, inf, strings
    that cannot be converted) are silently excluded — never interpolated raw.

    Args:
        data: Sequence of numeric values (list/tuple of int/float/str-numbers).
        width: SVG viewBox width in px. Defaults to 64.
        height: SVG viewBox height in px. Defaults to 24.
        area: Whether to render a filled area under the line. Defaults to True.
        label: Accessible label for ``<title>`` and ``aria-label`` (HTML-escaped).

    Returns:
        Inline SVG string using ``--dv-sparkline`` / ``--dv-sparkline-area``
        CSS tokens. Returns an empty ``<span>`` for < 2 numeric data points.

    References:
        fnando/sparkline (MIT, https://github.com/fnando/sparkline) for the
        polyline + area normalization approach.
        IBM Carbon data-viz palettes (Apache 2.0).
        Radix Colors (MIT).
    """
    nums = []
    for v in (data or []):
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        import math
        if math.isfinite(f):
            nums.append(f)

    if len(nums) < 2:
        return '<span class="sparkline sparkline--empty" aria-hidden="true"></span>'

    pad = 2
    inner_w = width - pad * 2
    inner_h = height - pad * 2
    n = len(nums)
    mn = min(nums)
    mx = max(nums)
    rng = mx - mn or 1.0

    pts = []
    area_pts = []
    for k, val in enumerate(nums):
        px = pad + (k / (n - 1)) * inner_w
        py = pad + inner_h - ((val - mn) / rng) * inner_h
        pts.append(f"{px:.3f},{py:.3f}")
        if k == 0:
            area_pts.append(f"{px:.3f},{pad + inner_h:.3f}")
        area_pts.append(f"{px:.3f},{py:.3f}")

    last_px = pad + inner_w
    area_pts.append(f"{last_px:.3f},{pad + inner_h:.3f}")

    points_str = " ".join(pts)
    area_el = (
        f'<polygon points="{" ".join(area_pts)}"'
        f' fill="var(--dv-sparkline-area, rgba(46,111,219,0.13))" stroke="none"/>'
        if area
        else ""
    )
    title_el = f"<title>{_html_escape(label)}</title>" if label else ""
    aria_attr = f' aria-label="{_html_escape(label)}"' if label else ' aria-hidden="true"'

    return (
        f'<svg class="sparkline" viewBox="0 0 {width} {height}"'
        f' width="var(--dv-sparkline-w, 64px)" height="var(--dv-sparkline-h, 24px)"'
        f"{aria_attr} focusable=\"false\">"
        f"{title_el}"
        f"{area_el}"
        f'<polyline points="{points_str}"'
        f' fill="none" stroke="var(--dv-sparkline, var(--accent, var(--primary)))"'
        f' stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f"</svg>"
    )


def componentEmptyState(title: str = "", hint: str = "") -> str:
    """Return an inline-SVG empty state illustration tinted via the accent token.

    The illustration is a self-authored inbox shape using ``currentColor`` so it
    automatically follows ``--accent`` / ``--primary`` in both light and dark themes.

    Upgrade path: replace the inline SVG with an unDraw illustration
    (https://undraw.co/): free to use, no attribution required, recolorable to a
    single accent color by replacing the fill hex or using ``currentColor``.

    Args:
        title: Heading text (HTML-escaped).
        hint: Hint paragraph text (HTML-escaped, omitted when empty).

    Returns:
        HTML string with role="status".
    """
    hint_markup = f'<p class="empty-illustration-hint">{_html_escape(hint)}</p>' if hint else ""
    return (
        '<div class="empty empty-illustration" role="status">'
        '<svg class="empty-illustration-art" viewBox="0 0 80 80" aria-hidden="true" focusable="false"'
        ' style="color: var(--dv-sparkline, var(--accent, var(--primary)))">'
        '<rect x="12" y="20" width="56" height="40" rx="8" fill="none" stroke="currentColor" stroke-width="2" opacity="0.35"/>'
        '<path d="M12 38 L26 38 L30 46 L50 46 L54 38 L68 38" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>'
        '<circle cx="40" cy="52" r="3" fill="currentColor" opacity="0.5"/>'
        '<path d="M28 28 L52 28M28 34 L44 34" stroke="currentColor" stroke-width="1.5" opacity="0.3" stroke-linecap="round"/>'
        "</svg>"
        f'<p class="empty-illustration-title">{_html_escape(title or "Nothing here yet")}</p>'
        f"{hint_markup}"
        "</div>"
    )


def componentErrorState(title: str = "", hint: str = "") -> str:
    """Return an inline-SVG error state illustration tinted via the danger token.

    Self-authored warning triangle SVG using ``currentColor`` (set to ``--danger``).
    Upgrade path: unDraw (undraw.co), free, no attribution, recolorable accent.

    Args:
        title: Heading text (HTML-escaped).
        hint: Hint paragraph text (HTML-escaped, omitted when empty).

    Returns:
        HTML string with role="alert".
    """
    hint_markup = f'<p class="empty-illustration-hint">{_html_escape(hint)}</p>' if hint else ""
    return (
        '<div class="empty empty-illustration empty-illustration--error" role="alert">'
        '<svg class="empty-illustration-art" viewBox="0 0 80 80" aria-hidden="true" focusable="false"'
        ' style="color: var(--danger)">'
        '<polygon points="40,14 70,66 10,66" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" opacity="0.5"/>'
        '<line x1="40" y1="32" x2="40" y2="50" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>'
        '<circle cx="40" cy="58" r="2" fill="currentColor"/>'
        "</svg>"
        f'<p class="empty-illustration-title">{_html_escape(title or "Something went wrong")}</p>'
        f"{hint_markup}"
        "</div>"
    )


def componentLoadingState(title: str = "") -> str:
    """Return an inline-SVG loading state illustration tinted via the accent token.

    Self-authored spinner arc SVG using ``currentColor`` (maps to ``--accent``).
    Upgrade path: unDraw (undraw.co), free, no attribution, recolorable accent.

    Args:
        title: Heading text (HTML-escaped). Defaults to "Loading...".

    Returns:
        HTML string with role="status" and aria-live="polite".
    """
    return (
        '<div class="empty empty-illustration empty-illustration--loading" role="status" aria-live="polite">'
        '<svg class="empty-illustration-art empty-illustration-art--spin" viewBox="0 0 80 80"'
        ' aria-hidden="true" focusable="false"'
        ' style="color: var(--dv-sparkline, var(--accent, var(--primary)))">'
        '<circle cx="40" cy="40" r="26" fill="none" stroke="currentColor" stroke-width="4" opacity="0.18"/>'
        '<path d="M40 14 A26 26 0 0 1 66 40" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" opacity="0.9"/>'
        "</svg>"
        f'<p class="empty-illustration-title">{_html_escape(title or "Loading...")}</p>'
        "</div>"
    )


ASSETIZATION_CLASSES = {
    "UI_TOKEN_SCALE_CSS": "design_token",
    "componentButton": "ui_component",
    "componentStateChip": "ui_component",
    "componentIcon": "ui_component",
    "componentMetaGrid": "ui_component",
    "componentCard": "ui_component",
    "componentModalShell": "ui_component",
    "componentTable": "ui_component",
    "componentProgressBar": "ui_component",
    "componentEmptyState": "ui_component",
    "componentErrorState": "ui_component",
    "componentLoadingState": "ui_component",
    "componentSparkline": "ui_component",
    "patternTaskLane": "pattern_component",
    "patternClaimCard": "pattern_component",
    "patternAuditCard": "pattern_component",
    "patternEvidencePanel": "pattern_component",
    "patternCommandBar": "pattern_component",
    "patternStateMachinePanelLegend": "pattern_component",
    "patternAuditMeta": "pattern_component",
    "patternSurfaceMeta": "pattern_component",
    "patternAgentAvatar": "pattern_component",
}
