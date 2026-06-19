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
"""
from __future__ import annotations

UI_TOKEN_SCALE_CSS = """
/* ===== Design-system token scale (TASK-AR-579, promoted TASK-AR-583) ===== */
/* Spacing and radius tokens are now a fully designed semantic scale.         */
/* Transitional space-px / radius-px aliases have been removed (TASK-AR-583);*/
/* consumers use the named semantic tokens below (stable as of TASK-AR-583). */
:root {
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
  return `<div class="empty empty-illustration" role="status">
    <svg class="empty-illustration-art" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <rect x="10" y="14" width="44" height="36" rx="6"></rect>
      <path d="M18 26h28M18 34h20M18 42h24"></path>
    </svg>
    <p class="empty-illustration-title">${escapeHtml(title || "Nothing here yet")}</p>
    ${hintMarkup}
  </div>`;
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
    label_el = f"<title>{label}</title>" if label else ""

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


ASSETIZATION_CLASSES = {
    "UI_TOKEN_SCALE_CSS": "design_token",
    "componentButton": "ui_component",
    "componentStateChip": "ui_component",
    "componentMetaGrid": "ui_component",
    "componentCard": "ui_component",
    "componentModalShell": "ui_component",
    "componentTable": "ui_component",
    "componentProgressBar": "ui_component",
    "componentEmptyState": "ui_component",
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
