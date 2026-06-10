from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse

from . import ui_commands
from . import ui_state


@dataclass(frozen=True)
class ConsoleResponse:
    status: int
    content_type: str
    body: bytes


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Runtime Console</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <div id="runtime-console-app" class="shell">
    <header class="topbar">
      <div class="brand">
        <svg class="brand-mark" viewBox="0 0 48 48" role="img" aria-label="Agent Runtime">
          <rect x="6" y="8" width="36" height="32" rx="6"></rect>
          <path d="M14 18h20M14 24h12M14 30h16"></path>
          <circle cx="35" cy="30" r="3"></circle>
        </svg>
        <div>
          <h1>Agent Runtime Console</h1>
          <p id="status-line">Loading runtime state</p>
        </div>
      </div>
      <div class="toolbar">
        <button id="refresh-button" type="button">Refresh</button>
        <span id="poll-state" class="state-chip">polling</span>
      </div>
    </header>

    <main class="layout">
      <section class="dashboard" aria-label="Dashboard">
        <div class="metric"><span>Total Tasks</span><strong id="metric-tasks">0</strong></div>
        <div class="metric"><span>Active</span><strong id="metric-active">0</strong></div>
        <div class="metric"><span>Blocked</span><strong id="metric-blocked">0</strong></div>
        <div class="metric"><span>Warnings</span><strong id="metric-warnings">0</strong></div>
      </section>

      <section class="work-surface">
        <form id="create-task-form" class="create-form">
          <input id="new-task-id" name="id" placeholder="TASK-UI-001">
          <input id="new-task-title" name="title" placeholder="New task title" required>
          <select id="new-task-priority" name="priority">
            <option>P1</option>
            <option>P0</option>
            <option>P2</option>
            <option>P3</option>
          </select>
          <button type="submit">Create</button>
        </form>
        <form id="runtime-command-form" class="runtime-form">
          <select id="runtime-command-type" name="type">
            <option value="runtime.call_agent">Call Agent</option>
            <option value="runtime.assign_task">Assign Task</option>
            <option value="runtime.request_review">Request Review</option>
            <option value="runtime.request_meeting">Request Meeting</option>
            <option value="runtime.goal.start">Start Goal</option>
            <option value="runtime.goal.pause">Pause Goal</option>
            <option value="runtime.goal.resume">Resume Goal</option>
            <option value="runtime.goal.stop">Stop Goal</option>
            <option value="planning.scan">Planning Scan</option>
          </select>
          <input id="runtime-target-agent" name="target" placeholder="target agent">
          <input id="runtime-task-id" name="task_id" placeholder="task id">
          <input id="runtime-goal-id" name="goal_id" placeholder="goal id">
          <textarea id="runtime-instruction" name="instruction" placeholder="Instruction or lifecycle reason"></textarea>
          <button type="submit">Send</button>
        </form>
        <nav class="tabs" aria-label="Views">
          <button class="tab is-active" type="button" data-view="board">Backlog</button>
          <button class="tab" type="button" data-view="agents">Agents</button>
          <button class="tab" type="button" data-view="messages">Messages</button>
          <button class="tab" type="button" data-view="events">Events</button>
          <button class="tab" type="button" data-view="evidence">Evidence</button>
          <button class="tab" type="button" data-view="planner">Planner</button>
          <button class="tab" type="button" data-view="map">Map</button>
          <button class="tab" type="button" data-view="sources">Sources</button>
          <button class="tab" type="button" data-view="writes">Writes</button>
        </nav>

        <div id="view-board" class="view is-active">
          <div id="kanban" class="kanban" aria-label="Kanban"></div>
        </div>
        <div id="view-agents" class="view">
          <div id="tasksets-list" class="taskset-strip"></div>
          <div id="agents-list" class="list-panel"></div>
        </div>
        <div id="view-messages" class="view">
          <div id="messages-list" class="list-panel"></div>
        </div>
        <div id="view-events" class="view">
          <div class="filter-row">
            <input id="event-filter-type" placeholder="event type">
            <input id="event-filter-agent" placeholder="agent">
            <input id="event-filter-task" placeholder="task id">
            <input id="event-filter-goal" placeholder="goal id">
            <input id="event-filter-search" placeholder="search">
          </div>
          <div id="events-list" class="list-panel"></div>
        </div>
        <div id="view-evidence" class="view">
          <div class="evidence-grid">
            <section>
              <h2>Errors</h2>
              <div id="errors-list" class="list-panel"></div>
            </section>
            <section>
              <h2>Evidence</h2>
              <div id="evidence-list" class="list-panel"></div>
            </section>
            <section>
              <h2>Replay</h2>
              <div id="replay-list" class="list-panel"></div>
            </section>
          </div>
        </div>
        <div id="view-planner" class="view">
          <div class="evidence-grid">
            <section>
              <h2>Planning Proposals</h2>
              <div id="planning-proposals-list" class="list-panel"></div>
            </section>
            <section>
              <h2>Planning Scans</h2>
              <div id="planning-scans-list" class="list-panel"></div>
            </section>
            <section>
              <h2>Requests and Drafts</h2>
              <div id="planning-requests-list" class="list-panel"></div>
            </section>
          </div>
        </div>
        <div id="view-map" class="view">
          <div class="evidence-grid">
            <section>
              <h2>Graph</h2>
              <div id="graph-list" class="list-panel"></div>
            </section>
            <section>
              <h2>State Machines</h2>
              <div id="state-machine-list" class="list-panel"></div>
            </section>
            <section>
              <h2>Roadmap</h2>
              <div id="roadmap-list" class="list-panel"></div>
            </section>
          </div>
        </div>
        <div id="view-sources" class="view">
          <div id="sources-list" class="list-panel"></div>
        </div>
        <div id="view-writes" class="view">
          <div id="command-log" class="list-panel"></div>
        </div>
      </section>

      <aside id="detail-panel" class="detail-panel" aria-label="Task detail">
        <div class="detail-empty">No task selected</div>
      </aside>
    </main>
  </div>
  <script src="/app.js"></script>
