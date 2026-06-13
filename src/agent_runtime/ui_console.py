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
          <button class="tab" type="button" data-view="work">Work Explorer</button>
          <button class="tab" type="button" data-view="meeting">Meeting Room</button>
          <button class="tab" type="button" data-view="tasksets">Tasksets</button>
          <button class="tab" type="button" data-view="tsboard">Taskset Board</button>
          <button class="tab" type="button" data-view="agents">Agents</button>
          <button class="tab" type="button" data-view="messages">Messages</button>
          <button class="tab" type="button" data-view="events">Events</button>
          <button class="tab" type="button" data-view="evidence">Evidence</button>
          <button class="tab" type="button" data-view="planner">Planner</button>
          <button class="tab" type="button" data-view="roadmap">Roadmap</button>
          <button class="tab" type="button" data-view="map">Map</button>
          <button class="tab" type="button" data-view="sources">Sources</button>
          <button class="tab" type="button" data-view="writes">Writes</button>
        </nav>

        <div id="view-board" class="view is-active">
          <div id="kanban" class="kanban" aria-label="Kanban"></div>
        </div>
        <div id="view-work" class="view">
          <div class="work-toolbar">
            <input id="work-search" placeholder="search work items">
            <select id="work-depth-filter" aria-label="Work tree depth">
              <option value="3">All levels</option>
              <option value="0">Initiatives</option>
              <option value="1">+ Tasksets</option>
              <option value="2">+ Tasks</option>
            </select>
            <button id="work-expand-all" type="button">Expand all</button>
            <button id="work-collapse-all" type="button">Collapse all</button>
          </div>
          <p id="work-staleness" class="work-staleness"></p>
          <div id="work-facets" class="work-facets" aria-label="Work facet filters"></div>
          <div class="work-grid">
            <div id="work-tree" class="work-tree" aria-label="Work Explorer tree"></div>
            <aside id="work-node-detail" class="work-node-detail" aria-label="Work node detail"></aside>
          </div>
        </div>
        <div id="view-meeting" class="view">
          <div class="meeting-grid">
            <section class="meeting-roster" aria-label="Available agents">
              <h2>Available agents</h2>
              <p class="meeting-hint">Drag a card into the room, or focus a card and press Enter to add it. Keyboard: Enter/Space adds; Delete removes a participant.</p>
              <div id="meeting-available" class="meeting-card-list" aria-label="Available agent cards"></div>
            </section>
            <section class="meeting-room" aria-label="Meeting room">
              <h2>Meeting room</h2>
              <div id="meeting-dropzone" class="meeting-dropzone" role="group" aria-label="Participant drop zone" aria-dropeffect="move" tabindex="0">
                <p class="meeting-dropzone-empty">Drop agents here to add participants</p>
                <div id="meeting-participants" class="meeting-participant-list" aria-label="Selected participants"></div>
              </div>
              <form id="meeting-config-form" class="meeting-config" aria-label="Meeting configuration">
                <label class="meeting-field">
                  <span>Topic</span>
                  <input id="meeting-topic" name="topic" placeholder="meeting topic or pick a task">
                </label>
                <label class="meeting-field">
                  <span>Task</span>
                  <select id="meeting-task" name="task_id">
                    <option value="">(free-form topic)</option>
                  </select>
                </label>
                <label class="meeting-field">
                  <span>Type</span>
                  <select id="meeting-type" name="meeting_type">
                    <option value="meeting">meeting</option>
                    <option value="seminar">seminar</option>
                    <option value="review">review</option>
                  </select>
                </label>
                <label class="meeting-field">
                  <span>Rounds</span>
                  <input id="meeting-rounds" name="rounds" type="number" min="1" max="20" value="3">
                </label>
                <button id="meeting-start" type="submit">Start meeting</button>
              </form>
              <p id="meeting-validation" class="meeting-validation" role="status" aria-live="polite"></p>
            </section>
          </div>
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
        <div id="view-tsboard" class="view">
          <div class="tsboard-toolbar">
            <input id="tsboard-filter" placeholder="taskset, task id, owner">
            <label class="tsboard-swimlane-toggle">
              <input id="tsboard-swimlane-toggle" type="checkbox">
              <span>Kanban swimlanes</span>
            </label>
            <button id="tsboard-expand-all" type="button">Expand all</button>
            <button id="tsboard-collapse-all" type="button">Collapse all</button>
          </div>
          <p id="tsboard-staleness" class="tsboard-staleness"></p>
          <div id="tsboard-cards" class="tsboard-cards" aria-label="Taskset board"></div>
          <div id="tsboard-swimlanes" class="tsboard-swimlanes" aria-label="Taskset swimlanes" hidden></div>
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
        <div id="view-roadmap" class="view">
          <p id="roadmap-timeline-summary" class="roadmap-timeline-summary" role="status"></p>
          <div id="roadmap-timeline" class="roadmap-timeline" aria-label="Roadmap timeline"></div>
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
.task-card .task-card-inflight {
  color: var(--amber);
  font-size: 11px;
  line-height: 1.3;
  overflow-wrap: anywhere;
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
.work-toolbar {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(150px, 0.4fr) auto auto;
  gap: 8px;
  margin-bottom: 8px;
}
.work-staleness {
  color: var(--subtle);
  font-size: 11px;
  margin-bottom: 8px;
  overflow-wrap: anywhere;
}
.work-facets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.facet-group {
  min-width: 0;
  margin: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 6px 8px;
}
.facet-group legend {
  color: var(--subtle);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  padding: 0 4px;
}
.facet-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-width: 460px;
}
.facet-option {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 3px 9px;
  color: var(--muted);
  font-size: 11px;
  cursor: pointer;
}
.facet-option:hover { border-color: var(--line-strong); }
.facet-option input {
  width: auto;
  min-width: 0;
  padding: 0;
  margin: 0;
  accent-color: var(--primary);
}
.work-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(240px, 1fr);
  gap: 10px;
  align-items: start;
}
.work-tree {
  display: grid;
  gap: 4px;
  min-width: 0;
}
.work-node {
  display: grid;
  gap: 4px;
  min-width: 0;
}
.work-node-children {
  display: grid;
  gap: 4px;
  margin-left: 18px;
  min-width: 0;
}
.work-node-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.044);
  color: var(--ink);
  padding: 8px 10px;
  text-align: left;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.026);
}
.work-node-row:hover { border-color: var(--line-strong); }
.work-node-row:focus-visible {
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
  box-shadow: var(--focus);
}
.work-node-row.is-selected {
  border-color: var(--primary-hover);
  box-shadow: var(--focus);
}
.work-node-row.bucket-completed { border-left: 3px solid var(--success); }
.work-node-row.bucket-in-progress { border-left: 3px solid var(--warning); }
.work-node-row.bucket-planned { border-left: 3px solid var(--line-strong); }
.work-toggle {
  min-height: 24px;
  min-width: 24px;
  padding: 2px 6px;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-size: 11px;
}
.work-node-number {
  color: var(--primary-hover);
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 11px;
  white-space: nowrap;
}
.work-node-id {
  color: var(--ink);
  font-size: 12px;
  font-weight: 700;
  overflow-wrap: anywhere;
}
.work-node-title {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.3;
  min-width: 0;
  flex: 1 1 180px;
  overflow-wrap: anywhere;
}
.rollup-badge {
  border: 1px solid rgba(49, 208, 170, 0.24);
  border-radius: 999px;
  background: rgba(49, 208, 170, 0.10);
  color: var(--teal);
  font-size: 11px;
  padding: 3px 8px;
  white-space: nowrap;
}
.evidence-badge {
  border: 1px solid rgba(130, 143, 255, 0.24);
  border-radius: 999px;
  background: rgba(94, 106, 210, 0.12);
  color: var(--primary-hover);
  font-size: 11px;
  padding: 3px 8px;
  white-space: nowrap;
}
.work-node-detail {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.026);
  padding: 10px;
  display: grid;
  gap: 8px;
  min-width: 0;
}
.work-node-detail h3 {
  font-size: 14px;
  overflow-wrap: anywhere;
}
.work-node-detail p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}
.work-detail-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
}
.work-detail-meta > span {
  min-width: 0;
  border: 1px solid rgba(52, 56, 68, 0.76);
  border-radius: 6px;
  background: rgba(1, 1, 2, 0.34);
  padding: 6px;
}
.work-detail-meta strong {
  display: block;
  margin-top: 4px;
  color: var(--ink);
  font-size: 11px;
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.evidence-ref {
  display: block;
  color: var(--subtle);
  font-size: 11px;
  overflow-wrap: anywhere;
}
.meeting-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(0, 1.6fr);
  gap: 12px;
  align-items: start;
}
.meeting-roster,
.meeting-room {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: rgba(255, 255, 255, 0.026);
  padding: 12px;
  min-width: 0;
}
.meeting-roster h2,
.meeting-room h2 {
  font-size: 14px;
  margin-bottom: 6px;
}
.meeting-hint {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
  margin-bottom: 8px;
}
.meeting-card-list,
.meeting-participant-list {
  display: grid;
  gap: 6px;
}
.meeting-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--line-strong);
  border-radius: 8px;
  background: rgba(1, 1, 2, 0.34);
  padding: 8px;
  cursor: grab;
  min-width: 0;
}
.meeting-card:focus-visible {
  outline: 2px solid var(--accent, #5b8def);
  outline-offset: 1px;
}
.meeting-card.is-placed {
  opacity: 0.45;
}
.meeting-card-name {
  font-size: 12px;
  overflow-wrap: anywhere;
}
.meeting-card-meta {
  color: var(--muted);
  font-size: 10px;
  white-space: nowrap;
}
.meeting-dropzone {
  border: 2px dashed var(--line-strong);
  border-radius: var(--radius);
  background: rgba(1, 1, 2, 0.24);
  padding: 12px;
  min-height: 96px;
  margin-bottom: 10px;
}
.meeting-dropzone.is-dragover {
  border-color: var(--accent, #5b8def);
  background: rgba(91, 141, 239, 0.12);
}
.meeting-dropzone:focus-visible {
  outline: 2px solid var(--accent, #5b8def);
  outline-offset: 1px;
}
.meeting-dropzone-empty {
  color: var(--muted);
  font-size: 12px;
}
.meeting-dropzone.has-participants .meeting-dropzone-empty {
  display: none;
}
.meeting-participant {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  border: 1px solid var(--accent, #5b8def);
  border-radius: 8px;
  background: rgba(91, 141, 239, 0.1);
  padding: 8px;
}
.meeting-participant button {
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: transparent;
  color: var(--subtle);
  cursor: pointer;
  font-size: 12px;
  padding: 2px 8px;
}
.meeting-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
  align-items: end;
}
.meeting-field {
  display: grid;
  gap: 4px;
  font-size: 11px;
  color: var(--muted);
  min-width: 0;
}
.meeting-field input,
.meeting-field select {
  min-width: 0;
}
.meeting-validation {
  margin-top: 8px;
  font-size: 12px;
  color: var(--warning, #e0a23a);
  min-height: 16px;
}
.meeting-validation.is-ok {
  color: var(--success, #4caf7d);
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
.tsboard-toolbar {
  display: grid;
  grid-template-columns: 1fr auto auto auto;
  gap: 10px;
  align-items: center;
  margin-bottom: 12px;
}
.tsboard-swimlane-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 13px;
}
.tsboard-staleness {
  color: var(--subtle);
  font-size: 12px;
  margin-bottom: 12px;
}
.tsboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}
.tsboard-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.tsboard-card.bucket-completed { border-left: 3px solid var(--success); }
.tsboard-card.bucket-in_progress { border-left: 3px solid var(--blue); }
.tsboard-card.bucket-planned { border-left: 3px solid var(--subtle); }
.tsboard-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}
.tsboard-title { display: flex; flex-direction: column; gap: 2px; }
.tsboard-title span { color: var(--muted); font-size: 13px; }
.tsboard-toggle {
  background: var(--surface-raised);
  border: 1px solid var(--line);
  color: var(--ink);
  border-radius: 6px;
  padding: 4px 8px;
  cursor: pointer;
}
.tsboard-card-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 13px;
}
.tsboard-distribution { display: flex; flex-wrap: wrap; gap: 6px; }
.dist-chip {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
  border: 1px solid var(--line-strong);
}
.dist-completed { color: var(--success); }
.dist-in_progress { color: var(--blue); }
.dist-planned { color: var(--muted); }
.agent-stack { display: flex; gap: 4px; flex-wrap: wrap; }
.agent-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--surface-raised);
  border: 1px solid var(--line-strong);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}
