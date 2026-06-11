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
          <button class="tab" type="button" data-view="tasksets">Tasksets</button>
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
        <div id="view-tasksets" class="view">
          <div class="taskset-toolbar">
            <input id="taskset-filter" placeholder="taskset alias, name, task id">
            <select id="taskset-status-filter">
              <option value="">All states</option>
              <option value="active">Active</option>
              <option value="blocked">Blocked</option>
              <option value="planned">Planned</option>
              <option value="completed">Completed</option>
            </select>
          </div>
          <div id="taskset-quick-list" class="taskset-grid"></div>
        </div>
        <div id="view-agents" class="view">
          <div id="multipane-assurance-list" class="assurance-grid"></div>
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
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
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
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
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
.tab:focus-visible,
.taskset-card:focus-visible,
.task-card:focus-visible,
.agent-card:focus-visible,
.command-card:focus-visible,
.audit-card:focus-visible,
.surface-card:focus-visible {
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
  border-color: var(--primary-hover);
  box-shadow: var(--focus);
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
.taskset-strip,
.assurance-grid {
  display: grid;
  gap: 8px;
}
.taskset-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(150px, 0.28fr);
  gap: 8px;
  margin-bottom: 10px;
}
.taskset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 10px;
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
.agent-card,
.assurance-card,
.command-card,
.audit-card,
.surface-card,
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
.agent-card:hover,
.assurance-card:hover,
.command-card:hover,
.audit-card:hover,
.surface-card:hover,
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
.agent-card-meta,
.taskset-card-meta,
.command-card-meta,
.audit-card-meta,
.surface-card-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}
.task-card-meta > span,
.taskset-card-meta > span,
.agent-card-meta > span,
.command-card-meta > span,
.audit-card-meta > span,
.surface-card-meta > span,
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
.taskset-card-meta strong,
.agent-card-meta strong,
.command-card-meta strong,
.audit-card-meta strong,
.surface-card-meta strong,
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
.agent-card-header,
.taskset-card-header,
.command-card-header,
.audit-card-header,
.surface-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
}
.taskset-title {
  display: grid;
  gap: 3px;
  min-width: 0;
}
.taskset-title b {
  font-size: 14px;
}
.taskset-title span {
  color: var(--muted);
  font-size: 12px;
}
.alias-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.alias-row code {
  border: 1px solid rgba(130, 143, 255, 0.24);
  border-radius: 999px;
  padding: 4px 7px;
  background: rgba(94, 106, 210, 0.12);
  color: var(--primary-hover);
  font-size: 11px;
}
.taskset-summary,
.taskset-command {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}
.taskset-command {
  overflow-wrap: anywhere;
}
.taskset-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px;
}
.taskset-action {
  min-height: 32px;
  padding: 7px 9px;
  font-size: 12px;
}
.audit-card p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}
.event-card,
.error-card,
.evidence-card,
.replay-card,
.map-card,
.graph-card,
.state-machine-card,
.roadmap-card,
.planning-card,
.source-card {
  gap: 10px;
}
.audit-card-meta strong,
.surface-card-meta strong,
.evidence-card b,
.replay-card b,
.map-card b,
.planning-card b,
.source-card b {
  color: var(--primary-hover);
}
.surface-card-meta strong.boundary-read,
.surface-card-meta strong.boundary-api,
.command-card-meta strong.boundary-read,
.command-card-meta strong.boundary-api {
  color: var(--teal);
}
.surface-card-meta strong.boundary-write,
.command-card-meta strong.boundary-write {
  color: var(--amber);
}
.agent-score strong {
  color: var(--teal);
}
.agent-claim strong,
.command-card-meta strong {
  color: var(--primary-hover);
}
.agent-status-text,
.command-approval {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.35;
}
.command-payload,
.command-result {
  max-height: 128px;
  white-space: pre-wrap;
}
.task-card b,
.taskset-card b,
.agent-card b,
.command-card b,
.audit-card b,
.surface-card b,
.list-row b {
  overflow-wrap: anywhere;
}
.task-card span,
.taskset-card span,
.agent-card span,
.command-card span,
.audit-card span,
.surface-card span,
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
.task-card .meta-label,
.agent-card .meta-label,
.command-card .meta-label,
.audit-card .meta-label,
.surface-card .meta-label {
  color: var(--subtle);
  font-size: 10px;
  line-height: 1;
}
.task-card code,
.taskset-card code,
.agent-card code,
.command-card code,
.audit-card code,
.surface-card code,
.list-row code {
  color: var(--subtle);
  font-size: 11px;
  overflow-wrap: anywhere;
}
.list-row.ok,
.agent-card.ok,
.command-card.risk-low,
.audit-card.pass,
.surface-card.pass,
.taskset-card.taskset-status-completed,
.task-card.status-completed,
.task-card.status-done {
  border-left: 3px solid var(--success);
}
.list-row.warn,
.agent-card.warn,
.command-card.risk-unknown,
.audit-card.warn,
.surface-card.warn,
.taskset-card.taskset-status-active,
.taskset-card.taskset-status-in-progress,
.taskset-card.taskset-status-planned,
.task-card.status-in-progress,
.task-card.status-active,
.task-card.status-planned,
.task-card.status-ready {
  border-left: 3px solid var(--warning);
}
.list-row.error,
.command-card.risk-high,
.command-card.risk-failed,
.audit-card.fail,
.surface-card.fail,
.taskset-card.taskset-status-blocked,
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
    flex-wrap: wrap;
    padding: 16px;
  }
  .toolbar {
    justify-content: flex-start;
    width: 100%;
  }
  h1 { font-size: 24px; }
  .layout { padding: 14px; }
  .tabs {
    flex-wrap: nowrap;
    margin-inline: -2px;
    overflow-x: auto;
    padding-bottom: 8px;
    scroll-snap-type: x proximity;
  }
  .tab {
    flex: 0 0 auto;
    scroll-snap-align: start;
  }
  .task-card-header,
  .taskset-card-header,
  .agent-card-header,
  .command-card-header,
  .audit-card-header,
  .surface-card-header {
    flex-wrap: wrap;
  }
  .state-chip,
  .pill {
    max-width: 100%;
    overflow-wrap: anywhere;
    white-space: normal;
  }
  .dashboard,
  .kanban,
  .create-form,
  .runtime-form,
  .filter-row,
  .taskset-toolbar,
  .taskset-grid,
  .evidence-grid,
  .task-card-meta,
  .taskset-card-meta,
  .agent-card-meta,
  .command-card-meta,
  .audit-card-meta,
  .surface-card-meta,
  .taskset-actions,
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
  const taskSets = (runtimeState.task_sets || []).filter((taskSet) => taskSet.status !== "completed" || taskSet.active);
  host.innerHTML = taskSets.length ? taskSetCards(taskSets.slice(0, 6), { compact: true }) : "";
}