</body>
</html>
"""


CSS = """:root {
  --canvas: #010102;
  --paper: #010102;
  --panel: #0f1011;
  --panel-strong: #15171a;
  --surface-raised: #1b1d22;
  --ink: #f7f8f8;
  --muted: #a2a8b3;
  --subtle: #62666d;
  --line: #23252a;
  --line-strong: #343844;
  --teal: #31d0aa;
  --blue: #57a0ff;
  --amber: #d99a2b;
  --red: #f04438;
  --violet: #5e6ad2;
  --primary: #5e6ad2;
  --primary-hover: #828fff;
  --success: #27a644;
  --warning: #d99a2b;
  --danger: #f04438;
  --radius: 8px;
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.34);
  --focus: 0 0 0 3px rgba(130, 143, 255, 0.22);
}
* { box-sizing: border-box; }
html { background: var(--canvas); }
body {
  margin: 0;
  min-height: 100vh;
  font-family: "Geist", "IBM Plex Sans", "Segoe UI", sans-serif;
  background:
    linear-gradient(rgba(247, 248, 248, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(247, 248, 248, 0.035) 1px, transparent 1px),
    linear-gradient(180deg, #08090b 0%, var(--canvas) 48%, #040405 100%);
  background-size: 44px 44px, 44px 44px, auto;
  color: var(--ink);
}
p, h1, h2, h3 { margin: 0; }
a {
  color: var(--blue);
  text-decoration: none;
}
a:hover { text-decoration: underline; }
.shell {
  min-height: 100vh;
  position: relative;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(12, 13, 16, 0.88);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 4;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.04);
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.brand-mark {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--primary), #20233b);
  box-shadow: 0 0 0 1px rgba(130, 143, 255, 0.22), 0 16px 34px rgba(94, 106, 210, 0.16);
}
.brand-mark rect {
  fill: rgba(1, 1, 2, 0.20);
  stroke: rgba(247, 248, 248, 0.54);
}
.brand-mark path,
.brand-mark circle {
  fill: none;
  stroke: var(--ink);
  stroke-width: 2;
  stroke-linecap: round;
}
h1 {
  font-size: 28px;
  line-height: 1.05;
  letter-spacing: 0;
}
#status-line {
  margin-top: 5px;
  color: var(--muted);
  font-size: 13px;
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}
button {
  border: 1px solid rgba(130, 143, 255, 0.42);
  border-radius: var(--radius);
  padding: 9px 12px;
  min-height: 36px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(180deg, var(--primary-hover), var(--primary));
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(94, 106, 210, 0.22);
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
}
button:hover { transform: translateY(-1px); }
button:focus-visible {
  outline: none;
  box-shadow: var(--focus);
}
button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  transform: none;
}
input,
select,
textarea {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 9px 10px;
  font: inherit;
  font-size: 13px;
  background: rgba(1, 1, 2, 0.64);
  color: var(--ink);
  outline: none;
}
textarea {
  min-height: 38px;
  resize: vertical;
}
input::placeholder,
textarea::placeholder {
  color: var(--subtle);
}
input:focus,
select:focus,
textarea:focus {
  border-color: rgba(130, 143, 255, 0.72);
  box-shadow: var(--focus);
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
  padding: 18px 24px 28px;
}
.dashboard {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 10px;
}
.metric {
  min-height: 82px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(21, 23, 26, 0.94), rgba(15, 16, 17, 0.94));
  padding: 14px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035);
}
.metric strong {
  display: block;
  margin-top: 8px;
  font-size: 30px;
  line-height: 1;
  letter-spacing: 0;
}
.metric span {
  color: var(--muted);
  font-size: 12px;
}
.work-surface,
.detail-panel {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: linear-gradient(180deg, rgba(15, 16, 17, 0.96), rgba(10, 11, 13, 0.96));
  box-shadow: var(--shadow);
}
.work-surface {
  min-width: 0;
  display: grid;
  gap: 12px;
  padding: 14px;
}
.create-form,
.runtime-form,
.filter-row,
.edit-form,
.edit-row,
.button-row {
  display: grid;
  gap: 8px;
}
.create-form {
  grid-template-columns: minmax(140px, 0.8fr) minmax(220px, 1.4fr) minmax(80px, 0.4fr) auto;
}
.runtime-form {
  grid-template-columns: minmax(170px, 1fr) minmax(130px, 0.8fr) minmax(110px, 0.7fr) minmax(110px, 0.7fr) minmax(240px, 1.4fr) auto;
  align-items: start;
}
.filter-row {
  grid-template-columns: repeat(5, minmax(120px, 1fr));
}
.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding-top: 2px;
  border-bottom: 1px solid var(--line);
}
.tab {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
  color: var(--muted);
  padding: 8px 10px;
}
.tab.is-active {
  color: #ffffff;
  background: rgba(94, 106, 210, 0.18);
  border-color: rgba(130, 143, 255, 0.36);
}
.view {
  display: none;
  min-width: 0;
}
.view.is-active {
  display: block;
}
.kanban {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: 10px;
}
.lane {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.032);
  padding: 10px;
}
.lane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  text-transform: uppercase;
  padding-bottom: 8px;
  letter-spacing: 0;
}
.lane-title {
  display: grid;
  gap: 2px;
  color: var(--ink);
}
.lane-title small {
  color: var(--subtle);
  font-size: 10px;
  text-transform: uppercase;
}
.lane-count {
  min-width: 28px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 3px 8px;
  background: rgba(94, 106, 210, 0.14);
  color: var(--ink);
  text-align: center;
}
.lane-body,
.list-panel,
.taskset-strip {
  display: grid;
  gap: 8px;
}
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.evidence-grid section {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.026);
  padding: 10px;
}
.evidence-grid h2 {
  font-size: 14px;
  margin-bottom: 8px;
  letter-spacing: 0;
}
.task-card,
.taskset-card,
.list-row {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.044);
  color: var(--ink);
  padding: 10px;
  display: grid;
  gap: 7px;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.026);
}
.task-card:hover,
.taskset-card:hover,
.list-row:hover {
  border-color: var(--line-strong);
}
.task-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.task-id {
  color: var(--primary-hover);
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 11px;
}
.task-card-title {
  color: var(--ink);
  font-size: 13px;
  line-height: 1.25;
}
.task-card-summary {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.35;
}
.task-card-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}
.task-card-meta > span,
.task-status {
  min-width: 0;
  border: 1px solid rgba(52, 56, 68, 0.76);
  border-radius: 6px;
  background: rgba(1, 1, 2, 0.34);
  padding: 6px;
}
.meta-label {
  display: block;
  color: var(--subtle);
  font-size: 10px;
  font-weight: 800;
  line-height: 1;
  text-transform: uppercase;
}
.task-card-meta strong,
.task-status strong {
  display: block;
  margin-top: 4px;
  color: var(--ink);
  font-size: 11px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.task-card-evidence strong {
  color: var(--teal);
}
.task-card-taskset strong {
  color: var(--primary-hover);
}
.task-card b,
.taskset-card b,
.list-row b {
  overflow-wrap: anywhere;
}
.task-card span,
.taskset-card span,
.list-row span,
.list-row p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.35;
}
.task-card .task-id {
  color: var(--primary-hover);
  font-size: 11px;
}
.task-card .task-card-summary {
  color: var(--muted);
}
.task-card .meta-label {
  color: var(--subtle);
  font-size: 10px;
  line-height: 1;
}
.task-card code,
.taskset-card code,
.list-row code {
  color: var(--subtle);
  font-size: 11px;
  overflow-wrap: anywhere;
}
.list-row.ok,
.task-card.status-completed,
.task-card.status-done {
  border-left: 3px solid var(--success);
}
.list-row.warn,
.task-card.status-in-progress,
.task-card.status-active,
.task-card.status-planned,
.task-card.status-ready {
  border-left: 3px solid var(--warning);
}
.list-row.error,
.task-card.status-blocked,
.task-card.status-hold {
  border-left: 3px solid var(--danger);
}
.state-chip,
.pill {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  gap: 6px;
  border-radius: 999px;
  padding: 5px 8px;
  border: 1px solid rgba(49, 208, 170, 0.20);
  background: rgba(49, 208, 170, 0.10);
  color: var(--teal);
  font-size: 12px;
}
.pill.high { color: var(--red); border-color: rgba(240, 68, 56, 0.24); background: rgba(240, 68, 56, 0.10); }
.pill.medium { color: var(--amber); border-color: rgba(217, 154, 43, 0.24); background: rgba(217, 154, 43, 0.10); }
.pill.low { color: var(--teal); }
.agent-progress,
.meta-grid {
  display: grid;
  gap: 8px;
}
.agent-progress-meta,
.meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.agent-progress-meta {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
}
.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--teal), var(--primary-hover));
}
.detail-panel {
  padding: 14px;
  align-self: start;
  position: sticky;
  top: 88px;
}
.detail-panel h2 {
  font-size: 18px;
  line-height: 1.2;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}