.agent-stack-empty { color: var(--subtle); font-size: 12px; }
.tsboard-activity { list-style: none; margin: 0; padding: 0; font-size: 12px; }
.tsboard-activity li { color: var(--muted); }
.tsboard-add-row { display: flex; gap: 6px; }
.tsboard-add-title { flex: 1; }
.tsboard-add-task {
  background: var(--primary);
  border: none;
  color: var(--ink);
  border-radius: 6px;
  padding: 6px 10px;
  cursor: pointer;
}
.tsboard-children { display: flex; flex-direction: column; gap: 4px; }
.tsboard-child {
  display: grid;
  grid-template-columns: auto 90px 1fr auto auto auto;
  gap: 8px;
  align-items: center;
  padding: 6px;
  border-top: 1px solid var(--line);
  cursor: pointer;
  font-size: 12px;
}
.tsboard-child:hover { background: var(--surface-raised); }
.tsboard-child-id { font-family: monospace; color: var(--muted); }
.phase-chip {
  border-radius: 999px;
  padding: 1px 7px;
  font-size: 10px;
  text-transform: uppercase;
}
.phase-plan { background: rgba(98, 102, 109, 0.25); color: var(--muted); }
.phase-work { background: rgba(87, 160, 255, 0.18); color: var(--blue); }
.phase-review { background: rgba(217, 154, 43, 0.18); color: var(--amber); }
.phase-done { background: rgba(39, 166, 68, 0.18); color: var(--success); }
.tsboard-swimlanes { display: flex; flex-direction: column; gap: 16px; }
.tsboard-swimlane {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 12px;
  background: var(--panel);
}
.tsboard-swimlane-header { display: flex; gap: 8px; align-items: baseline; margin-bottom: 8px; }
.tsboard-swimlane-header span { color: var(--muted); font-size: 13px; }
.tsboard-swimlane-cols {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.tsboard-swim-col { background: var(--surface-raised); border-radius: 6px; padding: 8px; }
.tsboard-swim-col header { font-size: 12px; color: var(--muted); margin-bottom: 6px; }
.tsboard-swim-card {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px;
  background: var(--panel);
  border-radius: 4px;
  margin-bottom: 6px;
  cursor: pointer;
  font-size: 12px;
}
.tsboard-swim-card code { color: var(--muted); }

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
  .work-toolbar,
  .work-grid,
  .tsboard-toolbar,
  .tsboard-cards,
  .tsboard-swimlane-cols,
  .work-detail-meta,
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
.roadmap-timeline-summary {
  color: var(--muted);
  font-size: 13px;
  margin: 0 0 12px;
}
.roadmap-timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-left: 22px;
  border-left: 2px solid var(--border, #2a2a3a);
}
.roadmap-tl-item {
  position: relative;
  display: block;
}
.roadmap-tl-marker {
  position: absolute;
  left: -29px;
  top: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--muted);
  border: 2px solid var(--bg, #11111a);
}
.roadmap-tl-marker.is-done {
  background: var(--teal);
}
.roadmap-tl-marker.is-release {
  background: var(--amber);
  border-radius: 2px;
}
.roadmap-tl-vision .roadmap-tl-marker {
  background: var(--primary-hover);
}
.roadmap-tl-statement {
  color: var(--muted);
  font-size: 13px;
  margin: 4px 0 8px;
}
.roadmap-tl-links {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.roadmap-tl-link {
  display: grid;
  grid-template-columns: 120px 70px 1fr 90px;
  gap: 8px;
  font-size: 12px;
  align-items: center;
}
.roadmap-tl-link-id strong,
.roadmap-tl-link-id {
  color: var(--primary-hover);
  font-weight: 600;
}
.roadmap-tl-link-level,
.roadmap-tl-link-status {
  color: var(--muted);
}
.roadmap-tl-link-completed .roadmap-tl-link-status {
  color: var(--teal);
}
.roadmap-tl-link-in_progress .roadmap-tl-link-status {
  color: var(--amber);
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
const runtimeCommandTypes = ["runtime.call_agent", "runtime.assign_task", "runtime.request_review", "runtime.request_meeting", "runtime.goal.start", "runtime.goal.pause", "runtime.goal.resume", "runtime.goal.stop", "planning.scan", "planning.approve", "planning.reject"];
let runtimeState = null;
let selectedTaskId = null;
let pendingWrites = [];
let eventStream = null;
let selectedWorkNodeId = null;
let collapsedWorkNodes = new Set();
let workFacetSelections = {};
let workFacetSignature = "";
let meetingParticipants = [];
let meetingKeyboardHeld = null;
let expandedTasksetCards = new Set();
let tasksetSwimlaneMode = false;

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

function connectEventStream() {
  if (!window.EventSource || eventStream) return;
  eventStream = new EventSource("/api/stream");
  eventStream.addEventListener("state", (event) => {
    runtimeState = JSON.parse(event.data);
    renderAll();
    setText("poll-state", "live");
  });
  eventStream.onerror = () => {
    setText("poll-state", "polling");
  };
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

function inflightRecordsForTask(taskId) {
  return (((runtimeState || {}).inflight || {}).records || []).filter((row) => row.task_id === taskId);
}

function inflightAnnotation(task) {
  const rows = inflightRecordsForTask(task.id);
  if (!rows.length) return "";
  const first = rows[0];
  const extra = rows.length > 1 ? ` (+${rows.length - 1} more branches)` : "";
  return `<span class="task-card-inflight">${escapeHtml(first.main_status || "?")} (main) / ${escapeHtml(first.branch_status || "?")} @${escapeHtml(first.branch)} +${escapeHtml(first.ahead ?? "?")}${extra}</span>`;
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
    ${inflightAnnotation(task)}
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

function renderRoadmapTimeline() {
  const timeline = runtimeState.roadmap_timeline || { vision: {}, milestones: [], releases: [], summary: {} };
  const summary = timeline.summary || {};
  const vision = timeline.vision || {};
  $("roadmap-timeline-summary").textContent =
    `${summary.milestones_done || 0}/${summary.milestones || 0} milestones done`
    + ` - ${summary.linked_work || 0} linked work items`
    + ` - ${summary.releases || 0} releases`
    + ` (phase: ${timeline.phase || "n/a"})`;

  const visionItem = `
    <article class="roadmap-tl-item roadmap-tl-vision" data-tier="vision">
      <div class="roadmap-tl-marker"></div>
      <div class="roadmap-tl-body surface-card pass">
        <div class="surface-card-header">
          <b>${escapeHtml(vision.title || "Vision")}</b>
          <span class="state-chip">vision</span>
        </div>
        <p class="roadmap-tl-statement">${escapeHtml(vision.statement || vision.problem || "No vision statement")}</p>
        ${renderSurfaceMeta(`
          <span><span class="meta-label">Problem</span><strong>${escapeHtml(vision.problem || "n/a")}</strong></span>
          <span><span class="meta-label">Success</span><strong>${escapeHtml(vision.success_metric || "n/a")}</strong></span>
          <span><span class="meta-label">Source</span><strong>${escapeHtml(vision.source_path || "VISION.md")}</strong></span>
        `)}
      </div>
    </article>`;

  const milestoneItems = (timeline.milestones || []).map((milestone) => {
    const rollup = milestone.rollup || {};
    const pct = rollup.pct == null ? null : rollup.pct;
    const tone = milestone.done ? "pass" : (milestone.status_bucket === "in_progress" ? "warn" : "");
    const links = (milestone.linked_work || []).map((work) => `
      <li class="roadmap-tl-link roadmap-tl-link-${escapeHtml(work.status_bucket || "planned")}">
        <span class="roadmap-tl-link-id">${escapeHtml(work.id)}</span>
        <span class="roadmap-tl-link-level">${escapeHtml(work.level || "")}</span>
        <span class="roadmap-tl-link-title">${escapeHtml(work.title || work.id)}</span>
        <span class="roadmap-tl-link-status">${escapeHtml(work.status_bucket || "")}</span>
      </li>`).join("");
    return `
    <article class="roadmap-tl-item roadmap-tl-milestone" data-tier="milestone">
      <div class="roadmap-tl-marker ${milestone.done ? "is-done" : ""}"></div>
      <div class="roadmap-tl-body surface-card ${tone}">
        <div class="surface-card-header">
          <b>${escapeHtml(milestone.date || "undated")} - ${escapeHtml(milestone.title || "milestone")}</b>
          <span class="state-chip">${escapeHtml(milestone.done ? "done" : milestone.status_bucket || "open")}</span>
        </div>
        ${renderSurfaceMeta(`
          <span><span class="meta-label">Progress</span><strong>${pct == null ? "n/a" : escapeHtml(String(pct)) + "%"}</strong></span>
          <span><span class="meta-label">Linked</span><strong>${escapeHtml(String(rollup.linked || 0))}</strong></span>
          <span><span class="meta-label">Done</span><strong>${escapeHtml(String(rollup.completed || 0))}</strong></span>
          <span><span class="meta-label">Source</span><strong>${escapeHtml(milestone.source_path || "ROADMAP.md")}</strong></span>
        `)}
        ${links ? `<ul class="roadmap-tl-links">${links}</ul>` : `<div class="empty">No linked work</div>`}
      </div>
    </article>`;
  }).join("");

  const releaseItems = (timeline.releases || []).map((release) => `
    <article class="roadmap-tl-item roadmap-tl-release" data-tier="release">
      <div class="roadmap-tl-marker is-release"></div>
      <div class="roadmap-tl-body surface-card ${release.status_bucket === "completed" ? "pass" : "warn"}">
        <div class="surface-card-header">
          <b>${escapeHtml(release.title || release.version || "release")}</b>
          <span class="state-chip">${escapeHtml(release.status || "release")}</span>
        </div>
        ${renderSurfaceMeta(`
          <span><span class="meta-label">Version</span><strong>${escapeHtml(release.version || "n/a")}</strong></span>
          <span><span class="meta-label">Decided</span><strong>${escapeHtml(release.date || "n/a")}</strong></span>
          <span><span class="meta-label">Owner gate</span><strong>${release.owner_required ? "required" : "no"}</strong></span>
          <span><span class="meta-label">Source</span><strong>${escapeHtml(release.source_path || "release decision")}</strong></span>
        `)}
      </div>
    </article>`).join("");

  $("roadmap-timeline").innerHTML =
    visionItem
    + (milestoneItems || `<div class="empty">No milestones</div>`)
    + (releaseItems || `<div class="empty">No releases</div>`);
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
      <div class="taskset-actions">
        <button class="taskset-action" type="button" onclick="queuePlanningDecision('planning.approve', '${escapeHtml(row.id || row.title || "proposal")}')">Approve</button>
        <button class="taskset-action" type="button" onclick="queuePlanningDecision('planning.reject', '${escapeHtml(row.id || row.title || "proposal")}')">Reject</button>
      </div>
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

function queuePlanningDecision(type, proposalId) {
  return sendJson("/api/commands", {
    type,
    payload: {
      type,
      payload: {
        actor: "ui",
        proposal_id: proposalId,
        reason: `${type} from planner panel`,
        apply: false
      }
    }
  });
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

function workExplorerData() {
  return (runtimeState && runtimeState.work_explorer) || { nodes: [], roots: [], facets: {}, staleness_note: "" };
}

function workNodeIndex() {
  const byId = new Map();
  (workExplorerData().nodes || []).forEach((node) => byId.set(node.id, node));
  return byId;
}

function workBucketClass(node) {
  const normalized = String(node.status_bucket || "planned").replace(/[^a-z0-9]+/g, "-");
  return `bucket-${normalized || "planned"}`;
}

function workMaxDepth() {
  const value = Number($("work-depth-filter")?.value);
  return Number.isFinite(value) ? value : 3;
}

function workSearchQuery() {
  return $("work-search")?.value.trim().toLowerCase() || "";
}

function workNodeMatchesFacets(node) {
  return Object.entries(workFacetSelections).every(([facet, values]) => {
    if (!values || values.size === 0) return true;
    const value = (node.facets || {})[facet];
    return value !== undefined && values.has(String(value));
  });
}

function workNodeMatchesSearch(node, query) {
  if (!query) return true;
  return [node.id, node.number, node.title, node.status, node.level, JSON.stringify(node.facets || {})]
    .join(" ")
    .toLowerCase()
    .includes(query);
}

function workNodeMatches(node, query) {
  return workNodeMatchesFacets(node) && workNodeMatchesSearch(node, query);
}

function workNodeVisible(node, byId, query, memo) {
  if (memo.has(node.id)) return memo.get(node.id);
  let visible = workNodeMatches(node, query);
  if (!visible) {
    visible = (node.children || []).some((childId) => {
      const child = byId.get(childId);
      return child ? workNodeVisible(child, byId, query, memo) : false;
    });
  }
  memo.set(node.id, visible);
  return visible;
}

function workRollupBadge(node) {
  const rollup = node.rollup || {};
  if (!rollup.total) return "";
  const pct = rollup.pct === null || rollup.pct === undefined ? "~" : `${rollup.pct}%`;
  const title = `completed ${rollup.completed}/${rollup.total} | in progress ${rollup.in_progress} | planned ${rollup.planned}`;
  return `<span class="rollup-badge" title="${escapeHtml(title)}">${escapeHtml(rollup.completed)}/${escapeHtml(rollup.total)} done - ${escapeHtml(pct)}</span>`;
}

function workEvidenceBadge(node) {
  const count = (node.evidence_refs || []).length + (node.descendant_evidence_refs || []).length;
  return count ? `<span class="evidence-badge">${escapeHtml(count)} refs</span>` : "";
}

function workNodeMarkup(node, byId, query, memo) {
  if (!workNodeVisible(node, byId, query, memo)) return "";
  const maxDepth = workMaxDepth();
  const collapsed = collapsedWorkNodes.has(node.id);
  const childNodes = (node.children || []).map((childId) => byId.get(childId)).filter(Boolean);
  const renderableChildren = node.depth < maxDepth && !collapsed
    ? childNodes.map((child) => workNodeMarkup(child, byId, query, memo)).join("")
    : "";
  const hasToggle = childNodes.length > 0 && node.depth < maxDepth;
  const toggle = hasToggle
    ? `<button class="work-toggle" type="button" data-work-toggle="${escapeHtml(node.id)}" aria-label="${collapsed ? "Expand" : "Collapse"} ${escapeHtml(node.id)}">${collapsed ? "+" : "-"}</button>`
    : `<span class="work-toggle" aria-hidden="true"></span>`;
  return `<div class="work-node work-level-${escapeHtml(node.level || "unknown")}">
    <div class="work-node-row ${workBucketClass(node)} ${node.id === selectedWorkNodeId ? "is-selected" : ""}" role="button" tabindex="0" data-work-node="${escapeHtml(node.id)}">
      ${toggle}
      <span class="work-node-number">${escapeHtml(node.number || "")}</span>
      <span class="work-node-id">${escapeHtml(node.id)}</span>
      <span class="work-node-title">${escapeHtml(node.title || "")}</span>
      <span class="state-chip">${escapeHtml(node.status || "unknown")}</span>
      ${workRollupBadge(node)}
      ${workEvidenceBadge(node)}
    </div>
    ${renderableChildren ? `<div class="work-node-children">${renderableChildren}</div>` : ""}
  </div>`;
}

function renderWorkFacets() {
  const host = $("work-facets");
  if (!host) return;
  const facets = workExplorerData().facets || {};
  const signature = JSON.stringify(facets);
  if (signature === workFacetSignature && host.childElementCount) return;
  workFacetSignature = signature;
  const names = Object.keys(facets).filter((name) => (facets[name] || []).length);
  host.innerHTML = names.map((name) => `
    <fieldset class="facet-group">
      <legend>${escapeHtml(name.replace(/_/g, " "))}</legend>
      <div class="facet-options">
        ${(facets[name] || []).map((value) => {
          const checked = workFacetSelections[name]?.has(String(value)) ? "checked" : "";
          return `<label class="facet-option"><input type="checkbox" data-facet="${escapeHtml(name)}" value="${escapeHtml(value)}" ${checked}> ${escapeHtml(value)}</label>`;
        }).join("")}
      </div>
    </fieldset>
  `).join("");
  host.querySelectorAll("input[type=checkbox]").forEach((box) => {
    box.addEventListener("change", () => {
      const facet = box.dataset.facet;
      const selections = workFacetSelections[facet] || (workFacetSelections[facet] = new Set());
      if (box.checked) selections.add(box.value);
      else selections.delete(box.value);
      renderWorkTree();
    });
  });
}

function renderWorkNodeDetail() {
  const host = $("work-node-detail");
  if (!host) return;
  const node = workNodeIndex().get(selectedWorkNodeId);
  if (!node) {
    host.innerHTML = `<div class="detail-empty">No work item selected</div>`;
    return;
  }
  const rollup = node.rollup || {};
  const facets = node.facets || {};
  const ownRefs = node.evidence_refs || [];
  const childRefs = node.descendant_evidence_refs || [];
  const refsMarkup = (refs) => refs.map((ref) => `<code class="evidence-ref">${escapeHtml(ref)}</code>`).join("");
  host.innerHTML = `
    <h3>${escapeHtml(node.label || node.id)} - ${escapeHtml(node.id)}</h3>
    <p>${escapeHtml(node.title || "")}</p>
    <div class="work-detail-meta" aria-label="Work node metadata">
      <span><span class="meta-label">Level</span><strong>${escapeHtml(node.level || "unknown")}</strong></span>
      <span><span class="meta-label">Status</span><strong>${escapeHtml(node.status || "unknown")}</strong></span>
      <span><span class="meta-label">Roll-up</span><strong>${escapeHtml(rollup.total ? `${rollup.completed}/${rollup.total} done (${rollup.pct}%)` : "no children")}</strong></span>
      <span><span class="meta-label">In progress</span><strong>${escapeHtml(rollup.in_progress ?? 0)}</strong></span>
      <span><span class="meta-label">Planned</span><strong>${escapeHtml(rollup.planned ?? 0)}</strong></span>
      <span><span class="meta-label">Taskset</span><strong>${escapeHtml(node.taskset_id || "none")}</strong></span>
      ${Object.entries(facets).map(([name, value]) => `<span><span class="meta-label">${escapeHtml(name.replace(/_/g, " "))}</span><strong>${escapeHtml(value)}</strong></span>`).join("")}
    </div>
    <code class="evidence-ref">${escapeHtml(node.path || "")}</code>
    <div>
      <span class="meta-label">Evidence and review refs</span>
      ${ownRefs.length ? refsMarkup(ownRefs) : `<span class="evidence-ref">no direct refs</span>`}
    </div>
    <div>
      <span class="meta-label">Archived child evidence</span>
      ${childRefs.length ? refsMarkup(childRefs) : `<span class="evidence-ref">no child refs</span>`}
    </div>
  `;
}

function renderWorkTree() {
  const host = $("work-tree");
  if (!host) return;
  const explorer = workExplorerData();
  const byId = workNodeIndex();
  const query = workSearchQuery();
  const memo = new Map();
  const markup = (explorer.roots || [])
    .map((rootId) => byId.get(rootId))
    .filter(Boolean)
    .map((node) => workNodeMarkup(node, byId, query, memo))
    .join("");
  host.innerHTML = markup || `<div class="empty">No work items match the current filters</div>`;
  host.querySelectorAll("[data-work-toggle]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const nodeId = button.dataset.workToggle;
      if (collapsedWorkNodes.has(nodeId)) collapsedWorkNodes.delete(nodeId);
      else collapsedWorkNodes.add(nodeId);
      renderWorkTree();
    });
  });
  host.querySelectorAll("[data-work-node]").forEach((row) => {
    const select = () => {
      selectedWorkNodeId = row.dataset.workNode;
      renderWorkTree();
      renderWorkNodeDetail();
    };
    row.addEventListener("click", select);
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        select();
      }
    });
  });
}

function renderWorkExplorer() {
  setText("work-staleness", workExplorerData().staleness_note || "");
  renderWorkFacets();
  renderWorkTree();
  renderWorkNodeDetail();
}

function meetingRoomData() {
  return (runtimeState && runtimeState.meeting_room) || {
    available_agents: [],
    topic_options: [],
    meeting_types: ["meeting", "seminar", "review"],
    constraints: { min_participants: 2, min_rounds: 1 }
  };
}

function meetingConstraints() {
  return meetingRoomData().constraints || { min_participants: 2, min_rounds: 1 };
}

function meetingAddParticipant(id) {
  const name = String(id || "").trim();
  if (!name) return;
  if (!meetingParticipants.some((existing) => existing.toLowerCase() === name.toLowerCase())) {
    meetingParticipants.push(name);
    renderMeetingRoom();
  }
}

function meetingRemoveParticipant(id) {
  meetingParticipants = meetingParticipants.filter((existing) => existing !== id);
  renderMeetingRoom();
}

function renderMeetingAvailable() {
  const host = $("meeting-available");
  if (!host) return;
  const placed = new Set(meetingParticipants.map((name) => name.toLowerCase()));
  const cards = meetingRoomData().available_agents || [];
  host.innerHTML = cards.length
    ? cards.map((agent) => {
        const isPlaced = placed.has(String(agent.id).toLowerCase());
        const meta = `${agent.online ? "online" : "offline"}${agent.instances > 1 ? " x" + agent.instances : ""}`;
        return `<div class="meeting-card ${isPlaced ? "is-placed" : ""}" draggable="true" tabindex="0" role="button" data-meeting-agent="${escapeHtml(agent.id)}" aria-label="Add ${escapeHtml(agent.display_name || agent.id)} to meeting">
          <span class="meeting-card-name">${escapeHtml(agent.display_name || agent.id)}</span>
          <span class="meeting-card-meta">${escapeHtml(meta)}</span>
        </div>`;
      }).join("")
    : `<div class="empty">No runtime agents available</div>`;
  host.querySelectorAll("[data-meeting-agent]").forEach((card) => {
    const id = card.dataset.meetingAgent;
    card.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", id);
      event.dataTransfer.effectAllowed = "move";
    });
    card.addEventListener("click", () => meetingAddParticipant(id));
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        meetingAddParticipant(id);
      }
    });
  });
}