function taskSetById(taskSetId) {
  return (runtimeState.task_sets || []).find((taskSet) => taskSet.id === taskSetId);
}

function taskSetSearchText(taskSet) {
  return [
    taskSet.id,
    taskSet.display_name,
    taskSet.summary,
    taskSet.status,
    taskSet.next_task_id,
    taskSet.next_task_title,
    ...(taskSet.aliases || []),
    ...(taskSet.task_ids || [])
  ].join(" ").toLowerCase();
}

function filteredTaskSets() {
  const query = $("taskset-filter")?.value.trim().toLowerCase() || "";
  const status = $("taskset-status-filter")?.value.trim() || "";
  return (runtimeState.task_sets || []).filter((taskSet) => {
    if (status && taskSet.status !== status) return false;
    if (query && !taskSetSearchText(taskSet).includes(query)) return false;
    return true;
  });
}

function taskSetCommand(taskSet, action) {
  return (taskSet.commands || {})[action] || "";
}

function taskSetStatusClass(status) {
  const normalized = String(status || "planned").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return `taskset-status-${normalized || "planned"}`;
}

function taskSetInstruction(taskSet, action) {
  const alias = taskSet.primary_alias || taskSet.slug_alias || taskSet.id;
  const command = taskSetCommand(taskSet, action);
  if (action === "plan") {
    return `${alias} 계획: ${command} 실행 후 next task, worktree, claim 경계를 보고해줘.`;
  }
  if (action === "start") {
    return `${alias} 진행: ${command} 실행 후 ${taskSet.id} 범위 안에서만 진행하고 완료 시 정지/보고해줘.`;
  }
  return `${alias} gate 확인: ${command} 실행 후 결과를 보고해줘.`;
}