.detail-panel p {
  margin-top: 8px;
  color: var(--muted);
  line-height: 1.45;
}
.detail-empty {
  color: var(--muted);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: 18px;
}
.meta-grid {
  margin: 12px 0;
}
.meta-grid div {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 8px;
  background: rgba(255, 255, 255, 0.026);
}
.meta-grid span {
  display: block;
  color: var(--muted);
  font-size: 11px;
}
.meta-grid strong {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  overflow-wrap: anywhere;
}
.edit-row,
.button-row {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
pre {
  max-width: 100%;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #050608;
  color: #e9ebf0;
  padding: 10px;
}
.empty {
  color: var(--muted);
  font-style: italic;
  padding: 8px;
}
.hidden { display: none !important; }
@media (max-width: 1200px) {
  .layout { grid-template-columns: 1fr; }
  .detail-panel { position: static; }
  .kanban { grid-template-columns: repeat(2, minmax(220px, 1fr)); }
}
@media (max-width: 760px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
    padding: 16px;
  }
  h1 { font-size: 24px; }
  .layout { padding: 14px; }
  .dashboard,
  .kanban,
  .create-form,
  .runtime-form,
  .filter-row,
  .evidence-grid,
  .task-card-meta,
  .meta-grid,
  .edit-row,
  .button-row {
    grid-template-columns: 1fr;
  }
}
"""

JS = """const lanes = ["Backlog", "Ready", "In Progress", "Review", "Blocked", "Done"];
const taskStatusOptions = [
  "assigned",
  "blocked",
  "claimed",
  "completed",
  "defer",
  "deferred",
  "done",
  "hold",
  "in_progress",
  "pending",
  "planned",
  "ready",
  "ready_for_governance_review",
  "review",
  "waiting_review",
  "working",
];
const runtimeCommandTypes = ["runtime.call_agent", "runtime.assign_task", "runtime.request_review", "runtime.request_meeting", "runtime.goal.start", "runtime.goal.pause", "runtime.goal.resume", "runtime.goal.stop", "planning.scan"];
let runtimeState = null;
let selectedTaskId = null;
let pendingWrites = [];