function renderMeetingParticipants() {
  const zone = $("meeting-dropzone");
  const host = $("meeting-participants");
  if (!host || !zone) return;
  zone.classList.toggle("has-participants", meetingParticipants.length > 0);
  host.innerHTML = meetingParticipants
    .map((name) => `<div class="meeting-participant" data-participant="${escapeHtml(name)}">
        <span class="meeting-card-name">${escapeHtml(name)}</span>
        <button type="button" data-remove-participant="${escapeHtml(name)}" aria-label="Remove ${escapeHtml(name)}">Remove</button>
      </div>`)
    .join("");
  host.querySelectorAll("[data-remove-participant]").forEach((button) => {
    button.addEventListener("click", () => meetingRemoveParticipant(button.dataset.removeParticipant));
  });
}

function renderMeetingTaskOptions() {
  const select = $("meeting-task");
  if (!select) return;
  const topics = meetingRoomData().topic_options || [];
  const current = select.value;
  select.innerHTML = `<option value="">(free-form topic)</option>` +
    topics.map((topic) => `<option value="${escapeHtml(topic.id)}">${escapeHtml(topic.id)} - ${escapeHtml(topic.title)}</option>`).join("");
  if (topics.some((topic) => topic.id === current)) select.value = current;
}

function meetingValidationMessage() {
  const constraints = meetingConstraints();
  const minParticipants = constraints.min_participants || 2;
  const rounds = Number($("meeting-rounds")?.value);
  const topic = ($("meeting-topic")?.value || "").trim();
  const taskId = $("meeting-task")?.value || "";
  if (meetingParticipants.length < minParticipants) {
    return { ok: false, message: `Add at least ${minParticipants} participants (have ${meetingParticipants.length}).` };
  }
  if (!topic && !taskId) {
    return { ok: false, message: "Pick a task or enter a topic." };
  }
  if (!Number.isFinite(rounds) || rounds < 1) {
    return { ok: false, message: "Rounds must be > 0." };
  }
  return { ok: true, message: `Ready: ${meetingParticipants.length} participants, ${rounds} round(s).` };
}