async function queueTaskSetCommand(taskSet, action) {
  const commandType = action === "gate" ? "runtime.request_review" : "runtime.assign_task";
  await sendJson("/api/commands", {
    type: commandType,
    payload: {
      type: commandType,
      target: "lead-engineer",
      payload: {
        actor: "owner",
        instruction: taskSetInstruction(taskSet, action),
        reason: `${taskSet.primary_alias || taskSet.id} ${action}`,
        task_id: taskSet.next_task_id || "",
        goal_id: taskSet.id
      }
    }
  });
}

function wireTaskSetActions(host) {
  host.querySelectorAll("[data-taskset-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const taskSet = taskSetById(button.dataset.tasksetId);
      if (!taskSet) return;
      queueTaskSetCommand(taskSet, button.dataset.tasksetAction);
    });
  });
}

function taskSetCards(taskSets, options = {}) {
  const compact = Boolean(options.compact);
  return taskSets.map((taskSet) => {
    const aliases = (taskSet.quick_aliases || taskSet.aliases || []).slice(0, compact ? 2 : 4);
    const nextTask = taskSet.next_task_id || "no open task";
    const taskCount = `${taskSet.tasks_done || 0}/${taskSet.tasks_total || 0}`;
    const command = taskSetCommand(taskSet, "start") || taskSetCommand(taskSet, "plan");
    return `
      <article class="taskset-card ${taskSetStatusClass(taskSet.status)}" tabindex="0">
        <div class="taskset-card-header">
          <div class="taskset-title">
            <b>${escapeHtml(taskSet.primary_alias || taskSet.id)}</b>
            <span>${escapeHtml(taskSet.display_name || taskSet.id)}</span>
          </div>
          <span class="state-chip">${escapeHtml(taskSet.letter_alias || taskSet.status || "")}</span>
        </div>
        <div class="alias-row" aria-label="Task set aliases">
          ${aliases.map((alias) => `<code>${escapeHtml(alias)}</code>`).join("")}
        </div>
        ${compact ? "" : `<p class="taskset-summary">${escapeHtml(taskSet.summary || "No summary")}</p>`}
        <div class="taskset-card-meta" aria-label="Task set metadata">
          <span><span class="meta-label">Status</span><strong>${escapeHtml(taskSet.status || "planned")}</strong></span>
          <span><span class="meta-label">Tasks</span><strong>${escapeHtml(taskCount)}</strong></span>
          <span><span class="meta-label">Open</span><strong>${escapeHtml(taskSet.tasks_open || 0)}</strong></span>
          <span><span class="meta-label">Active</span><strong>${escapeHtml(taskSet.active || 0)}</strong></span>
          <span><span class="meta-label">Blocked</span><strong>${escapeHtml(taskSet.tasks_blocked || taskSet.blocked || 0)}</strong></span>
          <span><span class="meta-label">Next</span><strong>${escapeHtml(nextTask)}</strong></span>
        </div>
        ${progressBar(taskSet.progress_pct)}
        ${compact ? "" : `<code class="taskset-command">${escapeHtml(command)}</code>`}
        ${compact ? "" : `<div class="taskset-actions">
          <button class="taskset-action" type="button" data-taskset-action="plan" data-taskset-id="${escapeHtml(taskSet.id)}">Plan</button>
          <button class="taskset-action" type="button" data-taskset-action="start" data-taskset-id="${escapeHtml(taskSet.id)}">Start</button>
          <button class="taskset-action" type="button" data-taskset-action="gate" data-taskset-id="${escapeHtml(taskSet.id)}">Gate</button>
        </div>`}
      </article>
    `;
  }).join("");
}

function renderTaskSetDirectory() {
  const host = $("taskset-quick-list");
  if (!host) return;
  const taskSets = filteredTaskSets();
  host.innerHTML = taskSets.length ? taskSetCards(taskSets) : `<div class="empty">No task sets</div>`;
  wireTaskSetActions(host);
}

