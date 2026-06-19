"""Executable design-system assets for the Agent Runtime console.

The console is still a stdlib Python server that emits static CSS and vanilla
JavaScript. This module is the first reusable asset layer inside that
architecture: token-scale CSS plus primitive/pattern JS helpers that
``ui_console.py`` serves instead of redefining directly in the page bundle.
"""
from __future__ import annotations

UI_TOKEN_SCALE_CSS = """
/* ===== Design-system token scale (TASK-AR-579, TASK-AR-583) ============= */
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
  --space-none: 0px;
  --space-hairline: 1px;
  --space-2xs: 2px;
  --space-xs: 3px;
  --space-sm: 4px;
  --space-md: 5px;
  --space-lg: 6px;
  --space-xl: 7px;
  --space-2xl: 8px;
  --space-3xl: 9px;
  --space-4xl: 10px;
  --space-5xl: 11px;
  --space-6xl: 12px;
  --space-7xl: 14px;
  --space-8xl: 16px;
  --space-9xl: 18px;
  --space-10xl: 20px;
  --space-11xl: 22px;
  --space-12xl: 24px;
  --space-13xl: 28px;
  --space-viewport-gap: 40px;
  --space-floating-offset: 76px;
  --radius-hairline: 2px;
  --radius-xs: 3px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: var(--radius);
  --radius-xl: 10px;
  --radius-2xl: 12px;
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

function normalizeRelationState(state) {
  const allowed = new Set(["default", "active", "stale", "blocked", "missing", "claimed", "guarded", "interrupted"]);
  const clean = String(state || "default").toLowerCase();
  return allowed.has(clean) ? clean : "default";
}

function componentRelationChip(label, state = "default", options = {}) {
  const chipState = normalizeRelationState(state);
  const value = options.value || chipState;
  const title = options.title ? ` title="${escapeHtml(options.title)}"` : "";
  return `<span class="relation-chip relation-${escapeHtml(chipState)}"${title}>
    <span class="relation-chip-label">${escapeHtml(label || "Relation")}</span>
    <strong>${escapeHtml(value)}</strong>
  </span>`;
}

function componentEvidencePreviewRow(row) {
  const item = row || {};
  const state = normalizeRelationState(item.state || "missing");
  const label = item.label || "Evidence";
  const detail = item.detail || "No evidence linked";
  const freshness = item.freshness || state;
  return `<div class="evidence-preview-row evidence-${escapeHtml(state)}" data-relation-state="${escapeHtml(state)}">
    <span class="evidence-preview-state">${escapeHtml(freshness)}</span>
    <span class="evidence-preview-copy">
      <strong>${escapeHtml(label)}</strong>
      <small>${escapeHtml(detail)}</small>
    </span>
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

function patternGraphContextStack(items, emptyLabel = "No graph context") {
  const rows = items || [];
  if (!rows.length) {
    return `<div class="graph-context-empty">${componentRelationChip("Graph context", "missing", { value: emptyLabel })}</div>`;
  }
  return `<div class="graph-context-stack" aria-label="Graph context stack">${rows.map((item) => {
    const state = normalizeRelationState(item.state || "default");
    const meta = item.meta ? `<small>${escapeHtml(item.meta)}</small>` : "";
    return `<div class="graph-context-item relation-${escapeHtml(state)}">
      ${componentRelationChip(item.label || "Node", state, { value: item.value || state })}
      <span>${escapeHtml(item.detail || "")}</span>
      ${meta}
    </div>`;
  }).join("")}</div>`;
}

function patternAttentionRelationPanel(options) {
  const panel = options || {};
  const evidenceRows = panel.evidenceRows || [];
  const graphItems = panel.graphItems || [];
  const label = panel.tasksetId ? `Attention graph for ${panel.tasksetId}` : "Attention graph";
  const chips = [
    componentRelationChip("Taskset", panel.tasksetState || "default", { value: panel.tasksetLabel || "tracked" }),
    componentRelationChip("Claim path", panel.claimState || "missing", { value: panel.claimLabel || "missing" }),
    componentRelationChip("Evidence freshness", panel.evidenceState || "missing", { value: panel.evidenceLabel || "missing" }),
    componentRelationChip("Command readiness", panel.commandState || "default", { value: panel.commandLabel || "proposal" }),
  ].join("");
  const evidence = evidenceRows.length
    ? evidenceRows.map(componentEvidencePreviewRow).join("")
    : componentEvidencePreviewRow({ state: "missing", label: "Evidence", detail: "No recent evidence or activity", freshness: "missing" });
  return `<section class="attention-relation-panel" aria-label="${escapeHtml(label)}" tabindex="0">
    <div class="attention-relation-head">
      <span class="attention-relation-kicker">operator_attention_graph</span>
      <strong>${escapeHtml(panel.title || panel.tasksetId || "Taskset relation")}</strong>
    </div>
    <div class="attention-relation-chips" aria-label="Relation states">${chips}</div>
    <div class="attention-relation-body">
      <div class="attention-evidence-preview" aria-label="Evidence preview">${evidence}</div>
      ${patternGraphContextStack(graphItems, panel.emptyGraphLabel || "No child context")}
    </div>
  </section>`;
}

function componentTasksetQuickSwitcher(options = {}) {
  const value = options.value || "";
  const resultCount = Number(options.resultCount || 0);
  const selected = options.selectedLabel || "No taskset selected";
  const results = options.resultsMarkup || "";
  return `<section class="tsboard-switcher" aria-label="Taskset quick switcher">
    <label class="tsboard-switcher-label" for="tsboard-switcher">Quick switcher</label>
    <div class="tsboard-switcher-control">
      <input id="tsboard-switcher" class="tsboard-switcher-input" type="search" autocomplete="off"
             role="combobox" aria-expanded="${resultCount ? "true" : "false"}"
             aria-controls="tsboard-switcher-results"
             value="${escapeHtml(value)}"
             placeholder="taskset id, title, task id, owner">
      <span class="tsboard-switcher-count" aria-live="polite">${escapeHtml(resultCount)} matches</span>
    </div>
    <div class="tsboard-switcher-selected">${componentRelationChip("Selected", "active", { value: selected })}</div>
    <div id="tsboard-switcher-results" class="tsboard-switcher-results" role="listbox" aria-label="Taskset switcher results">
      ${results || `<div class="empty">No matching tasksets</div>`}
    </div>
  </section>`;
}

function componentAttentionLaneFilter(lanes, activeLane = "all") {
  const rows = [{ id: "all", label: "All lanes", count: (lanes || []).reduce((sum, lane) => sum + Number(lane.count || 0), 0) }, ...(lanes || [])];
  return `<div class="tsboard-lane-filter" role="tablist" aria-label="Attention lane filter">
    ${rows.map((lane) => {
      const selected = (lane.id || "all") === activeLane;
      return `<button type="button" class="tsboard-lane-filter-button${selected ? " is-active" : ""}"
              role="tab" aria-selected="${selected}" data-tsboard-lane="${escapeHtml(lane.id || "all")}">
        <span>${escapeHtml(lane.label || lane.id || "Lane")}</span>
        <strong>${escapeHtml(lane.count || 0)}</strong>
      </button>`;
    }).join("")}
  </div>`;
}

function patternTasksetAttentionLane(lane) {
  const items = (lane && lane.items) || [];
  const state = normalizeRelationState((lane && lane.state) || "default");
  const emptyLabel = (lane && lane.empty_label) || `No ${((lane && lane.label) || "attention").toLowerCase()} items are currently surfaced.`;
  const emptyHint = (lane && lane.empty_hint) || (lane && lane.reason) || "This lane will update when matching tasksets appear.";
  const body = items.length
    ? items.map((item) => {
        const itemState = normalizeRelationState(item.state || state);
        return `<button type="button" class="tsboard-attention-card relation-${escapeHtml(itemState)}"
                data-tsboard-select="${escapeHtml(item.taskset_id || "")}">
          <span class="tsboard-attention-card-head">
            <strong>${escapeHtml(item.taskset_id || "")}</strong>
            ${componentRelationChip("Why", itemState, { value: item.reason || "attention" })}
          </span>
          <span class="tsboard-attention-title">${escapeHtml(item.title || item.taskset_id || "")}</span>
          <span class="tsboard-attention-reason">${escapeHtml(item.reason || "")}</span>
          <span class="tsboard-attention-meta">
            <span>${escapeHtml(item.progress_label || "")}</span>
            <span>${escapeHtml(item.claim_label || item.command_label || item.status || "")}</span>
          </span>
        </button>`;
      }).join("")
    : `<div class="tsboard-attention-empty">${componentRelationChip(lane.label || "Lane", "missing", { value: "empty" })}<strong class="tsboard-attention-empty-copy">${escapeHtml(emptyLabel)}</strong><span class="tsboard-attention-empty-hint">${escapeHtml(emptyHint)}</span></div>`;
  return `<section class="tsboard-attention-lane relation-${escapeHtml(state)}" data-lane="${escapeHtml((lane && lane.id) || "")}">
    <header class="tsboard-attention-lane-header">
      <div>
        <span class="tsboard-attention-kicker">attention lane</span>
        <strong>${escapeHtml((lane && lane.label) || "Attention")}</strong>
      </div>
      ${componentRelationChip("Count", state, { value: String((lane && lane.count) || 0) })}
    </header>
    <div class="tsboard-attention-lane-body">${body}</div>
  </section>`;
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

function patternSvgLayeredRadialLayout(nodes, layers) {
  const positions = {};
  const used = new Set();
  (layers || []).forEach((layer) => {
    const items = (nodes || []).filter((node) => {
      if (used.has(node.id)) return false;
      return layer.filter ? layer.filter(node) : true;
    });
    items.forEach((node) => used.add(node.id));
    if (layer.point) {
      items.forEach((node) => {
        positions[node.id] = { x: layer.point.x, y: layer.point.y };
      });
      return;
    }
    const center = layer.center || { x: 500, y: 300 };
    const radiusX = layer.radiusX || layer.radius || 220;
    const radiusY = layer.radiusY || layer.radius || 160;
    items.forEach((node, index) => {
      const angle = (index / Math.max(items.length, 1)) * Math.PI * 2 - Math.PI / 2;
      positions[node.id] = {
        x: center.x + Math.cos(angle) * radiusX,
        y: center.y + Math.sin(angle) * radiusY,
      };
    });
  });
  return positions;
}

function patternSvgGraph(options) {
  const graph = options || {};
  const svg = graph.svg;
  if (!svg) return;
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const positions = graph.positions || {};
  const ns = graph.namespace || "http://www.w3.org/2000/svg";
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!nodes.length) {
    const note = document.createElementNS(ns, "text");
    note.setAttribute("x", graph.emptyX || "500");
    note.setAttribute("y", graph.emptyY || "300");
    note.setAttribute("class", graph.emptyClass || "svg-graph-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = graph.emptyLabel || "No graph data";
    svg.appendChild(note);
    return;
  }

  const edgeLayer = document.createElementNS(ns, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const line = document.createElementNS(ns, "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", graph.edgeClassFor ? graph.edgeClassFor(edge) : (graph.edgeClass || "svg-graph-edge"));
    const edgeAttrs = graph.edgeAttrsFor ? graph.edgeAttrsFor(edge) : {};
    Object.entries(edgeAttrs || {}).forEach(([key, value]) => line.setAttribute(key, value));
    edgeLayer.appendChild(line);
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = document.createElementNS(ns, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const group = document.createElementNS(ns, "g");
    group.setAttribute("class", graph.nodeClassFor ? graph.nodeClassFor(node) : (graph.nodeClass || "svg-graph-node"));
    const nodeAttrs = graph.nodeAttrsFor ? graph.nodeAttrsFor(node) : {};
    Object.entries(nodeAttrs || {}).forEach(([key, value]) => group.setAttribute(key, value));
    const circle = document.createElementNS(ns, "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", graph.nodeRadiusFor ? graph.nodeRadiusFor(node) : (graph.nodeRadius || "16"));
    group.appendChild(circle);
    const label = document.createElementNS(ns, "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + (graph.labelDy || 28));
    label.textContent = graph.nodeLabelFor ? graph.nodeLabelFor(node) : String(node.id || "").slice(0, 18);
    group.appendChild(label);
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
}

function patternCalendarGrid(options) {
  const calendar = options || {};
  const weekdays = calendar.weekdays || [];
  const days = calendar.days || [];
  const byDate = calendar.byDate || {};
  const dateKeyFor = calendar.dateKeyFor || (() => "");
  const todayKey = calendar.todayKey || "";
  const header = weekdays.map((name) => `<div class="calendar-weekday" role="columnheader">${escapeHtml(name)}</div>`).join("");
  const cells = days.map(({ date, outside }) => {
    const key = dateKeyFor(date);
    const events = byDate[key] || [];
    const isToday = key === todayKey;
    const eventHtml = events.map((event) => {
      const extraClass = calendar.eventClassFor ? calendar.eventClassFor(event) : "";
      const title = calendar.eventTitleFor ? calendar.eventTitleFor(event) : (event.title || "");
      const id = calendar.eventIdFor ? calendar.eventIdFor(event) : (event.id || "");
      const label = calendar.eventLabelFor ? calendar.eventLabelFor(event) : title;
      return `<span class="calendar-event ${extraClass}" title="${escapeHtml(title)}" data-entity-id="${escapeHtml(id)}">${escapeHtml(label)}</span>`;
    }).join("");
    return `<div class="calendar-cell ${outside ? "is-outside" : ""} ${isToday ? "is-today" : ""}" role="gridcell">
      <span class="calendar-cell-date">${escapeHtml(date.getDate())}</span>
      ${eventHtml}
    </div>`;
  }).join("");
  return header + cells;
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
    "componentRelationChip": "ui_component",
    "componentEvidencePreviewRow": "ui_component",
    "componentTasksetQuickSwitcher": "ui_component",
    "componentAttentionLaneFilter": "ui_component",
    "patternTaskLane": "pattern_component",
    "patternClaimCard": "pattern_component",
    "patternAuditCard": "pattern_component",
    "patternEvidencePanel": "pattern_component",
    "patternAttentionRelationPanel": "pattern_component",
    "patternGraphContextStack": "pattern_component",
    "patternTasksetAttentionLane": "pattern_component",
    "patternCommandBar": "pattern_component",
    "patternStateMachinePanelLegend": "pattern_component",
    "patternSvgLayeredRadialLayout": "pattern_component",
    "patternSvgGraph": "pattern_component",
    "patternCalendarGrid": "pattern_component",
    "patternAuditMeta": "pattern_component",
    "patternSurfaceMeta": "pattern_component",
}
