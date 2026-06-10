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
          <button class="tab" type="button" data-view="sources">Sources</button>
          <button class="tab" type="button" data-view="writes">Writes</button>
        </nav>

        <div id="view-board" class="view is-active">
          <div id="kanban" class="kanban" aria-label="Kanban"></div>
        </div>
        <div id="view-agents" class="view">
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
  --paper: #f4f1ea;
  --panel: #fffaf0;
  --ink: #1e2320;
  --muted: #6f756e;
  --line: #d8d1c2;
  --teal: #0f766e;
  --blue: #1d4ed8;
  --amber: #b7791f;
  --red: #b42318;
  --violet: #6d28d9;
  --shadow: 0 18px 44px rgba(39, 32, 21, 0.10);
}

* { box-sizing: border-box; }

body {
  margin: 0;
  color: var(--ink);
  background:
    linear-gradient(90deg, rgba(30, 35, 32, 0.04) 1px, transparent 1px),
    linear-gradient(0deg, rgba(30, 35, 32, 0.04) 1px, transparent 1px),
    var(--paper);
  background-size: 24px 24px;
  font-family: "Aptos", "Segoe UI", sans-serif;
}

.shell { min-height: 100vh; padding: 16px; }

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 16px;
  border: 1px solid var(--line);
  background: rgba(255, 250, 240, 0.92);
  box-shadow: var(--shadow);
}

.brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.brand-mark { width: 44px; height: 44px; flex: 0 0 auto; fill: #f8efe0; stroke: var(--ink); stroke-width: 2; }
h1 { margin: 0; font-size: 18px; line-height: 1.15; letter-spacing: 0; }
p { margin: 4px 0 0; color: var(--muted); }

.toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
button {
  min-height: 36px;
  border: 1px solid var(--ink);
  border-radius: 6px;
  background: var(--ink);
  color: var(--panel);
  font: inherit;
  cursor: pointer;
}
button:hover { filter: brightness(1.08); }
.state-chip {
  display: inline-flex;
  align-items: center;
  min-height: 32px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: #edf7f4;
  color: var(--teal);
  font-size: 13px;
}

.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 360px);
  grid-template-areas:
    "dashboard detail"
    "work detail";
  gap: 16px;
  margin-top: 16px;
}