function renderMultipaneAssurance() {
  const host = $("multipane-assurance-list");
  if (!host) return;
  const assurance = runtimeState.multipane_assurance || {};
  const census = assurance.census || {};
  const process = assurance.process || {};
  const drift = assurance.drift || {};
  const roleCoverage = assurance.role_coverage || {};
  const activePanes = census.active_claims || 0;
  const roleCount = Object.keys(roleCoverage).length;
  const driftCount = ((drift.watch || []).length || 0) + ((drift.block || []).length || 0);
  host.innerHTML = `
    <article class="assurance-card ${escapeHtml(assurance.status || "watch")}">
      <div class="agent-card-header">
        <b>Multi-pane assurance</b>
        <span class="state-chip">${escapeHtml(assurance.status || "unknown")}</span>
      </div>
      <div class="agent-card-meta" aria-label="Multi-pane assurance metadata">
        <span><span class="meta-label">active panes</span><strong>${escapeHtml(activePanes)}</strong></span>
        <span><span class="meta-label">role coverage</span><strong>${escapeHtml(roleCount)}</strong></span>
        <span><span class="meta-label">drift</span><strong>${escapeHtml(driftCount)}</strong></span>
        <span><span class="meta-label">process</span><strong>${escapeHtml(process.status || "unknown")}</strong></span>
        <span><span class="meta-label">events</span><strong>${escapeHtml((assurance.event_summary || {}).event_count || 0)}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml((assurance.source_paths || {}).policy || "multipane assurance")}</strong></span>
      </div>
    </article>
  `;
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
  const taskSetInfo = taskSetById(task.task_set_id);
  const taskSet = taskSetInfo
    ? `${taskSetInfo.primary_alias || taskSetInfo.id} - ${taskSetInfo.display_name || taskSetInfo.id}`
    : task.task_set_id || "no task set";
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

function agentProgressLabel(agent) {
  const pct = numericPct(agent.progress_pct);
  return pct === null ? "~" : `${pct}%`;
}

function renderAgents() {
  renderMultipaneAssurance();
  renderTaskSets();
  const agents = runtimeState.agents || [];
  $("agents-list").innerHTML = agents.length ? agents.map((agent) => `
    <article class="agent-card ${agent.online ? "ok" : "warn"}">
      <div class="agent-card-header">
        <b>${escapeHtml(agent.display_name || agent.role || "agent")}</b>
        <span class="state-chip">${escapeHtml(agent.status || "offline")}</span>
      </div>
      <div class="agent-card-meta" aria-label="Agent metadata">
        <span><span class="meta-label">Role</span><strong>${escapeHtml(agent.role || "unknown")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(agent.status || "offline")}</strong></span>
        <span class="agent-score"><span class="meta-label">Score</span><strong>${escapeHtml(agent.score_label || "not scored")}</strong></span>
        <span class="agent-claim"><span class="meta-label">Claim</span><strong>${escapeHtml(agent.claim_id || agent.current_task_id || "no claim")}</strong></span>
        <span><span class="meta-label">Progress</span><strong>${escapeHtml(agent.step_index && agent.step_total ? `${agent.step_index}/${agent.step_total} - ${agentProgressLabel(agent)}` : agentProgressLabel(agent))}</strong></span>
        <span><span class="meta-label">Task set</span><strong>${escapeHtml(agent.task_set_id || "no task set")}</strong></span>
      </div>
      ${progressBar(agent.progress_pct)}
      <span class="agent-status-text">${escapeHtml(agent.status_text || agent.phase || "working")}</span>
      <code>${escapeHtml(agent.source_path || agent.worktree_path || "")}</code>
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

function auditSeverityLabel(row, fallback = "info") {
  return String(row.severity || row.status || row.event || row.type || row.kind || fallback);
}

function auditToneClass(row, fallback = "pass") {
  const text = JSON.stringify(row || {}).toLowerCase();
  if (text.includes("error") || text.includes("failed") || text.includes("fail") || text.includes("blocked")) return "fail";
  if (text.includes("warn") || text.includes("missing") || text.includes("gap") || text.includes("hold")) return "warn";
  if (text.includes("completed") || text.includes("done") || text.includes("pass") || text.includes("ok")) return "pass";
  return fallback;
}

function renderAuditMeta(content) {
  return `<div class="audit-card-meta" aria-label="Audit metadata">${content}</div>`;
}

function renderEvents() {
  const events = filterEvents(runtimeState.events || []);
  $("events-list").innerHTML = events.length ? events.slice(-80).reverse().map((event) => `
    <article class="audit-card event-card ${auditToneClass(event)}">
      <div class="audit-card-header">
        <b>${escapeHtml(event.type || event.event || event.id || "event")}</b>
        <span class="state-chip">${escapeHtml(auditSeverityLabel(event))}</span>
      </div>
      ${renderAuditMeta(`
        <span><span class="meta-label">Event</span><strong>${escapeHtml(event.type || event.event || "unknown")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>${escapeHtml(auditSeverityLabel(event))}</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(event.actor || event.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(event.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(event.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(event.source_path || event.id || "event stream")}</strong></span>
      `)}
      ${event.error || event.message ? `<p>${escapeHtml(event.error || event.message)}</p>` : ""}
      <code>${escapeHtml(event.id || event.created_at || event.ts || "")}</code>
    </article>
  `).join("") : `<div class="empty">No events</div>`;
}

function renderEvidence() {
  const errors = runtimeState.errors || [];
  const evidence = runtimeState.evidence || [];
  const replay = runtimeState.replay || [];
  $("errors-list").innerHTML = errors.length ? errors.slice(-40).reverse().map((item) => `
    <article class="audit-card error-card fail">
      <div class="audit-card-header">
        <b>${escapeHtml(item.message || item.error || "runtime error")}</b>
        <span class="state-chip">fail</span>
      </div>
      ${renderAuditMeta(`
        <span><span class="meta-label">Event</span><strong>${escapeHtml(item.event_id || item.type || "error")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>fail</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.event_id || "error stream")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No recent errors</div>`;
  $("evidence-list").innerHTML = evidence.length ? evidence.slice(-60).reverse().map((item) => `
    <article class="audit-card evidence-card pass">
      <div class="audit-card-header">
        <b>${escapeHtml(item.evidence || item.source_path || "evidence")}</b>
        <span class="state-chip">pass</span>
      </div>
      ${renderAuditMeta(`
        <span><span class="meta-label">Evidence</span><strong>${escapeHtml(item.evidence || "linked")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>pass</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || item.source_type || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.source_id || "evidence index")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No evidence links</div>`;
  $("replay-list").innerHTML = replay.length ? replay.slice(-80).reverse().map((item) => `
    <article class="audit-card replay-card ${auditToneClass(item, "warn")}">
      <div class="audit-card-header">
        <b>${escapeHtml(item.type || item.kind || "replay")}</b>
        <span class="state-chip">${escapeHtml(auditSeverityLabel(item, "replay"))}</span>
      </div>
      ${renderAuditMeta(`
        <span><span class="meta-label">Replay</span><strong>${escapeHtml(item.type || item.kind || "record")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>${escapeHtml(auditSeverityLabel(item, "replay"))}</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.source_id || "replay log")}</strong></span>
      `)}
      ${item.summary ? `<p>${escapeHtml(item.summary)}</p>` : ""}
    </article>
  `).join("") : `<div class="empty">No replay records</div>`;
}

function boundaryLabel(value, fallback = "read-only") {
  return String(value || fallback).replace(/_/g, " ");
}

function boundaryClass(value) {
  const text = boundaryLabel(value).toLowerCase();
  if (text.includes("write") || text.includes("mutation") || text.includes("command")) return "boundary-write";
  if (text.includes("api") || text.includes("outbox")) return "boundary-api";
  return "boundary-read";
}

function renderSurfaceMeta(content) {
  return `<div class="surface-card-meta" aria-label="Surface metadata">${content}</div>`;
}

function surfaceTone(row, fallback = "pass") {
  const text = JSON.stringify(row || {}).toLowerCase();
  if (text.includes("failed") || text.includes("error") || text.includes("block")) return "fail";
  if (text.includes("warn") || text.includes("watch") || text.includes("pending") || text.includes("missing")) return "warn";
  return fallback;
}

function renderMap() {
  const graph = runtimeState.graph || { nodes: [], edges: [] };
  const machines = runtimeState.state_machines || [];
  const roadmap = runtimeState.roadmap || { milestones: [] };
  $("graph-list").innerHTML = graph.edges.length ? graph.edges.slice(0, 80).map((edge) => `
    <article class="surface-card map-card graph-card pass">
      <div class="surface-card-header">
        <b>${escapeHtml(edge.from)} -> ${escapeHtml(edge.to)}</b>
        <span class="state-chip">read-only</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">From</span><strong>${escapeHtml(edge.from || "unknown")}</strong></span>
        <span><span class="meta-label">To</span><strong>${escapeHtml(edge.to || "unknown")}</strong></span>
        <span><span class="meta-label">Kind</span><strong>${escapeHtml(edge.kind || "edge")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("read-only")}">${escapeHtml(boundaryLabel("read-only"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(edge.source_path || edge.id || "graph")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(edge.task_id || "no task")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No graph edges</div>`;
  $("state-machine-list").innerHTML = machines.length ? machines.map((machine) => `
    <article class="surface-card map-card state-machine-card pass">
      <div class="surface-card-header">
        <b>${escapeHtml(machine.id)}: ${escapeHtml(machine.current_state || machine.initial || "unknown")}</b>
        <span class="state-chip">read-only</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>state machine</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(machine.current_state || machine.initial || "unknown")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("read-only")}">${escapeHtml(boundaryLabel("read-only"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(machine.source_path || "state machine file")}</strong></span>
        <span><span class="meta-label">From</span><strong>${escapeHtml(machine.initial || "initial")}</strong></span>
        <span><span class="meta-label">To</span><strong>${escapeHtml((machine.states || []).join(" -> ") || "states")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No state machines</div>`;
  $("roadmap-list").innerHTML = (roadmap.milestones || []).length ? (roadmap.milestones || []).slice(0, 40).map((item) => `
    <article class="surface-card map-card roadmap-card ${item.done ? "pass" : "warn"}">
      <div class="surface-card-header">
        <b>${escapeHtml(item.date)} - ${escapeHtml(item.title)}</b>
        <span class="state-chip">${escapeHtml(item.done ? "done" : "open")}</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>roadmap</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(item.done ? "done" : "open")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("read-only")}">${escapeHtml(boundaryLabel("read-only"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(roadmap.source_path || "roadmap")}</strong></span>
        <span><span class="meta-label">From</span><strong>${escapeHtml(roadmap.phase || "phase")}</strong></span>
        <span><span class="meta-label">To</span><strong>${escapeHtml(item.title || "milestone")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No roadmap milestones</div>`;
}

function renderPlanning() {
  const planning = runtimeState.planning || { scan_reports: [], proposals: [], requests: [], draft_tasks: [], applied: [], summary: {} };
  const proposals = planning.proposals || [];
  const scans = planning.scan_reports || [];
  const requests = [...(planning.requests || []), ...(planning.draft_tasks || []), ...(planning.applied || [])];
  $("planning-proposals-list").innerHTML = proposals.length ? proposals.slice(0, 80).map((row) => `
    <article class="surface-card planning-card ${surfaceTone(row, row.risk_tier === "high" || row.status === "blocked" ? "warn" : "pass")}">
      <div class="surface-card-header">
        <b>${escapeHtml(row.id || row.title || "proposal")}</b>
        <span class="state-chip">${escapeHtml(row.status || "unknown")}</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>${escapeHtml(row.action_type || "proposal")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(row.status || "unknown")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml(row.risk_tier || "unknown")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass(row.owner_boundary || "proposal-only")}">${escapeHtml(boundaryLabel(row.owner_boundary || "proposal-only"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(row.source_path || (row.source_refs || [])[0]?.path || "planning proposal")}</strong></span>
        <span><span class="meta-label">Mutation</span><strong>${escapeHtml(row.suggested_next_action || "no direct mutation")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No planning proposals</div>`;
  $("planning-scans-list").innerHTML = scans.length ? scans.slice(0, 40).map((row) => `
    <article class="surface-card planning-card ${surfaceTone(row, row.status === "block" || row.status === "watch" ? "warn" : "pass")}">
      <div class="surface-card-header">
        <b>${escapeHtml(row.id || "scan")}</b>
        <span class="state-chip">${escapeHtml(row.status || "unknown")}</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>${escapeHtml(row.trigger || "manual scan")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(row.status || "unknown")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml((row.summary || {}).finding_count || 0)} findings</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("read-only scan")}">${escapeHtml(boundaryLabel("read-only scan"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(row.source_path || "planning scan")}</strong></span>
        <span><span class="meta-label">Mutation</span><strong>none</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No planning scans</div>`;
  $("planning-requests-list").innerHTML = requests.length ? requests.slice(0, 80).map((row) => `
    <article class="surface-card planning-card ${surfaceTone(row)}">
      <div class="surface-card-header">
        <b>${escapeHtml(row.id || row.source_path || "planning record")}</b>
        <span class="state-chip">${escapeHtml(row.status || row.source_kind || "record")}</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>${escapeHtml(row.type || row.mode || "planning")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(row.status || row.source_kind || "record")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml(row.risk_tier || "unknown")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass(row.mutation_boundary || "proposal-only")}">${escapeHtml(boundaryLabel(row.mutation_boundary || "proposal-only"))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(row.source_path || "planning record")}</strong></span>
        <span><span class="meta-label">Mutation</span><strong>${escapeHtml(row.action || "queued record")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No planning requests, drafts, or apply records</div>`;
}

function renderSources() {
  const rows = [...(runtimeState.sources || []), ...(runtimeState.gaps || []), ...(runtimeState.warnings || [])];
  $("sources-list").innerHTML = rows.length ? rows.map((row) => `
    <article class="surface-card source-card ${row.fresh === false || row.kind?.includes("error") ? "warn" : "pass"}">
      <div class="surface-card-header">
        <b>${escapeHtml(row.id || row.kind || "source")}</b>
        <span class="state-chip">${escapeHtml(row.freshness || row.detail || "source")}</span>
      </div>
      ${renderSurfaceMeta(`
        <span><span class="meta-label">Kind</span><strong>${escapeHtml(row.kind || "source")}</strong></span>
        <span><span class="meta-label">Status</span><strong>${escapeHtml(row.fresh === false ? "watch" : "pass")}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass(row.mutation_boundary)}">${escapeHtml(boundaryLabel(row.mutation_boundary))}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(row.path || "no path")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml(row.detail || row.freshness || "known")}</strong></span>
        <span><span class="meta-label">Mutation</span><strong>${escapeHtml(row.mutation_boundary || "read-only")}</strong></span>
      `)}
    </article>
  `).join("") : `<div class="empty">No sources</div>`;
}

function formatCommandValue(value) {
  if (value === undefined || value === null || value === "") return "none";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch (error) {
    return String(value);
  }
}

function commandRiskClass(row) {
  if (row.status === "failed") return "risk-failed";
  if (row.approval_required || row.risk_level === "high") return "risk-high";
  if (row.risk_level === "low" || row.status === "accepted" || row.status === "queued") return "risk-low";
  return "risk-unknown";
}

function renderCommands() {
  const rows = [...pendingWrites, ...((runtimeState && runtimeState.commands) || [])];
  const host = $("command-log");
  if (!host) return;
  host.innerHTML = rows.length ? rows.slice(0, 80).map((row) => `
    <article class="command-card ${commandRiskClass(row)}">
      <div class="command-card-header">
        <b>${escapeHtml(row.id || row.type || "command")}</b>
        <span class="state-chip">${escapeHtml(row.status || "pending")}</span>
      </div>
      <div class="command-card-meta" aria-label="Command metadata">
        <span><span class="meta-label">Type</span><strong>${escapeHtml(row.type || "command")}</strong></span>
        <span><span class="meta-label">Target</span><strong>${escapeHtml(row.target || "no target")}</strong></span>
        <span><span class="meta-label">Risk</span><strong>${escapeHtml(row.risk_level || (row.approval_required ? "high" : "unknown"))}</strong></span>
        <span><span class="meta-label">Boundary</span><strong class="${boundaryClass("write command")}">${escapeHtml(boundaryLabel("write command"))}</strong></span>
      </div>
      <div>
        <span class="meta-label">Payload</span>
        <pre class="command-payload">${escapeHtml(formatCommandValue(row.payload))}</pre>
      </div>
      <div>
        <span class="meta-label">Result</span>
        <pre class="command-result">${escapeHtml(formatCommandValue(row.result || row.errors || row.status))}</pre>
      </div>
      ${row.approval_required ? `<p class="command-approval">approval required: ${escapeHtml((row.approval_reasons || []).join(", ") || "owner review")}</p>` : ""}
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
  renderTaskSetDirectory();
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
["taskset-filter", "taskset-status-filter"].forEach((id) => {
  const node = $(id);
  if (node) {
    node.addEventListener("input", renderTaskSetDirectory);
    node.addEventListener("change", renderTaskSetDirectory);
  }
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