function renderMeetingValidation() {
  const node = $("meeting-validation");
  if (!node) return;
  const result = meetingValidationMessage();
  node.textContent = result.message;
  node.classList.toggle("is-ok", result.ok);
  const start = $("meeting-start");
  if (start) start.disabled = !result.ok;
}

function renderMeetingRoom() {
  renderMeetingAvailable();
  renderMeetingParticipants();
  renderMeetingTaskOptions();
  renderMeetingValidation();
}

async function submitMeetingPlan(event) {
  event.preventDefault();
  const result = meetingValidationMessage();
  if (!result.ok) {
    renderMeetingValidation();
    return;
  }
  const topic = ($("meeting-topic").value || "").trim();
  const taskId = $("meeting-task").value || "";
  await sendJson("/api/commands", {
    type: "runtime.request_meeting",
    payload: {
      to: meetingParticipants[0],
      meeting_type: $("meeting-type").value,
      rounds: Number($("meeting-rounds").value),
      topic: topic || taskId,
      task_id: taskId || null,
      participants: meetingParticipants.slice(),
      instruction: `Plan ${$("meeting-type").value} on ${topic || taskId} with ${meetingParticipants.join(", ")}`,
      script: "python scripts/meeting_room.py plan"
    }
  });
}

function tasksetsBoardData() {
  return (runtimeState && runtimeState.tasksets_board) || { cards: [], totals: {}, staleness_note: "" };
}