const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#039;"
}[char]));

function setText(id, value) {
  const node = $(id);
  if (node) node.textContent = value;
}

async function loadState() {
  setText("poll-state", "refreshing");
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    runtimeState = await response.json();
    renderAll();
    setText("poll-state", "polling");
  } catch (error) {
    setText("poll-state", "error");
    $("status-line").textContent = `State load failed: ${error.message}`;
  }
}

async function sendJson(url, options) {
  const requestId = `pending-${Date.now()}`;
  pendingWrites.unshift({ id: requestId, type: options.type || "request", status: "pending", created_at: new Date().toISOString() });
  renderCommands();
  const response = await fetch(url, {
    method: options.method || "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options.payload || {})
  });
  const payload = await response.json();
  pendingWrites = pendingWrites.filter((item) => item.id !== requestId);
  pendingWrites.unshift(payload);
  await loadState();
  renderCommands();
  return payload;
}

function taskCounts(tasks) {
  return {
    active: tasks.filter((task) => task.lane === "In Progress").length,
    blocked: tasks.filter((task) => task.lane === "Blocked").length
  };
}

function numericPct(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return null;
  return Math.max(0, Math.min(100, Math.round(number)));
}

function progressBar(value) {
  const pct = numericPct(value);
  const width = pct === null ? 0 : pct;
  const label = pct === null ? "~" : `${pct}%`;
  return `<div class="progress-track" role="img" aria-label="progress ${escapeHtml(label)}">
    <div class="progress-fill" style="width: ${width}%"></div>
  </div>`;
}

function renderDashboard() {
  const tasks = runtimeState.tasks || [];
  const counts = taskCounts(tasks);
  setText("metric-tasks", tasks.length);
  setText("metric-active", counts.active);
  setText("metric-blocked", counts.blocked);
  setText("metric-warnings", (runtimeState.warnings || []).length + (runtimeState.gaps || []).length);
  $("status-line").textContent = `Generated ${runtimeState.generated_at} - ${tasks.length} tasks`;
}

function renderTaskSets() {
  const host = $("tasksets-list");
  if (!host) return;
  const taskSets = runtimeState.task_sets || [];
  host.innerHTML = taskSets.length ? taskSets.map((taskSet) => `
    <article class="taskset-card">
      <b>${escapeHtml(taskSet.id)}</b>
      <span>${escapeHtml(taskSet.status_text || "active task set")}</span>
      <span>${escapeHtml(taskSet.active || 0)} active / ${escapeHtml(taskSet.blocked || 0)} blocked / ${escapeHtml(taskSet.done || 0)} done</span>
      ${progressBar(taskSet.progress_pct)}
    </article>
  `).join("") : "";
}

function statusClassName(status) {
  const normalized = String(status || "unknown").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `status-${normalized || "unknown"}`;
}

function laneClassName(lane) {
  const normalized = String(lane || "backlog").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `lane-${normalized || "backlog"}`;
}

function evidenceCountForTask(task) {
  const directCount = Number(task.evidence_count);
  if (Number.isFinite(directCount)) return directCount;
  return (runtimeState.evidence || []).filter((item) => item.task_id === task.id).length;
}

function evidenceLabelForTask(task) {
  if (task.evidence_label) return String(task.evidence_label);
  const count = evidenceCountForTask(task);
  return count === 1 ? "1 evidence" : `${count} evidence`;
}

function taskCard(task) {
  const status = task.status || "unknown";
  const priority = task.priority || "P?";
  const taskSet = task.task_set_id || "no task set";
  const evidence = evidenceLabelForTask(task);
  return `<button class="task-card ${statusClassName(status)}" type="button" data-task-id="${escapeHtml(task.id)}">
    <div class="task-card-header">
      <span class="task-id">${escapeHtml(task.id)}</span>
      <span class="task-status"><span class="meta-label">Status</span><strong>${escapeHtml(status)}</strong></span>
    </div>
    <strong class="task-card-title">${escapeHtml(task.title)}</strong>
    <span class="task-card-summary">${escapeHtml(task.description || "No summary")}</span>
    <div class="task-card-meta" aria-label="Task metadata">
      <span><span class="meta-label">Priority</span><strong>${escapeHtml(priority)}</strong></span>
      <span><span class="meta-label">Owner</span><strong>${escapeHtml(task.owner_agent || "unassigned")}</strong></span>
      <span class="task-card-taskset"><span class="meta-label">Task set</span><strong>${escapeHtml(taskSet)}</strong></span>
      <span class="task-card-evidence"><span class="meta-label">Evidence</span><strong>${escapeHtml(evidence)}</strong></span>
    </div>
  </button>`;
}