.dashboard { grid-area: dashboard; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.metric {
  min-height: 88px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}
.metric span { display: block; color: var(--muted); font-size: 13px; }
.metric strong { display: block; margin-top: 8px; font-size: 30px; line-height: 1; }

.work-surface { grid-area: work; min-width: 0; }
.create-form {
  display: grid;
  grid-template-columns: minmax(110px, 160px) minmax(180px, 1fr) minmax(84px, 100px) minmax(88px, auto);
  gap: 8px;
  margin-bottom: 12px;
}
.runtime-form {
  display: grid;
  grid-template-columns: minmax(140px, 180px) minmax(120px, 160px) minmax(120px, 160px) minmax(120px, 160px) minmax(220px, 1fr) minmax(88px, auto);
  gap: 8px;
  margin-bottom: 12px;
}
input, select, textarea {
  min-height: 36px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #ffffff;
  color: var(--ink);
  font: inherit;
}
textarea { min-height: 74px; resize: vertical; }
.tabs { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; }
.tab { flex: 0 0 auto; background: #ffffff; color: var(--ink); border-color: var(--line); padding: 0 12px; }
.tab.is-active { background: var(--teal); border-color: var(--teal); color: #ffffff; }
.view { display: none; }
.view.is-active { display: block; }
.filter-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}
.evidence-grid h2 {
  margin: 0 0 8px;
  font-size: 15px;
  letter-spacing: 0;
}

.kanban {
  display: grid;
  grid-template-columns: repeat(6, minmax(180px, 1fr));
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 6px;
}
.lane {
  min-height: 460px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 250, 240, 0.88);
}
.lane header {
  position: sticky;
  top: 0;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 10px;
  border-bottom: 1px solid var(--line);
  background: #fffdf7;
  font-weight: 700;
}
.lane-body { display: grid; gap: 8px; padding: 10px; }
.task-card {
  width: 100%;
  min-height: 92px;
  padding: 10px;
  text-align: left;
  border-color: var(--line);
  background: #ffffff;
  color: var(--ink);
}
.task-card strong { display: block; font-size: 13px; overflow-wrap: anywhere; }
.task-card span { display: block; margin-top: 6px; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
.task-card small { display: inline-block; margin-top: 8px; color: var(--teal); font-weight: 700; }

.list-panel {
  display: grid;
  gap: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
  padding: 12px;
  min-height: 360px;
}
.list-row {
  padding: 10px;
  border: 1px solid var(--line);
  border-left: 4px solid var(--blue);
  border-radius: 6px;
  background: #ffffff;
  overflow-wrap: anywhere;
}
.list-row.warn { border-left-color: var(--amber); }
.list-row.error { border-left-color: var(--red); }
.list-row.ok { border-left-color: var(--teal); }
.list-row b { display: block; margin-bottom: 4px; }
.list-row code { font-family: "Cascadia Mono", Consolas, monospace; font-size: 12px; }

.detail-panel {
  grid-area: detail;
  position: sticky;
  top: 16px;
  align-self: start;
  max-height: calc(100vh - 32px);
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fffdf7;
  box-shadow: var(--shadow);
}
.detail-panel article { padding: 14px; }
.detail-panel h2 { margin: 0 0 10px; font-size: 18px; letter-spacing: 0; }
.detail-empty { padding: 16px; color: var(--muted); }
.meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 14px; }
.meta-grid div { padding: 8px; border: 1px solid var(--line); border-radius: 6px; background: #ffffff; }
.meta-grid span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; }
.meta-grid strong { display: block; margin-top: 4px; font-size: 12px; overflow-wrap: anywhere; }
.edit-form { display: grid; gap: 8px; margin-top: 14px; }
.edit-row { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.button-row { display: flex; flex-wrap: wrap; gap: 8px; }

.empty {
  display: grid;
  place-items: center;
  min-height: 140px;
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.58);
}

@media (max-width: 960px) {
  .layout { grid-template-columns: 1fr; grid-template-areas: "dashboard" "work" "detail"; }
  .detail-panel { position: static; max-height: none; }
  .dashboard { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 560px) {
  .shell { padding: 10px; }
  .topbar { align-items: flex-start; flex-direction: column; }
  .toolbar { justify-content: flex-start; }
  .create-form { grid-template-columns: 1fr; }
  .runtime-form { grid-template-columns: 1fr; }
  .dashboard { grid-template-columns: 1fr; }
  .kanban { grid-template-columns: repeat(6, minmax(220px, 84vw)); }
  .filter-row, .evidence-grid { grid-template-columns: 1fr; }
  .meta-grid { grid-template-columns: 1fr; }
}
"""


JS = """const lanes = ["Backlog", "Ready", "In Progress", "Review", "Blocked", "Done"];
const runtimeCommandTypes = ["runtime.call_agent", "runtime.assign_task", "runtime.request_review", "runtime.request_meeting", "runtime.goal.start", "runtime.goal.pause", "runtime.goal.resume", "runtime.goal.stop"];
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

function renderDashboard() {
  const tasks = runtimeState.tasks || [];
  const counts = taskCounts(tasks);
  setText("metric-tasks", tasks.length);
  setText("metric-active", counts.active);
  setText("metric-blocked", counts.blocked);
  setText("metric-warnings", (runtimeState.warnings || []).length + (runtimeState.gaps || []).length);
  $("status-line").textContent = `Generated ${runtimeState.generated_at} - ${tasks.length} tasks`;
}

function taskCard(task) {
  return `<button class="task-card" type="button" data-task-id="${escapeHtml(task.id)}">
    <strong>${escapeHtml(task.id)} - ${escapeHtml(task.title)}</strong>
    <span>${escapeHtml(task.description || "No summary")}</span>
    <small>${escapeHtml(task.owner_agent || "unassigned")} / ${escapeHtml(task.priority || "P?")}</small>
  </button>`;
}

function renderKanban() {
  const tasks = runtimeState.tasks || [];
  $("kanban").innerHTML = lanes.map((lane) => {
    const laneTasks = tasks.filter((task) => task.lane === lane);
    const body = laneTasks.length ? laneTasks.map(taskCard).join("") : `<div class="empty">No ${escapeHtml(lane)} tasks</div>`;
    return `<section class="lane"><header><span>${escapeHtml(lane)}</span><span>${laneTasks.length}</span></header><div class="lane-body">${body}</div></section>`;
  }).join("");
  document.querySelectorAll(".task-card").forEach((button) => {
    button.addEventListener("click", () => {
      selectedTaskId = button.dataset.taskId;
      renderDetail();
    });
  });
}

function renderAgents() {
  const agents = runtimeState.agents || [];
  $("agents-list").innerHTML = agents.length ? agents.map((agent) => `
    <article class="list-row ${agent.online ? "ok" : "warn"}">
      <b>${escapeHtml(agent.display_name || agent.role)}</b>
      <span>${escapeHtml(agent.status || "offline")} / ${escapeHtml(agent.current_task_id || "no task")}</span>
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
          ${["planned", "ready", "in_progress", "review", "blocked", "completed"].map((status) => `<option ${status === task.status ? "selected" : ""}>${status}</option>`).join("")}
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
        "/api/messages": "messages",
        "/api/goals": "goals",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/replay": "replay",
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