function tasksetCardSearchText(card) {
  return [
    card.id,
    card.title,
    card.status,
    ...(card.assigned_agents || []),
    ...(card.children || []).map((child) => `${child.id} ${child.title} ${child.owner}`)
  ].join(" ").toLowerCase();
}

function filteredTasksetCards() {
  const query = $("tsboard-filter")?.value.trim().toLowerCase() || "";
  const cards = tasksetsBoardData().cards || [];
  if (!query) return cards;
  return cards.filter((card) => tasksetCardSearchText(card).includes(query));
}

function tasksetPhaseChip(child) {
  const phase = String(child.phase || "plan");
  return `<span class="phase-chip phase-${escapeHtml(phase)}">${escapeHtml(phase)}</span>`;
}

function tasksetStatusDistribution(card) {
  const dist = card.status_distribution || {};
  return ["completed", "in_progress", "planned"]
    .filter((bucket) => dist[bucket])
    .map((bucket) => `<span class="dist-chip dist-${escapeHtml(bucket)}">${escapeHtml(bucket)} ${escapeHtml(dist[bucket])}</span>`)
    .join("");
}

function tasksetAgentStack(card) {
  const agents = card.assigned_agents || [];
  if (!agents.length) return `<span class="agent-stack-empty">unassigned</span>`;
  return agents.slice(0, 6)
    .map((agent) => `<span class="agent-avatar" title="${escapeHtml(agent)}">${escapeHtml(String(agent).slice(0, 2).toUpperCase())}</span>`)
    .join("");
}