function renderKanban() {
  const tasks = runtimeState.tasks || [];
  $("kanban").innerHTML = lanes.map((lane) => {
    const laneTasks = tasks.filter((task) => task.lane === lane);
    const body = laneTasks.length ? laneTasks.map(taskCard).join("") : `<div class="empty">No ${escapeHtml(lane)} tasks</div>`;
    return `<section class="lane ${laneClassName(lane)}" data-lane="${escapeHtml(lane)}"><header class="lane-header"><span class="lane-title">${escapeHtml(lane)}<small>Lane</small></span><span class="lane-count" aria-label="${escapeHtml(lane)} task count">${laneTasks.length}</span></header><div class="lane-body">${body}</div></section>`;
  }).join("");
  document.querySelectorAll(".task-card").forEach((button) => {
    button.addEventListener("click", () => {
      selectedTaskId = button.dataset.taskId;
      renderDetail();
    });
  });
}

function renderAgents() {
  renderTaskSets();
  const agents = runtimeState.agents || [];
  $("agents-list").innerHTML = agents.length ? agents.map((agent) => `
    <article class="list-row ${agent.online ? "ok" : "warn"}">
      <b>${escapeHtml(agent.display_name || agent.role)}</b>
      <span>${escapeHtml(agent.status || "offline")} / ${escapeHtml(agent.current_task_id || "no task")}</span>
      <div class="agent-progress">
        <div class="agent-progress-meta">
          <span>phase: ${escapeHtml(agent.phase || "unknown")}</span>
          <span>step: ${escapeHtml(agent.step_index && agent.step_total ? `${agent.step_index}/${agent.step_total}` : "?")}</span>
          <span>progress_pct: ${escapeHtml(numericPct(agent.progress_pct) ?? "~")}</span>
        </div>
        ${progressBar(agent.progress_pct)}
        <span>${escapeHtml(agent.status_text || agent.phase || "working")}</span>
        <code>${escapeHtml(agent.task_set_id || "no task set")}</code>
      </div>
      <code>${escapeHtml(agent.source_path)}</code>
    </article>
  `).join("") : `<div class="empty">No active sessions</div>`;
}

function renderMessages() {
  const messages = runtimeState.messages || [];
  $("messages-list").innerHTML = messages.length ? messages.map((message) => `
    <article class="list-row">
      <b>${escapeHtml(message.id)}</b>
      <span>${escapeHtml(message.from)} -> ${escapeHtml(message.to)} / ${escapeHtml(message.status)}</span>
      <p>${escapeHtml(message.body).slice(0, 220)}</p>
      <code>${escapeHtml(message.source_path)}</code>
    </article>
  `).join("") : `<div class="empty">No messages</div>`;
}

function filterEvents(events) {
  const type = $("event-filter-type")?.value.trim();
  const agent = $("event-filter-agent")?.value.trim();
  const task = $("event-filter-task")?.value.trim();
  const goal = $("event-filter-goal")?.value.trim();
  const search = $("event-filter-search")?.value.trim().toLowerCase();
  return events.filter((event) => {
    if (type && event.event !== type && event.type !== type) return false;
    if (agent && event.role !== agent && event.actor !== agent) return false;
    if (task && event.task_id !== task) return false;
    if (goal && event.goal_id !== goal) return false;
    if (search && !JSON.stringify(event).toLowerCase().includes(search)) return false;
    return true;
  });
}

function renderEvents() {
  const events = filterEvents(runtimeState.events || []);
  $("events-list").innerHTML = events.length ? events.slice(-80).reverse().map((event) => `
    <article class="list-row ${event.severity === "error" ? "error" : "ok"}">
      <b>${escapeHtml(event.type || event.event || event.id)}</b>
      <span>${escapeHtml(event.created_at || event.ts)} / ${escapeHtml(event.actor || event.role || "runtime")}</span>
      <code>${escapeHtml(event.id)}</code>
    </article>
  `).join("") : `<div class="empty">No events</div>`;
}