function tasksetRecentActivity(card) {
  const recent = card.recent_activity || [];
  if (!recent.length) return "";
  return `<ul class="tsboard-activity">${recent.map((item) =>
    `<li><code>${escapeHtml(item.task_id)}</code> ${escapeHtml(item.event)} <small>${escapeHtml(item.ts || "")}</small></li>`
  ).join("")}</ul>`;
}

function tasksetChildRows(card) {
  const children = card.children || [];
  if (!children.length) return `<div class="empty">No tasks</div>`;
  return children.map((child) => `
    <div class="tsboard-child" data-child-id="${escapeHtml(child.id)}">
      ${tasksetPhaseChip(child)}
      <span class="tsboard-child-id">${escapeHtml(child.id)}</span>
      <span class="tsboard-child-title">${escapeHtml(child.title)}</span>
      <span class="tsboard-child-owner">${escapeHtml(child.owner || "unassigned")}</span>
      <span class="tsboard-child-priority">${escapeHtml(child.priority || "-")}</span>
      <span class="tsboard-child-pct">${escapeHtml(numericPct(child.progress_pct) ?? 0)}%</span>
    </div>
  `).join("");
}

function tasksetBoardCards(cards) {
  return cards.map((card) => {
    const expanded = expandedTasksetCards.has(card.id);
    const progress = card.progress || { done: 0, total: 0 };
    return `
      <article class="tsboard-card ${escapeHtml("bucket-" + (card.status_bucket || "planned"))}" data-taskset-id="${escapeHtml(card.id)}">
        <header class="tsboard-card-header">
          <div class="tsboard-title">
            <b>${escapeHtml(card.id)}</b>
            <span>${escapeHtml(card.title || card.id)}</span>
          </div>
          <button class="tsboard-toggle" type="button" data-tsboard-toggle="${escapeHtml(card.id)}" aria-expanded="${expanded}">${expanded ? "Collapse" : "Expand"}</button>
        </header>
        <div class="tsboard-card-meta">
          <span><span class="meta-label">Progress</span><strong>${escapeHtml(progress.done)}/${escapeHtml(progress.total)}</strong></span>
          <span><span class="meta-label">Status</span><strong>${escapeHtml(card.status || "planned")}</strong></span>
        </div>
        ${progressBar(card.progress_pct)}
        <div class="tsboard-distribution">${tasksetStatusDistribution(card)}</div>
        <div class="agent-stack" aria-label="Assigned agents">${tasksetAgentStack(card)}</div>
        ${tasksetRecentActivity(card)}
        <div class="tsboard-add-row">
          <input class="tsboard-add-title" data-tsboard-add-input="${escapeHtml(card.id)}" placeholder="new task title">
          <button class="tsboard-add-task" type="button" data-tsboard-add="${escapeHtml(card.id)}">+ Add task</button>
        </div>
        ${expanded ? `<div class="tsboard-children">${tasksetChildRows(card)}</div>` : ""}
      </article>
    `;
  }).join("");
}

async function queueTasksetAddTask(taskSetId, title) {
  const cleanTitle = String(title || "").trim();
  if (!cleanTitle) return;
  await sendJson("/api/tasks", {
    type: "task.create",
    payload: {
      title: cleanTitle,
      description: cleanTitle,
      status: "planned",
      owner: "lead-engineer",
      task_set_id: taskSetId,
      queue_position: "front"
    }
  });
}

function wireTasksetBoardActions(host) {
  host.querySelectorAll("[data-tsboard-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.tsboardToggle;
      if (expandedTasksetCards.has(id)) {
        expandedTasksetCards.delete(id);
      } else {
        expandedTasksetCards.add(id);
      }
      renderTasksetBoard();
    });
  });
  host.querySelectorAll("[data-tsboard-add]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.tsboardAdd;
      const input = host.querySelector(`[data-tsboard-add-input="${CSS.escape(id)}"]`);
      queueTasksetAddTask(id, input ? input.value : "");
      if (input) input.value = "";
    });
  });
  host.querySelectorAll(".tsboard-child").forEach((row) => {
    row.addEventListener("click", () => {
      selectedTaskId = row.dataset.childId;
      renderDetail();
    });
  });
}

function tasksetSwimlanes(cards) {
  const phases = [
    ["plan", "Plan"],
    ["work", "Work"],
    ["review", "Review"],
    ["done", "Done"]
  ];
  return cards.map((card) => `
    <section class="tsboard-swimlane" data-taskset-id="${escapeHtml(card.id)}">
      <header class="tsboard-swimlane-header"><b>${escapeHtml(card.id)}</b><span>${escapeHtml(card.title || "")}</span></header>
      <div class="tsboard-swimlane-cols">
        ${phases.map(([phase, label]) => {
          const items = (card.children || []).filter((child) => String(child.phase) === phase);
          const body = items.length
            ? items.map((child) => `<div class="tsboard-swim-card" data-child-id="${escapeHtml(child.id)}"><code>${escapeHtml(child.id)}</code><span>${escapeHtml(child.title)}</span></div>`).join("")
            : `<div class="empty">-</div>`;
          return `<div class="tsboard-swim-col phase-${escapeHtml(phase)}"><header>${escapeHtml(label)} <small>${items.length}</small></header>${body}</div>`;
        }).join("")}
      </div>
    </section>
  `).join("");
}