function renderEvidence() {
  const errors = runtimeState.errors || [];
  const evidence = runtimeState.evidence || [];
  const replay = runtimeState.replay || [];
  $("errors-list").innerHTML = errors.length ? errors.slice(-40).reverse().map((item) => `
    <article class="list-row error">
      <b>${escapeHtml(item.message)}</b>
      <span>${escapeHtml(item.actor || "runtime")} / ${escapeHtml(item.task_id || item.goal_id || "no context")}</span>
      <code>${escapeHtml(item.source_path || item.event_id || "")}</code>
    </article>
  `).join("") : `<div class="empty">No recent errors</div>`;
  $("evidence-list").innerHTML = evidence.length ? evidence.slice(-60).reverse().map((item) => `
    <article class="list-row ok">
      <b>${escapeHtml(item.evidence)}</b>
      <span>${escapeHtml(item.source_type)} / ${escapeHtml(item.task_id || item.goal_id || "no context")}</span>
      <code>${escapeHtml(item.source_path || item.source_id || "")}</code>
    </article>
  `).join("") : `<div class="empty">No evidence links</div>`;
  $("replay-list").innerHTML = replay.length ? replay.slice(-80).reverse().map((item) => `
    <article class="list-row">
      <b>${escapeHtml(item.type || item.kind)}</b>
      <span>${escapeHtml(item.created_at || "")} / ${escapeHtml(item.actor || "runtime")}</span>
      <p>${escapeHtml(item.summary || "")}</p>
      <code>${escapeHtml(item.task_id || item.goal_id || item.source_path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No replay records</div>`;
}

function renderMap() {
  const graph = runtimeState.graph || { nodes: [], edges: [] };
  const machines = runtimeState.state_machines || [];
  const roadmap = runtimeState.roadmap || { milestones: [] };
  $("graph-list").innerHTML = graph.edges.length ? graph.edges.slice(0, 80).map((edge) => `
    <article class="list-row">
      <b>${escapeHtml(edge.from)} -> ${escapeHtml(edge.to)}</b>
      <span>${escapeHtml(edge.kind)} / ${escapeHtml(edge.task_id || "no task")}</span>
      <code>${escapeHtml(edge.source_path || edge.id || "")}</code>
    </article>
  `).join("") : `<div class="empty">No graph edges</div>`;
  $("state-machine-list").innerHTML = machines.length ? machines.map((machine) => `
    <article class="list-row ok">
      <b>${escapeHtml(machine.id)}: ${escapeHtml(machine.current_state || machine.initial || "unknown")}</b>
      <span>${escapeHtml(machine.scope || "")} / ${escapeHtml((machine.states || []).join(" -> "))}</span>
      <code>${escapeHtml(machine.source_path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No state machines</div>`;
  $("roadmap-list").innerHTML = (roadmap.milestones || []).length ? (roadmap.milestones || []).slice(0, 40).map((item) => `
    <article class="list-row ${item.done ? "ok" : "warn"}">
      <b>${escapeHtml(item.date)} - ${escapeHtml(item.title)}</b>
      <span>${escapeHtml(item.done ? "done" : "open")} / ${escapeHtml(roadmap.phase || "no phase")}</span>
      <code>${escapeHtml(roadmap.source_path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No roadmap milestones</div>`;
}

function renderPlanning() {
  const planning = runtimeState.planning || { scan_reports: [], proposals: [], requests: [], draft_tasks: [], applied: [], summary: {} };
  const proposals = planning.proposals || [];
  const scans = planning.scan_reports || [];
  const requests = [...(planning.requests || []), ...(planning.draft_tasks || []), ...(planning.applied || [])];
  $("planning-proposals-list").innerHTML = proposals.length ? proposals.slice(0, 80).map((row) => `
    <article class="list-row ${row.risk_tier === "high" || row.status === "blocked" ? "warn" : "ok"}">
      <b>${escapeHtml(row.id || row.title || "proposal")}</b>
      <span>${escapeHtml(row.status || "unknown")} / ${escapeHtml(row.action_type || "proposal")} / ${escapeHtml(row.risk_tier || "unknown")}</span>
      <p>${escapeHtml(row.owner_boundary || row.suggested_next_action || "")}</p>
      <code>${escapeHtml(row.source_path || (row.source_refs || [])[0]?.path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No planning proposals</div>`;
  $("planning-scans-list").innerHTML = scans.length ? scans.slice(0, 40).map((row) => `
    <article class="list-row ${row.status === "block" || row.status === "watch" ? "warn" : "ok"}">
      <b>${escapeHtml(row.id || "scan")}</b>
      <span>${escapeHtml(row.status || "unknown")} / ${escapeHtml(row.trigger || "manual")} / findings ${escapeHtml((row.summary || {}).finding_count || 0)}</span>
      <code>${escapeHtml(row.source_path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No planning scans</div>`;
  $("planning-requests-list").innerHTML = requests.length ? requests.slice(0, 80).map((row) => `
    <article class="list-row ${row.status === "failed" ? "error" : "ok"}">
      <b>${escapeHtml(row.id || row.source_path || "planning record")}</b>
      <span>${escapeHtml(row.status || row.source_kind || "record")} / ${escapeHtml(row.type || row.mode || "planning")}</span>
      <code>${escapeHtml(row.source_path || "")}</code>
    </article>
  `).join("") : `<div class="empty">No planning requests, drafts, or apply records</div>`;
}

function renderSources() {
  const rows = [...(runtimeState.sources || []), ...(runtimeState.gaps || []), ...(runtimeState.warnings || [])];
  $("sources-list").innerHTML = rows.length ? rows.map((row) => `
    <article class="list-row ${row.fresh === false || row.kind?.includes("error") ? "warn" : "ok"}">
      <b>${escapeHtml(row.id || row.kind)}</b>
      <span>${escapeHtml(row.freshness || row.detail || row.mutation_boundary || "")}</span>
      <code>${escapeHtml(row.path)}</code>
    </article>
  `).join("") : `<div class="empty">No sources</div>`;
}

function renderCommands() {
  const rows = [...pendingWrites, ...((runtimeState && runtimeState.commands) || [])];
  const host = $("command-log");
  if (!host) return;
  host.innerHTML = rows.length ? rows.slice(0, 80).map((row) => `
    <article class="list-row ${row.status === "failed" ? "error" : row.status === "pending" ? "warn" : "ok"}">
      <b>${escapeHtml(row.id || row.type)}</b>
      <span>${escapeHtml(row.status)} / ${escapeHtml(row.type || "command")} / ${escapeHtml(row.risk_level || "unknown")}</span>
      <code>${escapeHtml(row.target || row.source_path || "")}</code>
      ${row.approval_required ? `<p>approval required: ${escapeHtml((row.approval_reasons || []).join(", ") || "owner review")}</p>` : ""}
      ${row.errors ? `<p>${escapeHtml(row.errors.join("; "))}</p>` : ""}
    </article>
  `).join("") : `<div class="empty">No write commands</div>`;
}

function renderDetail() {
  const panel = $("detail-panel");
  const task = (runtimeState.tasks || []).find((item) => item.id === selectedTaskId);
  if (!task) {
    panel.innerHTML = `<div class="detail-empty">No task selected</div>`;
    return;
  }
  panel.innerHTML = `<article>
    <h2>${escapeHtml(task.id)}</h2>
    <p>${escapeHtml(task.description || task.title)}</p>
    <div class="meta-grid">
      <div><span>Status</span><strong>${escapeHtml(task.status)}</strong></div>
      <div><span>Lane</span><strong>${escapeHtml(task.lane)}</strong></div>
      <div><span>Owner</span><strong>${escapeHtml(task.owner_agent || "unassigned")}</strong></div>
      <div><span>Priority</span><strong>${escapeHtml(task.priority || "none")}</strong></div>
      <div><span>Source</span><strong>${escapeHtml(task.source_path)}</strong></div>
      <div><span>Freshness</span><strong>${escapeHtml(task.freshness)}</strong></div>
      <div><span>Updated</span><strong>${escapeHtml(task.last_updated || "unknown")}</strong></div>
      <div><span>Blocked</span><strong>${escapeHtml(task.blocked_reason || "none")}</strong></div>
    </div>
    <form id="edit-task-form" class="edit-form">
      <div class="edit-row">
        <select id="detail-status">
          ${[...new Set([...taskStatusOptions, task.status])]
            .map((status) => `<option ${status === task.status ? "selected" : ""}>${status}</option>`)
            .join("")}
        </select>
        <select id="detail-priority">
          ${["P0", "P1", "P2", "P3"].map((priority) => `<option ${priority === task.priority ? "selected" : ""}>${priority}</option>`).join("")}
        </select>
      </div>
      <input id="detail-owner" value="${escapeHtml(task.owner_agent || "")}" placeholder="owner">
      <textarea id="detail-description">${escapeHtml(task.description || "")}</textarea>
      <div class="button-row">
        <button type="submit">Save</button>
        <button id="move-earlier" type="button">Move Earlier</button>
        <button id="move-later" type="button">Move Later</button>
        <button id="archive-task" type="button">Archive</button>
      </div>
      <textarea id="detail-comment" placeholder="Comment or message"></textarea>
      <button id="send-comment" type="button">Send Comment</button>
    </form>
  </article>`;
  $("edit-task-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendJson(`/api/tasks/${encodeURIComponent(task.id)}`, {
      method: "PATCH",
      type: "task.update",
      payload: {
        status: $("detail-status").value,
        priority: $("detail-priority").value,
        owner: $("detail-owner").value,
        description: $("detail-description").value
      }
    });
  });
  $("move-earlier").addEventListener("click", () => sendJson(`/api/tasks/${encodeURIComponent(task.id)}/reorder`, {
    type: "task.reorder",
    payload: { order: Math.max(0, Number(task.order || 0) - 1) }
  }));
  $("move-later").addEventListener("click", () => sendJson(`/api/tasks/${encodeURIComponent(task.id)}/reorder`, {
    type: "task.reorder",
    payload: { order: Number(task.order || 0) + 1 }
  }));
  $("send-comment").addEventListener("click", () => sendJson("/api/messages", {
    type: "task.comment",
    payload: { task_id: task.id, comment: $("detail-comment").value, to: task.owner_agent || "lead-engineer" }
  }));
  $("archive-task").addEventListener("click", () => {
    if (window.confirm(`Archive ${task.id}?`)) {
      sendJson(`/api/tasks/${encodeURIComponent(task.id)}/archive`, { type: "task.archive", payload: {} });
    }
  });
}

function renderAll() {
  renderDashboard();
  renderKanban();
  renderAgents();
  renderMessages();
  renderEvents();
  renderEvidence();
  renderPlanning();
  renderMap();
  renderSources();
  renderCommands();
  renderDetail();
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("is-active"));
    document.querySelectorAll(".view").forEach((item) => item.classList.remove("is-active"));
    tab.classList.add("is-active");
    $(`view-${tab.dataset.view}`).classList.add("is-active");
  });
});

$("refresh-button").addEventListener("click", loadState);
["event-filter-type", "event-filter-agent", "event-filter-task", "event-filter-goal", "event-filter-search"].forEach((id) => {
  const node = $(id);
  if (node) node.addEventListener("input", renderEvents);
});
$("create-task-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendJson("/api/tasks", {
    type: "task.create",
    payload: {
      id: $("new-task-id").value,
      title: $("new-task-title").value,
      description: $("new-task-title").value,
      priority: $("new-task-priority").value,
      status: "planned",
      owner: "lead-engineer"
    }
  });
  $("new-task-id").value = "";
  $("new-task-title").value = "";
});
$("runtime-command-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const commandType = $("runtime-command-type").value;
  const payload = {
    actor: "owner",
    instruction: $("runtime-instruction").value,
    reason: $("runtime-instruction").value,
    task_id: $("runtime-task-id").value,
    goal_id: $("runtime-goal-id").value
  };
  await sendJson("/api/commands", {
    type: commandType,
    payload: {
      type: commandType,
      target: $("runtime-target-agent").value || $("runtime-goal-id").value,
      payload
    }
  });
  $("runtime-instruction").value = "";
});
loadState();
setInterval(loadState, 4000);
"""


def _bytes(text: str) -> bytes:
    return text.encode("utf-8")


def _json_response(payload: object, status: int = 200) -> ConsoleResponse:
    return ConsoleResponse(
        status=status,
        content_type="application/json; charset=utf-8",
        body=_bytes(json.dumps(payload, ensure_ascii=False, indent=2)),
    )


def _decode_json_body(body: bytes | None) -> tuple[dict[str, object], list[str]]:
    if not body:
        return {}, []
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, [f"invalid json body: {exc}"]
    if not isinstance(payload, dict):
        return {}, ["json body must be an object"]
    return payload, []


def _command_response(root_path: Path, command: dict[str, object]) -> ConsoleResponse:
    result = ui_commands.submit_command(root_path, command)
    return _json_response(result, status=400 if result.get("status") == "failed" else 202)


def build_response(path: str, root: Path | str, *, method: str = "GET", body: bytes | None = None) -> ConsoleResponse:
    root_path = Path(root)
    parsed_url = urlparse(path)
    request_path = parsed_url.path
    method = method.upper()
    if method in {"POST", "PATCH"}:
        payload, errors = _decode_json_body(body)
        if errors:
            return _json_response({"status": "failed", "errors": errors}, status=400)
        if method == "POST" and request_path == "/api/commands":
            return _command_response(root_path, payload)
        if method == "POST" and request_path == "/api/tasks":
            return _command_response(root_path, {"type": "task.create", "payload": payload})
        if method == "POST" and request_path == "/api/messages":
            return _command_response(root_path, {"type": "task.comment", "target": payload.get("task_id"), "payload": payload})
        task_match = re_api_task_route(request_path)
        if task_match and method == "PATCH":
            return _command_response(root_path, {"type": "task.update", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "reorder":
            return _command_response(root_path, {"type": "task.reorder", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "archive":
            return _command_response(root_path, {"type": "task.archive", "target": task_match[0], "payload": payload})
        return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")

    if request_path in {"", "/"}:
        return ConsoleResponse(200, "text/html; charset=utf-8", _bytes(HTML))
    if request_path == "/favicon.ico":
        return ConsoleResponse(204, "image/x-icon", b"")
    if request_path == "/app.css":
        return ConsoleResponse(200, "text/css; charset=utf-8", _bytes(CSS))
    if request_path == "/app.js":
        return ConsoleResponse(200, "application/javascript; charset=utf-8", _bytes(JS))
    if request_path == "/api/state":
        return _json_response(ui_state.build_state(root_path))
    if request_path == "/api/events":
        state = ui_state.build_state(root_path)
        filters = {key: values[0] for key, values in parse_qs(parsed_url.query).items() if values}
        return _json_response(
            {
                "generated_at": state["generated_at"],
                "resource": "events",
                "items": ui_state.filter_events(state["events"], filters),
                "sources": state["sources"],
                "gaps": state["gaps"],
                "warnings": state["warnings"],
            }
        )

    api_resources = {
        "/api/tasks": "tasks",
        "/api/agents": "agents",
        "/api/task-sets": "task_sets",
        "/api/task_sets": "task_sets",
        "/api/messages": "messages",
        "/api/goals": "goals",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/replay": "replay",
        "/api/graph": "graph",
        "/api/state-machines": "state_machines",
        "/api/roadmap": "roadmap",
        "/api/planning": "planning",
        "/api/commands": "commands",
    }
    if request_path in api_resources:
        return _json_response(ui_state.build_resource(root_path, api_resources[request_path]))
    return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")


def re_api_task_route(request_path: str) -> tuple[str, str | None] | None:
    parts = [part for part in request_path.split("/") if part]
    if len(parts) == 3 and parts[:2] == ["api", "tasks"]:
        return parts[2], None
    if len(parts) == 4 and parts[:2] == ["api", "tasks"]:
        return parts[2], parts[3]
    return None


class _ConsoleHandler(BaseHTTPRequestHandler):
    root: Path = Path.cwd()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0") or "0")
        return self.rfile.read(length) if length else b""

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root, method="POST", body=self._read_body())
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def do_PATCH(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        response = build_response(self.path, self.root, method="PATCH", body=self._read_body())
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(root: Path, *, host: str = "127.0.0.1", port: int = 8765) -> int:
    root_path = Path(root).resolve()
    handler = type("AgentRuntimeConsoleHandler", (_ConsoleHandler,), {"root": root_path})
    with ThreadingHTTPServer((host, port), handler) as server:
        actual_host, actual_port = server.server_address[:2]
        print(f"Agent Runtime Console: http://{actual_host}:{actual_port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Agent Runtime Console stopped.")
    return 0