function renderTasksetBoard() {
  const cardsHost = $("tsboard-cards");
  const swimHost = $("tsboard-swimlanes");
  if (!cardsHost || !swimHost) return;
  setText("tsboard-staleness", tasksetsBoardData().staleness_note || "");
  const cards = filteredTasksetCards();
  if (tasksetSwimlaneMode) {
    cardsHost.hidden = true;
    swimHost.hidden = false;
    swimHost.innerHTML = cards.length ? tasksetSwimlanes(cards) : `<div class="empty">No task sets</div>`;
    swimHost.querySelectorAll(".tsboard-swim-card").forEach((row) => {
      row.addEventListener("click", () => {
        selectedTaskId = row.dataset.childId;
        renderDetail();
      });
    });
  } else {
    swimHost.hidden = true;
    cardsHost.hidden = false;
    cardsHost.innerHTML = cards.length ? tasksetBoardCards(cards) : `<div class="empty">No task sets</div>`;
    wireTasksetBoardActions(cardsHost);
  }
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
  renderWorkExplorer();
  renderMeetingRoom();
  renderTaskSetDirectory();
  renderTasksetBoard();
  renderAgents();
  renderMessages();
  renderEvents();
  renderEvidence();
  renderPlanning();
  renderRoadmapTimeline();
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
$("tsboard-filter")?.addEventListener("input", renderTasksetBoard);
$("tsboard-swimlane-toggle")?.addEventListener("change", (event) => {
  tasksetSwimlaneMode = Boolean(event.target.checked);
  renderTasksetBoard();
});
$("tsboard-expand-all")?.addEventListener("click", () => {
  expandedTasksetCards = new Set((tasksetsBoardData().cards || []).map((card) => card.id));
  renderTasksetBoard();
});
$("tsboard-collapse-all")?.addEventListener("click", () => {
  expandedTasksetCards = new Set();
  renderTasksetBoard();
});
["work-search", "work-depth-filter"].forEach((id) => {
  const node = $(id);
  if (node) {
    node.addEventListener("input", renderWorkTree);
    node.addEventListener("change", renderWorkTree);
  }
});
$("work-expand-all")?.addEventListener("click", () => {
  collapsedWorkNodes = new Set();
  renderWorkTree();
});
$("work-collapse-all")?.addEventListener("click", () => {
  collapsedWorkNodes = new Set((workExplorerData().nodes || []).filter((node) => (node.children || []).length).map((node) => node.id));
  renderWorkTree();
});
(() => {
  const zone = $("meeting-dropzone");
  if (zone) {
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      zone.classList.add("is-dragover");
    });
    zone.addEventListener("dragleave", () => zone.classList.remove("is-dragover"));
    zone.addEventListener("drop", (event) => {
      event.preventDefault();
      zone.classList.remove("is-dragover");
      meetingAddParticipant(event.dataTransfer.getData("text/plain"));
    });
    zone.addEventListener("keydown", (event) => {
      if ((event.key === "Delete" || event.key === "Backspace") && meetingParticipants.length) {
        event.preventDefault();
        meetingRemoveParticipant(meetingParticipants[meetingParticipants.length - 1]);
      }
    });
  }
  const form = $("meeting-config-form");
  if (form) form.addEventListener("submit", submitMeetingPlan);
  ["meeting-topic", "meeting-task", "meeting-rounds", "meeting-type"].forEach((id) => {
    const node = $(id);
    if (node) {
      node.addEventListener("input", renderMeetingValidation);
      node.addEventListener("change", renderMeetingValidation);
    }
  });
})();
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
connectEventStream();
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


def _sse_response(payload: object) -> ConsoleResponse:
    body = "event: state\n" + "data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n\n"
    return ConsoleResponse(200, "text/event-stream; charset=utf-8", _bytes(body))


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
    if request_path == "/api/stream":
        return _sse_response(ui_state.build_state(root_path))
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
    if request_path == "/api/replay/snapshot":
        state = ui_state.build_state(root_path)
        filters = {key: values[0] for key, values in parse_qs(parsed_url.query).items() if values}
        return _json_response(ui_state.build_replay_snapshot(state["replay"], filters.get("at")))

    api_resources = {
        "/api/tasks": "tasks",
        "/api/agents": "agents",
        "/api/task-sets": "task_sets",
        "/api/task_sets": "task_sets",
        "/api/messages": "messages",
        "/api/goals": "goals",
        "/api/inflight": "inflight",
        "/api/work_explorer": "work_explorer",
        "/api/work-explorer": "work_explorer",
        "/api/meeting_room": "meeting_room",
        "/api/meeting-room": "meeting_room",
        "/api/tasksets_board": "tasksets_board",
        "/api/tasksets-board": "tasksets_board",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/replay": "replay",
        "/api/graph": "graph",
        "/api/state-machines": "state_machines",
        "/api/roadmap": "roadmap",
        "/api/roadmap-timeline": "roadmap_timeline",
        "/api/roadmap_timeline": "roadmap_timeline",
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
