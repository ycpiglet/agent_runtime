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
  <script>
    // No-flash theme bootstrap: apply saved/preferred theme before first paint.
    (function () {
      try {
        var saved = window.localStorage.getItem("agent-runtime-theme");
        var prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
        var theme = (saved === "dark" || saved === "light") ? saved : (prefersDark ? "dark" : "light");
        document.documentElement.setAttribute("data-theme", theme);
      } catch (error) {
        document.documentElement.setAttribute("data-theme", "light");
      }
    })();
  </script>
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
        <button id="sidebar-toggle" class="sidebar-toggle" type="button" aria-controls="primary-sidebar" aria-expanded="true" aria-label="Toggle sidebar">&#9776;</button>
        <button id="theme-toggle" class="theme-toggle" type="button" aria-pressed="false" aria-label="Toggle dark mode" title="Toggle light/dark theme">
          <span class="theme-toggle-icon" aria-hidden="true"></span>
          <span id="theme-toggle-label" class="theme-toggle-label">Light</span>
        </button>
        <button id="refresh-button" type="button">Refresh</button>
        <span id="poll-state" class="state-chip">polling</span>
      </div>
    </header>

    <nav id="primary-sidebar" class="sidebar" aria-label="Primary navigation" data-collapsed="false">
      <div class="sidebar-pinned" aria-label="Active taskset">
        <div id="sidebar-active-taskset" class="sidebar-active-taskset" hidden>
          <span class="sidebar-active-label">Active taskset</span>
          <b id="sidebar-active-name" class="sidebar-active-name"></b>
          <div id="sidebar-active-progress" class="sidebar-active-progress"></div>
          <span id="sidebar-active-meta" class="sidebar-active-meta"></span>
        </div>
        <div id="sidebar-active-empty" class="sidebar-active-empty">No active taskset</div>
      </div>
      <div class="sidebar-nav" role="tablist" aria-label="Views">
        <div class="sidebar-group" data-group="home">
          <button class="sidebar-link is-active" type="button" role="tab" data-view="board" data-route="home/board" aria-selected="true">
            <span class="sidebar-icon" aria-hidden="true">&#8962;</span><span class="sidebar-label">Home</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="work">
          <span class="sidebar-group-title">WORK</span>
          <button class="sidebar-link" type="button" role="tab" data-view="tasksets" data-route="work/tasksets" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9635;</span><span class="sidebar-label">Tasksets</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="tsboard" data-route="work/board" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Taskset Board</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="work" data-route="work/explorer" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Work Explorer</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="planner" data-route="work/planner" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9998;</span><span class="sidebar-label">Planner</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="roadmap" data-route="work/roadmap" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Roadmap</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="agents">
          <span class="sidebar-group-title">AGENTS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="team" data-route="agents/team" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9733;</span><span class="sidebar-label">Team</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="agents" data-route="agents/list" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9737;</span><span class="sidebar-label">Agents</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="map" data-route="agents/map" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Live Map</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="comms">
          <span class="sidebar-group-title">COMMS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="channels" data-route="comms/channels" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Channels</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="messages" data-route="comms/messages" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Messages</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="meeting" data-route="comms/meetings" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9786;</span><span class="sidebar-label">Meetings</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="records">
          <span class="sidebar-group-title">RECORDS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="events" data-route="records/events" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9201;</span><span class="sidebar-label">Events</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="evidence" data-route="records/evidence" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9745;</span><span class="sidebar-label">Evidence</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="sources" data-route="records/sources" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Sources</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="ops">
          <span class="sidebar-group-title">OPS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="writes" data-route="ops/writes" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">Writes</span>
          </button>
        </div>
      </div>
      <button id="sidebar-collapse" class="sidebar-collapse" type="button" aria-label="Collapse sidebar">
        <span class="sidebar-collapse-icon" aria-hidden="true">&#8676;</span><span class="sidebar-label">Collapse</span>
      </button>
    </nav>
    <div id="sidebar-scrim" class="sidebar-scrim" hidden></div>

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
        <div id="view-board" class="view is-active">
          <p class="board-hint">Hover or focus a card for a peek. Drag a card between lanes to reorder, or focus it and press Ctrl+D to lift, arrows to move, Space to drop, Esc to cancel. Quick actions: Claim / Verify / Close.</p>
          <div id="kanban" class="kanban" aria-label="Kanban"></div>
          <div id="board-peek" class="board-peek" role="tooltip" aria-hidden="true" hidden></div>
          <div id="board-dnd-status" class="board-dnd-status" role="status" aria-live="polite"></div>
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
          <div id="taskset-completion-banner" class="taskset-completion" role="status" aria-live="polite" hidden></div>
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
        <div id="view-team" class="view">
          <div class="team-toolbar">
            <input id="team-filter" placeholder="team, role, callsign, agent id">
            <label class="team-online-toggle">
              <input id="team-online-toggle" type="checkbox">
              <span>Online only</span>
            </label>
          </div>
          <p id="team-summary" class="team-summary"></p>
          <div id="team-org" class="team-org" aria-label="Team agent organisation"></div>
        </div>
        <div id="view-agents" class="view">
          <div id="multipane-assurance-list" class="assurance-grid"></div>
          <div id="tasksets-list" class="taskset-strip"></div>
          <div id="list-toolbar-agents" class="list-toolbar-mount" data-list-view="agents"></div>
          <div id="agents-list" class="list-panel"></div>
        </div>
        <div id="view-channels" class="view">
          <div class="channels-grid">
            <aside class="channels-sidebar" aria-label="Channels">
              <h2 class="channels-heading">Channels</h2>
              <div id="channels-list" class="channels-list" role="tablist" aria-label="Channel list"></div>
            </aside>
            <section class="channels-main" aria-label="Channel conversation">
              <header class="channels-topbar">
                <h2 id="channels-active-name" class="channels-active-name">#general</h2>
                <span id="channels-active-meta" class="channels-active-meta"></span>
              </header>
              <div id="channels-threads" class="channels-threads" aria-label="Threads"></div>
              <form id="channels-input-form" class="channels-input" aria-label="Owner directive input">
                <label class="channels-input-label" for="channels-input-box">
                  Send a directive, or use <code>/meeting &lt;topic&gt; @role</code> or <code>/seminar &lt;topic&gt;</code>
                </label>
                <div class="channels-input-row">
                  <input id="channels-input-target" name="target" placeholder="@role (for directives)" aria-label="Target agent role">
                  <input id="channels-input-box" name="message" placeholder="Message #general, /meeting <topic> @role, /seminar <topic>" autocomplete="off" aria-label="Owner message or slash command">
                  <button id="channels-send" type="submit">Send</button>
                </div>
                <p id="channels-input-hint" class="channels-input-hint" role="status" aria-live="polite"></p>
              </form>
            </section>
          </div>
        </div>
        <div id="view-messages" class="view">
          <div id="list-toolbar-messages" class="list-toolbar-mount" data-list-view="messages"></div>
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
          <div id="list-toolbar-events" class="list-toolbar-mount" data-list-view="events"></div>
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
          <section class="live-map" aria-label="Live map">
            <header class="live-map-header">
              <h2>Live Map</h2>
              <p id="live-map-presence" class="live-map-presence" role="status">presence offline</p>
            </header>
            <div class="live-map-stage">
              <svg id="live-map-graph" class="live-map-graph" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Agent network graph"></svg>
            </div>
            <ul id="live-map-legend" class="live-map-legend" aria-label="Edge legend"></ul>
          </section>
          <div id="activity-feed" class="activity-feed" aria-live="polite" aria-label="Activity feed"></div>
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
  <div id="command-palette" class="command-palette" role="dialog" aria-modal="true" aria-label="Command palette" hidden>
    <div class="command-palette-backdrop" data-command-dismiss="1"></div>
    <div class="command-palette-panel" role="document">
      <input id="command-palette-input" class="command-palette-input" type="text" placeholder="Type a command or view (Ctrl+K)" aria-label="Command palette search" autocomplete="off">
      <div id="command-palette-results" class="command-palette-results" role="listbox" aria-label="Command palette results"></div>
    </div>
  </div>
  <script src="/app.js"></script>
</body>
</html>
"""


CSS = """/*
 * Theme tokens (TASK-AR-320).
 * :root is the default Notion-style LIGHT theme. [data-theme="dark"] restores
 * the original Linear dark palette. Every component consumes var(--token) only
 * so both themes share one structure. Status colors (success/warning/danger/
 * info/primary) keep the same semantic meaning across themes and are always
 * paired with text labels (never color-only signalling).
 */
:root {
  color-scheme: light;
  /* Surfaces */
  --canvas: #ffffff;
  --paper: #ffffff;
  --panel: #f7f7f5;
  --panel-strong: #f1f1ef;
  --surface-raised: #ffffff;
  /* Text */
  --ink: #37352f;
  --muted: #787774;
  --subtle: #9b9a97;
  --on-accent: #ffffff;
  /* Lines */
  --line: #e9e9e7;
  --line-strong: #d3d1cb;
  /* Status / semantic (consistent meaning in both themes) */
  --primary: #2e6fdb;
  --primary-hover: #1f5bc0;
  --success: #0f7b55;
  --warning: #cb7509;
  --danger: #e03e3e;
  --teal: #0f7b55;
  --blue: #2e6fdb;
  --amber: #cb7509;
  --red: #e03e3e;
  --violet: #6a48c9;
  --info: #2e6fdb;
  --purple: #6a48c9;
  /* Soft status fills (label chips, pills, left borders backgrounds) */
  --primary-soft: rgba(46, 111, 219, 0.10);
  --primary-soft-strong: rgba(46, 111, 219, 0.16);
  --primary-line: rgba(46, 111, 219, 0.30);
  --success-soft: rgba(15, 123, 85, 0.12);
  --success-line: rgba(15, 123, 85, 0.28);
  --warning-soft: rgba(203, 117, 9, 0.14);
  --warning-line: rgba(203, 117, 9, 0.30);
  --danger-soft: rgba(224, 62, 62, 0.12);
  --danger-line: rgba(224, 62, 62, 0.30);
  --teal-soft: rgba(15, 123, 85, 0.12);
  --teal-line: rgba(15, 123, 85, 0.28);
  --info-soft: rgba(46, 111, 219, 0.12);
  --violet-soft: rgba(106, 72, 201, 0.14);
  /* Generic raised/inset overlays used by cards and meta tiles */
  --raise: rgba(55, 53, 47, 0.03);
  --raise-strong: rgba(55, 53, 47, 0.05);
  --inset-soft: rgba(55, 53, 47, 0.02);
  --tile: #ffffff;
  --tile-line: var(--line-strong);
  --top-line: rgba(55, 53, 47, 0.08);
  --top-bg: rgba(255, 255, 255, 0.85);
  --hairline-top: rgba(0, 0, 0, 0.02);
  /* Sidebar / overlay scrim */
  --sidebar-bg: rgba(247, 247, 245, 0.92);
  --scrim: rgba(15, 15, 15, 0.40);
  --nav-active-text: var(--primary-hover);
  /* Effects */
  --radius: 8px;
  --shadow: 0 1px 2px rgba(15, 15, 15, 0.06), 0 8px 24px rgba(15, 15, 15, 0.06);
  --shadow-pop: 0 10px 30px rgba(15, 15, 15, 0.16);
  --focus: 0 0 0 3px rgba(46, 111, 219, 0.22);
  /* Decorative / brand */
  --brand-grad: linear-gradient(135deg, var(--primary), #6a48c9);
  --surface-grad: linear-gradient(180deg, var(--panel), var(--panel));
  --metric-grad: linear-gradient(180deg, var(--panel), var(--panel-strong));
  --canvas-grad: linear-gradient(180deg, #ffffff 0%, var(--canvas) 48%, #fbfbfa 100%);
  --grid-line: rgba(55, 53, 47, 0.035);
  --progress-track: rgba(55, 53, 47, 0.08);
  --progress-fill: linear-gradient(90deg, var(--success), var(--primary));
  --pre-bg: #f5f5f3;
  --pre-ink: #37352f;
  --accent: var(--primary);
  --border: var(--line-strong);
  --bg: var(--canvas);
  /* Live map pulse highlight (TASK-AR-326) */
  --pulse: var(--primary);
  --pulse-soft: var(--primary-soft-strong);
}
[data-theme="dark"] {
  color-scheme: dark;
  /* Surfaces */
  --canvas: #010102;
  --paper: #010102;
  --panel: #0f1011;
  --panel-strong: #15171a;
  --surface-raised: #1b1d22;
  /* Text */
  --ink: #f7f8f8;
  --muted: #a2a8b3;
  --subtle: #62666d;
  --on-accent: #ffffff;
  /* Lines */
  --line: #23252a;
  --line-strong: #343844;
  /* Status / semantic */
  --primary: #5e6ad2;
  --primary-hover: #828fff;
  --success: #27a644;
  --warning: #d99a2b;
  --danger: #f04438;
  --teal: #31d0aa;
  --blue: #57a0ff;
  --amber: #d99a2b;
  --red: #f04438;
  --violet: #5e6ad2;
  --info: #57a0ff;
  --purple: #5e6ad2;
  /* Soft status fills */
  --primary-soft: rgba(94, 106, 210, 0.12);
  --primary-soft-strong: rgba(94, 106, 210, 0.18);
  --primary-line: rgba(130, 143, 255, 0.36);
  --success-soft: rgba(39, 166, 68, 0.18);
  --success-line: rgba(39, 166, 68, 0.30);
  --warning-soft: rgba(217, 154, 43, 0.18);
  --warning-line: rgba(217, 154, 43, 0.24);
  --danger-soft: rgba(240, 68, 56, 0.10);
  --danger-line: rgba(240, 68, 56, 0.24);
  --teal-soft: rgba(49, 208, 170, 0.10);
  --teal-line: rgba(49, 208, 170, 0.20);
  --info-soft: rgba(87, 160, 255, 0.18);
  --violet-soft: rgba(94, 106, 210, 0.18);
  /* Generic raised/inset overlays */
  --raise: rgba(255, 255, 255, 0.044);
  --raise-strong: rgba(255, 255, 255, 0.032);
  --inset-soft: rgba(255, 255, 255, 0.026);
  --tile: rgba(1, 1, 2, 0.34);
  --tile-line: rgba(52, 56, 68, 0.76);
  --top-line: rgba(255, 255, 255, 0.08);
  --top-bg: rgba(12, 13, 16, 0.88);
  --hairline-top: rgba(255, 255, 255, 0.035);
  /* Sidebar / overlay scrim */
  --sidebar-bg: rgba(12, 13, 16, 0.92);
  --scrim: rgba(0, 0, 0, 0.5);
  --nav-active-text: #ffffff;
  /* Effects */
  --shadow: 0 18px 50px rgba(0, 0, 0, 0.34);
  --shadow-pop: 0 10px 30px rgba(0, 0, 0, 0.5);
  --focus: 0 0 0 3px rgba(130, 143, 255, 0.22);
  /* Decorative / brand */
  --brand-grad: linear-gradient(135deg, var(--primary), #20233b);
  --surface-grad: linear-gradient(180deg, rgba(15, 16, 17, 0.96), rgba(10, 11, 13, 0.96));
  --metric-grad: linear-gradient(180deg, rgba(21, 23, 26, 0.94), rgba(15, 16, 17, 0.94));
  --canvas-grad: linear-gradient(180deg, #08090b 0%, var(--canvas) 48%, #040405 100%);
  --grid-line: rgba(247, 248, 248, 0.035);
  --progress-track: rgba(255, 255, 255, 0.08);
  --progress-fill: linear-gradient(90deg, var(--teal), var(--primary-hover));
  --pre-bg: #050608;
  --pre-ink: #e9ebf0;
  --accent: #5b8def;
  --border: #2a2a3a;
  --bg: #11111a;
  /* Live map pulse highlight (TASK-AR-326) */
  --pulse: var(--primary-hover);
  --pulse-soft: var(--primary-soft-strong);
}
* { box-sizing: border-box; }
html { background: var(--canvas); }
body {
  margin: 0;
  min-height: 100vh;
  font-family: "Geist", "IBM Plex Sans", "Segoe UI", sans-serif;
  background:
    linear-gradient(var(--grid-line) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line) 1px, transparent 1px),
    var(--canvas-grad);
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
  --sidebar-width: 232px;
  --sidebar-rail: 60px;
}
.sidebar {
  position: fixed;
  top: 77px;
  left: 0;
  bottom: 0;
  width: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 10px;
  border-right: 1px solid var(--line);
  background: var(--sidebar-bg);
  backdrop-filter: blur(14px);
  overflow-y: auto;
  z-index: 3;
  transition: width 160ms ease, transform 200ms ease;
}
.sidebar[data-collapsed="true"] {
  width: var(--sidebar-rail);
}
.sidebar[data-collapsed="true"] .sidebar-label,
.sidebar[data-collapsed="true"] .sidebar-group-title,
.sidebar[data-collapsed="true"] .sidebar-active-taskset,
.sidebar[data-collapsed="true"] .sidebar-active-empty {
  display: none;
}
.sidebar-pinned {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--primary-soft);
  padding: 10px;
  margin-bottom: 6px;
}
.sidebar-active-label {
  display: block;
  color: var(--subtle);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.sidebar-active-name {
  display: block;
  margin: 4px 0 6px;
  color: var(--ink);
  font-size: 13px;
  overflow-wrap: anywhere;
}
.sidebar-active-progress {
  margin-bottom: 6px;
}
.sidebar-active-meta {
  color: var(--muted);
  font-size: 11px;
}
.sidebar-active-empty {
  color: var(--subtle);
  font-size: 11px;
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1 1 auto;
}
.sidebar-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 8px;
}
.sidebar-group-title {
  color: var(--subtle);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 8px 10px 2px;
}
.sidebar-link {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-size: 13px;
  font-weight: 600;
  text-align: left;
  padding: 8px 10px;
}
.sidebar-link:hover {
  transform: none;
  color: var(--ink);
  background: var(--raise-strong);
}
.sidebar-link.is-active {
  color: var(--nav-active-text);
  background: var(--primary-soft-strong);
  border-color: var(--primary-line);
}
.sidebar-link:focus-visible {
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
  box-shadow: var(--focus);
}
.sidebar-icon {
  flex: 0 0 auto;
  width: 20px;
  text-align: center;
  font-size: 15px;
  line-height: 1;
}
.sidebar[data-collapsed="true"] .sidebar-link {
  justify-content: center;
}
.sidebar-collapse {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-weight: 600;
  padding: 8px 10px;
  margin-top: auto;
}
.sidebar-collapse:hover {
  transform: none;
  color: var(--ink);
}
.sidebar-toggle {
  display: none;
  padding: 9px 11px;
}
.sidebar-scrim {
  position: fixed;
  inset: 0;
  z-index: 2;
  background: var(--scrim);
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  padding: 18px 24px;
  border-bottom: 1px solid var(--top-line);
  background: var(--top-bg);
  backdrop-filter: blur(18px);
  position: sticky;
  top: 0;
  z-index: 4;
  box-shadow: 0 1px 0 var(--hairline-top);
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
  background: var(--brand-grad);
  box-shadow: 0 0 0 1px var(--primary-line), 0 16px 34px var(--primary-soft);
}
.brand-mark rect {
  fill: rgba(255, 255, 255, 0.14);
  stroke: rgba(255, 255, 255, 0.72);
}
.brand-mark path,
.brand-mark circle {
  fill: none;
  stroke: #ffffff;
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
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  padding: 9px 12px;
  min-height: 36px;
  font: inherit;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  background: linear-gradient(180deg, var(--primary), var(--primary-hover));
  color: var(--on-accent);
  box-shadow: 0 10px 22px var(--primary-soft);
  transition: transform 140ms ease, border-color 140ms ease, background 140ms ease;
}
.theme-toggle {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: var(--raise);
  border: 1px solid var(--line-strong);
  color: var(--ink);
  box-shadow: none;
}
.theme-toggle:hover { border-color: var(--primary); }
.theme-toggle-icon {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--warning);
  box-shadow: 0 0 0 2px var(--warning-soft);
}
[data-theme="dark"] .theme-toggle-icon {
  background: transparent;
  box-shadow: inset -4px -2px 0 0 var(--ink);
}
.theme-toggle-label {
  font-size: 12px;
  font-weight: 700;
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
  background: var(--surface-raised);
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
  border-color: var(--primary);
  box-shadow: var(--focus);
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
  align-items: start;
  padding: 18px 24px 28px;
  margin-left: var(--sidebar-width);
  transition: margin-left 160ms ease;
}
.shell[data-sidebar-collapsed="true"] .layout {
  margin-left: var(--sidebar-rail);
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
  background: var(--metric-grad);
  padding: 14px;
  box-shadow: inset 0 1px 0 var(--hairline-top);
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
  background: var(--surface-grad);
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
  color: var(--primary);
  background: var(--primary-soft-strong);
  border-color: var(--primary-line);
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
  background: var(--raise-strong);
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
  background: var(--primary-soft-strong);
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
.lane-body {
  min-height: 48px;
}
.board-hint {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.4;
  margin-bottom: 8px;
}
.lane.is-drop-target {
  border-color: var(--primary-hover);
  background: var(--primary-soft);
}
.lane-body.is-dragover {
  outline: 2px dashed var(--primary-hover);
  outline-offset: -2px;
  border-radius: var(--radius);
}
.task-card.is-dragging {
  opacity: 0.45;
}
.task-card.is-lifted {
  outline: 2px solid var(--primary-hover);
  outline-offset: 1px;
}
.drop-placeholder {
  height: 6px;
  border-radius: 999px;
  background: var(--primary-hover);
  margin: 2px 0;
}
.task-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 2px;
}
.task-card-actions button {
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 6px;
  border: 1px solid var(--line-strong);
  background: var(--tile);
  color: var(--ink);
  cursor: pointer;
}
.task-card-actions button:hover {
  border-color: var(--primary-hover);
}
.task-card-actions button:focus-visible {
  outline: 2px solid var(--primary-hover);
  outline-offset: 1px;
}
.board-peek {
  position: fixed;
  z-index: 40;
  max-width: 320px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  background: var(--surface-raised);
  box-shadow: var(--shadow-pop);
  padding: 12px;
  color: var(--ink);
  font-size: 12px;
  line-height: 1.45;
  pointer-events: none;
}
.board-peek h3 {
  font-size: 13px;
  margin-bottom: 4px;
}
.board-peek code {
  color: var(--primary-hover);
  font-family: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;
  font-size: 11px;
}
.board-peek dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 2px 10px;
  margin-top: 6px;
}
.board-peek dt {
  color: var(--subtle);
}
.board-peek dd {
  margin: 0;
  overflow-wrap: anywhere;
}
.board-dnd-status {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
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
.taskset-completion {
  border: 1px solid var(--success-line);
  border-left: 3px solid var(--success);
  border-radius: var(--radius);
  background: var(--success-soft);
  color: var(--ink);
  padding: 12px;
  display: grid;
  gap: 8px;
  margin-bottom: 12px;
}
.taskset-completion-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.taskset-completion-badge {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--success);
}
.taskset-completion-message {
  color: var(--muted);
  font-size: 13px;
}
.taskset-completion-next {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--tile);
  padding: 8px 10px;
}
.taskset-completion-next-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--subtle);
}
.taskset-completion-next-meta {
  font-size: 12px;
  color: var(--muted);
}
.taskset-completion-next-cmd {
  font-size: 12px;
  color: var(--ink);
  background: var(--raise);
  border-radius: 4px;
  padding: 2px 6px;
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
  background: var(--inset-soft);
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
  background: var(--raise);
  color: var(--ink);
  padding: 10px;
  display: grid;
  gap: 7px;
  text-align: left;
  box-shadow: inset 0 1px 0 var(--inset-soft);
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
  border: 1px solid var(--tile-line);
  border-radius: 6px;
  background: var(--tile);
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
  border: 1px solid var(--primary-line);
  border-radius: 999px;
  padding: 4px 7px;
  background: var(--primary-soft);
  color: var(--primary);
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
/* ----- Live map: presence + node/edge graph (TASK-AR-326) ----- */
.live-map {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
}
.live-map-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.live-map-header h2 { margin: 0; }
.live-map-presence {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
}
.live-map-stage {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--canvas-grad);
  overflow: hidden;
}
.live-map-graph {
  display: block;
  width: 100%;
  height: 420px;
}
.live-map-edge {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: none;
  opacity: 0.55;
  transition: stroke 0.2s ease, opacity 0.2s ease, stroke-width 0.2s ease;
}
.live-map-edge.kind-message { stroke: var(--blue); }
.live-map-edge.kind-assignment { stroke: var(--success); }
.live-map-edge.kind-review { stroke: var(--amber); }
.live-map-edge.kind-block { stroke: var(--danger); }
.live-map-edge.is-pulsing {
  stroke: var(--pulse);
  stroke-width: 3.5;
  opacity: 1;
  filter: drop-shadow(0 0 6px var(--pulse-soft));
}
.live-map-node circle {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: var(--panel);
  transition: fill 0.2s ease, stroke 0.2s ease;
}
.live-map-node.kind-owner circle { fill: var(--primary-soft-strong); stroke: var(--primary-line); }
.live-map-node.kind-agent circle { fill: var(--panel-strong); }
.live-map-node.kind-taskset circle { fill: var(--success-soft); stroke: var(--success-line); }
.live-map-node.kind-gate circle { fill: var(--warning-soft); stroke: var(--warning-line); }
.live-map-node.presence-working circle { stroke: var(--blue); }
.live-map-node.presence-reviewing circle { stroke: var(--amber); }
.live-map-node.presence-in_meeting circle { stroke: var(--violet); }
.live-map-node.presence-online circle { stroke: var(--success); }
.live-map-node.is-pulsing circle {
  fill: var(--pulse-soft);
  stroke: var(--pulse);
}
.live-map-node text {
  fill: var(--ink);
  font-size: 11px;
  text-anchor: middle;
}
.live-map-empty {
  padding: 40px 16px;
  text-align: center;
  color: var(--subtle);
}
.live-map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  color: var(--muted);
}
.live-map-legend li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.live-map-legend .legend-swatch {
  width: 14px;
  height: 0;
  border-top: 3px solid var(--line-strong);
}
.live-map-legend .legend-message { border-top-color: var(--blue); }
.live-map-legend .legend-assignment { border-top-color: var(--success); }
.live-map-legend .legend-review { border-top-color: var(--amber); }
.live-map-legend .legend-block { border-top-color: var(--danger); }
.activity-feed {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 320px;
  pointer-events: none;
}
.activity-toast {
  pointer-events: auto;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow-pop);
  font-size: 12px;
  color: var(--ink);
  opacity: 1;
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.activity-toast.is-leaving { opacity: 0; transform: translateY(6px); }
.activity-toast.kind-message { border-left-color: var(--blue); }
.activity-toast.kind-assignment { border-left-color: var(--success); }
.activity-toast.kind-review { border-left-color: var(--amber); }
.activity-toast.kind-block { border-left-color: var(--danger); }
.activity-toast b { display: block; font-size: 11px; color: var(--muted); }
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
  border: 1px solid var(--teal-line);
  background: var(--teal-soft);
  color: var(--teal);
  font-size: 12px;
}
.pill.high { color: var(--red); border-color: var(--danger-line); background: var(--danger-soft); }
.pill.medium { color: var(--amber); border-color: var(--warning-line); background: var(--warning-soft); }
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
  background: var(--progress-track);
}
.progress-fill {
  height: 100%;
  border-radius: 999px;
  background: var(--progress-fill);
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
  background: var(--raise);
  color: var(--ink);
  padding: 8px 10px;
  text-align: left;
  box-shadow: inset 0 1px 0 var(--inset-soft);
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
  border: 1px solid var(--teal-line);
  border-radius: 999px;
  background: var(--teal-soft);
  color: var(--teal);
  font-size: 11px;
  padding: 3px 8px;
  white-space: nowrap;
}
.evidence-badge {
  border: 1px solid var(--primary-line);
  border-radius: 999px;
  background: var(--primary-soft);
  color: var(--primary);
  font-size: 11px;
  padding: 3px 8px;
  white-space: nowrap;
}
.work-node-detail {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
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
  border: 1px solid var(--tile-line);
  border-radius: 6px;
  background: var(--tile);
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
  background: var(--inset-soft);
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
  background: var(--tile);
  padding: 8px;
  cursor: grab;
  min-width: 0;
}
.meeting-card:focus-visible {
  outline: 2px solid var(--accent);
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
  background: var(--inset-soft);
  padding: 12px;
  min-height: 96px;
  margin-bottom: 10px;
}
.meeting-dropzone.is-dragover {
  border-color: var(--accent);
  background: var(--info-soft);
}
.meeting-dropzone:focus-visible {
  outline: 2px solid var(--accent);
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
  border: 1px solid var(--accent);
  border-radius: 8px;
  background: var(--info-soft);
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
  color: var(--warning);
  min-height: 16px;
}
.meeting-validation.is-ok {
  color: var(--success);
}
/* ===== Channels view (TASK-AR-327): Slack/Discord-style spectating ===== */
.channels-grid {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 14px;
  align-items: start;
}
.channels-sidebar {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  padding: 10px;
}
.channels-heading {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--subtle);
  margin-bottom: 8px;
}
.channels-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.channel-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 6px;
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--ink);
  text-align: left;
  padding: 7px 9px;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 13px;
}
.channel-link:hover {
  background: var(--raise-strong);
}
.channel-link.is-active {
  background: var(--primary-soft);
  color: var(--nav-active-text);
  font-weight: 600;
}
.channel-link .channel-count {
  font-size: 11px;
  color: var(--muted);
  background: var(--raise);
  border-radius: 999px;
  padding: 1px 7px;
}
.channels-main {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--paper);
  display: flex;
  flex-direction: column;
  min-height: 360px;
}
.channels-topbar {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--line);
}
.channels-active-name {
  font-size: 16px;
}
.channels-active-meta {
  font-size: 12px;
  color: var(--muted);
}
.channels-threads {
  flex: 1;
  overflow-y: auto;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.channel-thread {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: 10px 12px;
}
.channel-thread-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}
.channel-thread-title {
  font-weight: 600;
  font-size: 13px;
}
.channel-thread-task {
  font-size: 11px;
  color: var(--muted);
}
.channel-message {
  display: flex;
  gap: 9px;
  padding: 6px 0;
}
.channel-message + .channel-message {
  border-top: 1px solid var(--line);
}
.channel-avatar {
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--on-accent);
  background: var(--role-color, var(--primary));
}
.channel-message-body {
  flex: 1;
  min-width: 0;
}
.channel-message-head {
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.channel-sender {
  font-weight: 600;
  font-size: 13px;
  color: var(--role-color, var(--ink));
}
.channel-ts {
  font-size: 11px;
  color: var(--subtle);
}
.channel-message-text {
  font-size: 13px;
  color: var(--ink);
  line-height: 1.4;
  margin-top: 2px;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.channels-empty {
  color: var(--muted);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: 18px;
  text-align: center;
}
.channels-input {
  border-top: 1px solid var(--line);
  padding: 10px 14px 12px;
  background: var(--panel);
}
.channels-input-label {
  display: block;
  font-size: 11px;
  color: var(--muted);
  margin-bottom: 6px;
}
.channels-input-label code {
  background: var(--raise);
  border-radius: 4px;
  padding: 0 4px;
}
.channels-input-row {
  display: flex;
  gap: 8px;
}
.channels-input-row input {
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  background: var(--surface-raised);
  color: var(--ink);
  padding: 8px 10px;
  font-size: 13px;
}
#channels-input-target {
  flex: 0 0 150px;
}
#channels-input-box {
  flex: 1;
}
.channels-input-hint {
  font-size: 11px;
  color: var(--muted);
  min-height: 14px;
  margin-top: 6px;
}
.channels-input-hint.is-error {
  color: var(--danger);
}
.channels-input-hint.is-ok {
  color: var(--success);
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
  background: var(--inset-soft);
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
  background: var(--pre-bg);
  color: var(--pre-ink);
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
.phase-plan { background: var(--raise-strong); color: var(--muted); }
.phase-work { background: var(--info-soft); color: var(--blue); }
.phase-review { background: var(--warning-soft); color: var(--amber); }
.phase-done { background: var(--success-soft); color: var(--success); }
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

.team-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}
.team-online-toggle { display: flex; gap: 6px; align-items: center; color: var(--muted); font-size: 13px; }
.team-summary { color: var(--muted); font-size: 13px; margin: 0 0 12px; }
.team-org { display: flex; flex-direction: column; gap: 18px; }
.team-group {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
  background: var(--panel);
}
.team-group-header { display: flex; gap: 10px; align-items: baseline; margin-bottom: 12px; }
.team-group-header b { font-size: 15px; }
.team-group-header span { color: var(--muted); font-size: 13px; }
.team-role-badges { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.team-role-badge {
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 11px;
  border: 1px solid var(--line-strong);
  color: var(--muted);
}
.team-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}
.agent-character-card {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.agent-character-card.presence-working { border-left: 3px solid var(--blue); }
.agent-character-card.presence-reviewing { border-left: 3px solid var(--amber); }
.agent-character-card.presence-in_meeting { border-left: 3px solid var(--violet); }
.agent-character-card.presence-online { border-left: 3px solid var(--success); }
.agent-character-card.presence-offline { border-left: 3px solid var(--subtle); }
.agent-character-header { display: flex; gap: 12px; align-items: center; }
.agent-character-avatar {
  position: relative;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--surface-raised);
  border: 2px solid var(--line-strong);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex: 0 0 auto;
}
.agent-character-avatar .presence-ring {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--panel-strong);
  background: var(--subtle);
}
.agent-character-card.presence-working .presence-ring { background: var(--blue); }
.agent-character-card.presence-reviewing .presence-ring { background: var(--amber); }
.agent-character-card.presence-in_meeting .presence-ring { background: var(--violet); }
.agent-character-card.presence-online .presence-ring { background: var(--success); }
.agent-character-identity { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.agent-character-identity b { overflow-wrap: anywhere; }
.agent-character-identity span { color: var(--muted); font-size: 12px; }
.agent-character-level {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--muted);
}
.agent-character-level strong { color: var(--ink); }
.agent-character-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  font-size: 12px;
}
.agent-character-task { font-size: 12px; color: var(--muted); }
.agent-character-task code { color: var(--ink); }
.agent-character-activity { list-style: none; margin: 0; padding: 0; font-size: 12px; color: var(--muted); }

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
  .layout {
    padding: 14px;
    margin-left: 0;
  }
  .shell[data-sidebar-collapsed="true"] .layout {
    margin-left: 0;
  }
  .sidebar-toggle {
    display: inline-flex;
  }
  .sidebar {
    top: 0;
    width: min(82vw, 300px);
    transform: translateX(-100%);
    box-shadow: var(--shadow);
  }
  .sidebar[data-collapsed="true"] {
    width: min(82vw, 300px);
  }
  .sidebar[data-collapsed="true"] .sidebar-label,
  .sidebar[data-collapsed="true"] .sidebar-group-title,
  .sidebar[data-collapsed="true"] .sidebar-active-taskset,
  .sidebar[data-collapsed="true"] .sidebar-active-empty {
    display: revert;
  }
  .sidebar.is-open {
    transform: translateX(0);
  }
  .sidebar-collapse {
    display: none;
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
  .team-toolbar,
  .team-cards,
  .agent-character-meta,
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
  border-left: 2px solid var(--border);
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
  border: 2px solid var(--bg);
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

/* ===== Common list pattern toolbar / density / groups (TASK-AR-322) ===== */
.list-toolbar-mount {
  margin-bottom: 10px;
}
.list-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
}
.list-toolbar-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.list-toolbar-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.list-toolbar input,
.list-toolbar select {
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  color: var(--ink);
  padding: 5px 8px;
  font-size: 12px;
}
.list-toolbar input:focus,
.list-toolbar select:focus {
  outline: none;
  box-shadow: var(--focus);
}
.list-search {
  min-width: 160px;
}
.list-density {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.list-density-btn {
  border: 1px solid var(--line-strong);
  background: var(--panel-strong);
  color: var(--muted);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
}
.list-density-btn.is-active {
  background: var(--primary-soft-strong);
  border-color: var(--primary-hover);
  color: var(--ink);
}
.list-save-view {
  border: 1px solid var(--line-strong);
  background: var(--panel-strong);
  color: var(--ink);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
}
.list-group-block {
  margin-bottom: 12px;
}
.list-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  padding: 4px 2px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 6px;
}
.list-group-count {
  background: var(--primary-soft);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: 1px 8px;
  color: var(--ink);
}
.list-panel.density-compact .agent-card,
.list-panel.density-compact .list-row,
.list-panel.density-compact .audit-card {
  padding: 6px 8px;
  font-size: 11px;
  line-height: 1.25;
}
.list-panel.density-compact .agent-card-meta span,
.list-panel.density-compact .audit-card-meta span {
  font-size: 10px;
}
.list-panel.density-cozy .agent-card,
.list-panel.density-cozy .list-row,
.list-panel.density-cozy .audit-card {
  padding: 10px 12px;
}
.list-panel.density-detail .agent-card,
.list-panel.density-detail .list-row,
.list-panel.density-detail .audit-card {
  padding: 16px 18px;
  font-size: 13px;
  line-height: 1.5;
}
.list-row.is-cursor,
.agent-card.is-cursor,
.audit-card.is-cursor {
  outline: 2px solid var(--primary-hover);
  outline-offset: 1px;
}
.command-palette {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.command-palette[hidden] {
  display: none;
}
.command-palette-backdrop {
  position: absolute;
  inset: 0;
  background: var(--scrim);
}
.command-palette-panel {
  position: relative;
  margin-top: 12vh;
  width: min(560px, 90vw);
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.command-palette-input {
  width: 100%;
  border: none;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
  color: var(--ink);
  padding: 14px 16px;
  font-size: 15px;
}
.command-palette-input:focus {
  outline: none;
}
.command-palette-results {
  max-height: 50vh;
  overflow-y: auto;
}
.command-palette-item {
  padding: 10px 16px;
  font-size: 13px;
  cursor: pointer;
  color: var(--ink);
}
.command-palette-item.is-active,
.command-palette-item:hover {
  background: var(--primary-soft-strong);
}
.command-palette-empty {
  padding: 14px 16px;
  color: var(--muted);
  font-size: 13px;
}
"""

JS = """// --- Theme system (TASK-AR-320) -------------------------------------------
// Default is the Notion-style light theme. Dark mode restores the Linear
// palette. Resolution order on first load: saved localStorage choice, then the
// OS prefers-color-scheme hint; thereafter the header toggle persists a choice.
const THEME_STORAGE_KEY = "agent-runtime-theme";
function systemPrefersDark() {
  return Boolean(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
}
function storedTheme() {
  try {
    const value = window.localStorage.getItem(THEME_STORAGE_KEY);
    return value === "dark" || value === "light" ? value : null;
  } catch (error) {
    return null;
  }
}
function resolveInitialTheme() {
  return storedTheme() || (systemPrefersDark() ? "dark" : "light");
}
function applyTheme(theme) {
  const mode = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", mode);
  const toggle = document.getElementById("theme-toggle");
  const label = document.getElementById("theme-toggle-label");
  if (toggle) {
    toggle.setAttribute("aria-pressed", mode === "dark" ? "true" : "false");
    toggle.setAttribute("aria-label", mode === "dark" ? "Switch to light mode" : "Switch to dark mode");
  }
  if (label) label.textContent = mode === "dark" ? "Dark" : "Light";
}
function setTheme(theme, persist) {
  const mode = theme === "dark" ? "dark" : "light";
  applyTheme(mode);
  if (persist) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, mode);
    } catch (error) {
      /* localStorage unavailable (private mode) - theme still applies for the session */
    }
  }
}
function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  setTheme(current === "dark" ? "light" : "dark", true);
}
function initTheme() {
  applyTheme(resolveInitialTheme());
  const toggle = document.getElementById("theme-toggle");
  if (toggle) toggle.addEventListener("click", toggleTheme);
  if (window.matchMedia) {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event) => {
      if (!storedTheme()) setTheme(event.matches ? "dark" : "light", false);
    };
    if (media.addEventListener) media.addEventListener("change", onChange);
    else if (media.addListener) media.addListener(onChange);
  }
}
initTheme();

const lanes = ["Backlog", "Ready", "In Progress", "Review", "Blocked", "Done"];
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
let teamOnlineOnly = false;
let peekTimer = null;
let peekAnchorId = null;
let boardDragId = null;
let boardLifted = null;

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
    const previous = runtimeState;
    runtimeState = JSON.parse(event.data);
    renderAll();
    setText("poll-state", "live");
    // Phase-2 SSE-live: diff successive snapshots and pulse the edges /
    // presence nodes that changed, surfacing a toast in the activity feed.
    reconcileLiveMap(previous, runtimeState);
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

/* ===== Common list pattern: sort / filter / group / search + density (TASK-AR-322) ===== */
const LIST_DENSITY_LEVELS = ["compact", "cozy", "detail"];
const LIST_GROUP_OPTIONS = [
  { value: "taskset", label: "Task set" },
  { value: "status", label: "Status" },
  { value: "owner", label: "Owner" },
];
const LIST_SORT_OPTIONS = [
  { value: "priority", label: "Priority" },
  { value: "updated", label: "Updated time" },
  { value: "progress", label: "Progress" },
];
const LIST_FILTER_KEYS = ["status", "priority", "owner", "taskset", "tag", "date"];
const PRIORITY_RANK = { P0: 0, P1: 1, P2: 2, P3: 3, P4: 4 };

// Per-view active control state, hydrated from URL + localStorage.
let listControls = {};
// Per-view keyboard cursor index for j/k navigation.
let listCursor = {};

function listStorageKey(view) {
  return `ar.listControls.${view}`;
}

function defaultListControls() {
  return { search: "", sort: "priority", group: "taskset", density: "cozy", filters: {}, view: "" };
}

function readUrlListControls(view) {
  try {
    const params = new URLSearchParams(window.location.search);
    const raw = params.get(`lc_${view}`);
    if (!raw) return null;
    return JSON.parse(decodeURIComponent(raw));
  } catch (error) {
    return null;
  }
}

function readStoredListControls(view) {
  try {
    const raw = window.localStorage.getItem(listStorageKey(view));
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    return null;
  }
}

function loadListControls(view) {
  if (listControls[view]) return listControls[view];
  const base = defaultListControls();
  // URL wins over localStorage so a shared link reproduces the same list state.
  const stored = readStoredListControls(view) || {};
  const fromUrl = readUrlListControls(view) || {};
  const merged = Object.assign(base, stored, fromUrl);
  merged.filters = Object.assign({}, base.filters, stored.filters || {}, fromUrl.filters || {});
  listControls[view] = merged;
  return merged;
}

function persistListControls(view) {
  const controls = listControls[view];
  if (!controls) return;
  try {
    window.localStorage.setItem(listStorageKey(view), JSON.stringify(controls));
  } catch (error) { /* storage may be unavailable */ }
  try {
    const params = new URLSearchParams(window.location.search);
    params.set(`lc_${view}`, encodeURIComponent(JSON.stringify(controls)));
    const next = `${window.location.pathname}?${params.toString()}${window.location.hash}`;
    window.history.replaceState(null, "", next);
  } catch (error) { /* history may be unavailable */ }
}

function savedViewsKey(view) {
  return `ar.savedViews.${view}`;
}

function loadSavedViews(view) {
  try {
    const raw = window.localStorage.getItem(savedViewsKey(view));
    return raw ? JSON.parse(raw) : {};
  } catch (error) {
    return {};
  }
}

function saveNamedView(view, name) {
  if (!name) return;
  const views = loadSavedViews(view);
  views[name] = JSON.parse(JSON.stringify(listControls[view] || defaultListControls()));
  try {
    window.localStorage.setItem(savedViewsKey(view), JSON.stringify(views));
  } catch (error) { /* storage may be unavailable */ }
}

function applyNamedView(view, name) {
  const views = loadSavedViews(view);
  if (!views[name]) return;
  const base = defaultListControls();
  const next = Object.assign(base, views[name]);
  next.filters = Object.assign({}, views[name].filters || {});
  listControls[view] = next;
  persistListControls(view);
}

// Normalised accessors so the same logic spans task/agent/event/message/evidence rows.
function listItemStatus(item) {
  return String(item.status || item.lane || item.state || "").toLowerCase();
}
function listItemPriority(item) {
  return String(item.priority || "").toUpperCase();
}
function listItemOwner(item) {
  return String(item.owner_agent || item.owner || item.actor || item.role || item.from || "").toLowerCase();
}
function listItemTaskset(item) {
  return String(item.task_set_id || item.taskset || "").toLowerCase();
}
function listItemTags(item) {
  const tags = item.labels || item.tags || [];
  return Array.isArray(tags) ? tags.map((tag) => String(tag).toLowerCase()) : [];
}
function listItemDate(item) {
  return String(item.updated_at || item.last_updated || item.created_at || item.ts || item.generated_at || "");
}
function listItemProgress(item) {
  const pct = numericPct(item.progress_pct);
  return pct === null ? -1 : pct;
}

// Build facet option sets directly from the supplied rows (client-side, no server help needed).
function computeListFacets(items) {
  const facets = { status: new Set(), priority: new Set(), owner: new Set(), taskset: new Set(), tag: new Set() };
  (items || []).forEach((item) => {
    const status = listItemStatus(item);
    if (status) facets.status.add(status);
    const priority = listItemPriority(item);
    if (priority) facets.priority.add(priority);
    const owner = listItemOwner(item);
    if (owner) facets.owner.add(owner);
    const taskset = listItemTaskset(item);
    if (taskset) facets.taskset.add(taskset);
    listItemTags(item).forEach((tag) => { if (tag) facets.tag.add(tag); });
  });
  const out = {};
  Object.keys(facets).forEach((key) => { out[key] = Array.from(facets[key]).sort(); });
  return out;
}

function listItemMatchesFilters(item, filters, searchText) {
  if (filters.status && listItemStatus(item) !== filters.status) return false;
  if (filters.priority && listItemPriority(item) !== filters.priority) return false;
  if (filters.owner && listItemOwner(item) !== filters.owner) return false;
  if (filters.taskset && listItemTaskset(item) !== filters.taskset) return false;
  if (filters.tag && !listItemTags(item).includes(filters.tag)) return false;
  if (filters.date && !listItemDate(item).startsWith(filters.date)) return false;
  if (searchText) {
    if (!JSON.stringify(item).toLowerCase().includes(searchText.toLowerCase())) return false;
  }
  return true;
}

function sortListItems(items, sort) {
  const copy = items.slice();
  copy.sort((a, b) => {
    if (sort === "priority") {
      const ra = PRIORITY_RANK[listItemPriority(a)] ?? 99;
      const rb = PRIORITY_RANK[listItemPriority(b)] ?? 99;
      return ra - rb;
    }
    if (sort === "updated") {
      return listItemDate(b).localeCompare(listItemDate(a));
    }
    if (sort === "progress") {
      return listItemProgress(b) - listItemProgress(a);
    }
    return 0;
  });
  return copy;
}

function groupListItems(items, group) {
  const buckets = new Map();
  items.forEach((item) => {
    let key = "ungrouped";
    if (group === "status") key = listItemStatus(item) || "unknown";
    else if (group === "owner") key = listItemOwner(item) || "unassigned";
    else key = listItemTaskset(item) || "unassigned";
    if (!buckets.has(key)) buckets.set(key, []);
    buckets.get(key).push(item);
  });
  return Array.from(buckets.entries()).map(([key, rows]) => ({ key, rows }));
}

// Single entry point: returns filtered + sorted + grouped rows for a view.
function applyListControls(view, items) {
  const controls = loadListControls(view);
  const filtered = (items || []).filter((item) => listItemMatchesFilters(item, controls.filters || {}, controls.search));
  const sorted = sortListItems(filtered, controls.sort);
  const groups = groupListItems(sorted, controls.group);
  return { controls, filtered: sorted, groups };
}

function facetSelectHtml(view, key, label, options, selected) {
  const opts = [`<option value="">All ${escapeHtml(label.toLowerCase())}</option>`]
    .concat(options.map((value) => `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(value)}</option>`))
    .join("");
  return `<label class="list-toolbar-field"><span class="list-toolbar-label">${escapeHtml(label)}</span><select class="list-filter" data-list-view="${escapeHtml(view)}" data-filter-key="${escapeHtml(key)}">${opts}</select></label>`;
}

// Render the shared toolbar (search + filters + sort + group + density + saved views) into a mount.
function renderListToolbar(view, items) {
  const mount = $(`list-toolbar-${view}`);
  if (!mount) return;
  const controls = loadListControls(view);
  const facets = computeListFacets(items);
  const savedViews = loadSavedViews(view);
  const sortOpts = LIST_SORT_OPTIONS.map((opt) => `<option value="${opt.value}"${opt.value === controls.sort ? " selected" : ""}>${escapeHtml(opt.label)}</option>`).join("");
  const groupOpts = LIST_GROUP_OPTIONS.map((opt) => `<option value="${opt.value}"${opt.value === controls.group ? " selected" : ""}>${escapeHtml(opt.label)}</option>`).join("");
  const densityBtns = LIST_DENSITY_LEVELS.map((level) => `<button type="button" class="list-density-btn${level === controls.density ? " is-active" : ""}" data-list-view="${escapeHtml(view)}" data-density="${level}">${escapeHtml(level)}</button>`).join("");
  const savedOpts = [`<option value="">Saved views</option>`]
    .concat(Object.keys(savedViews).map((name) => `<option value="${escapeHtml(name)}">${escapeHtml(name)}</option>`))
    .join("");
  mount.innerHTML = `
    <div class="list-toolbar" role="toolbar" aria-label="List controls">
      <input type="search" class="list-search" data-list-view="${escapeHtml(view)}" placeholder="search" aria-label="Search ${escapeHtml(view)}" value="${escapeHtml(controls.search || "")}">
      ${facetSelectHtml(view, "status", "Status", facets.status, controls.filters.status || "")}
      ${facetSelectHtml(view, "priority", "Priority", facets.priority, controls.filters.priority || "")}
      ${facetSelectHtml(view, "owner", "Owner", facets.owner, controls.filters.owner || "")}
      ${facetSelectHtml(view, "taskset", "Task set", facets.taskset, controls.filters.taskset || "")}
      ${facetSelectHtml(view, "tag", "Tag", facets.tag, controls.filters.tag || "")}
      <label class="list-toolbar-field"><span class="list-toolbar-label">Date</span><input type="text" class="list-filter list-filter-date" data-list-view="${escapeHtml(view)}" data-filter-key="date" placeholder="YYYY-MM-DD" value="${escapeHtml(controls.filters.date || "")}"></label>
      <label class="list-toolbar-field"><span class="list-toolbar-label">Sort</span><select class="list-sort" data-list-view="${escapeHtml(view)}">${sortOpts}</select></label>
      <label class="list-toolbar-field"><span class="list-toolbar-label">Group</span><select class="list-group" data-list-view="${escapeHtml(view)}">${groupOpts}</select></label>
      <div class="list-density" role="group" aria-label="Density"><span class="list-toolbar-label">Density</span>${densityBtns}</div>
      <label class="list-toolbar-field"><span class="list-toolbar-label">Views</span><select class="list-saved-views" data-list-view="${escapeHtml(view)}">${savedOpts}</select></label>
      <button type="button" class="list-save-view" data-list-view="${escapeHtml(view)}">Save view</button>
    </div>`;
  mount.dataset.density = controls.density;
}

// Apply density class onto the actual list container so compact/cozy/detail change row height.
function applyListDensity(view) {
  const controls = loadListControls(view);
  const panel = $(`${view}-list`);
  if (panel) {
    LIST_DENSITY_LEVELS.forEach((level) => panel.classList.remove(`density-${level}`));
    panel.classList.add(`density-${controls.density}`);
  }
}

// Centralised re-render hook so toolbar changes refresh the owning view.
function rerenderListView(view) {
  if (view === "agents") renderAgents();
  else if (view === "messages") renderMessages();
  else if (view === "events") renderEvents();
  else if (view === "evidence") renderEvidence();
}

// Delegated wiring for every list toolbar (search / filters / sort / group / density / saved views).
function wireListToolbars() {
  document.addEventListener("input", (event) => {
    const search = event.target.closest(".list-search");
    if (search) {
      const view = search.dataset.listView;
      loadListControls(view).search = search.value;
      persistListControls(view);
      rerenderListView(view);
      return;
    }
    const dateFilter = event.target.closest(".list-filter-date");
    if (dateFilter) {
      const view = dateFilter.dataset.listView;
      loadListControls(view).filters[dateFilter.dataset.filterKey] = dateFilter.value.trim();
      persistListControls(view);
      rerenderListView(view);
    }
  });
  document.addEventListener("change", (event) => {
    const filter = event.target.closest("select.list-filter");
    if (filter) {
      const view = filter.dataset.listView;
      loadListControls(view).filters[filter.dataset.filterKey] = filter.value;
      persistListControls(view);
      rerenderListView(view);
      return;
    }
    const sort = event.target.closest(".list-sort");
    if (sort) {
      const view = sort.dataset.listView;
      loadListControls(view).sort = sort.value;
      persistListControls(view);
      rerenderListView(view);
      return;
    }
    const group = event.target.closest(".list-group");
    if (group) {
      const view = group.dataset.listView;
      loadListControls(view).group = group.value;
      persistListControls(view);
      rerenderListView(view);
      return;
    }
    const saved = event.target.closest(".list-saved-views");
    if (saved && saved.value) {
      const view = saved.dataset.listView;
      applyNamedView(view, saved.value);
      rerenderListView(view);
    }
  });
  document.addEventListener("click", (event) => {
    const density = event.target.closest(".list-density-btn");
    if (density) {
      const view = density.dataset.listView;
      loadListControls(view).density = density.dataset.density;
      persistListControls(view);
      rerenderListView(view);
      return;
    }
    const save = event.target.closest(".list-save-view");
    if (save) {
      const view = save.dataset.listView;
      const name = window.prompt ? window.prompt("Name this view") : "";
      if (name) {
        saveNamedView(view, name);
        rerenderListView(view);
      }
    }
  });
}

// Render grouped rows with group headers using a per-row template fn.
function renderGroupedList(view, items, rowTemplate, emptyLabel) {
  const panel = $(`${view}-list`);
  if (!panel) return;
  renderListToolbar(view, items);
  const { groups, filtered } = applyListControls(view, items);
  if (!filtered.length) {
    panel.innerHTML = `<div class="empty">${escapeHtml(emptyLabel || "No items")}</div>`;
    applyListDensity(view);
    return;
  }
  panel.innerHTML = groups.map((group) => {
    const rows = group.rows.map((item, index) => rowTemplate(item, index)).join("");
    return `<div class="list-group-block"><div class="list-group-header"><span>${escapeHtml(group.key)}</span><span class="list-group-count">${group.rows.length}</span></div>${rows}</div>`;
  }).join("");
  applyListDensity(view);
}

/* ===== Command palette (Ctrl+K) groundwork ===== */
const COMMAND_PALETTE_VIEWS = [
  "board", "work", "meeting", "tasksets", "tsboard", "team", "agents",
  "messages", "events", "evidence", "planner", "roadmap", "map", "sources", "writes",
];
let commandPaletteIndex = 0;

function commandPaletteCommands() {
  const commands = COMMAND_PALETTE_VIEWS.map((view) => ({
    id: `view:${view}`,
    label: `Go to ${view}`,
    run: () => activateView(view),
  }));
  commands.push({ id: "action:refresh", label: "Refresh state", run: loadState });
  return commands;
}

function activateView(view) {
  const tab = document.querySelector(`.tab[data-view="${view}"]`);
  if (!tab) return;
  document.querySelectorAll(".tab").forEach((item) => item.classList.remove("is-active"));
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("is-active"));
  tab.classList.add("is-active");
  const node = $(`view-${view}`);
  if (node) node.classList.add("is-active");
}

function openCommandPalette() {
  const palette = $("command-palette");
  if (!palette) return;
  palette.hidden = false;
  commandPaletteIndex = 0;
  const input = $("command-palette-input");
  if (input) {
    input.value = "";
    input.focus();
  }
  renderCommandPalette();
}

function closeCommandPalette() {
  const palette = $("command-palette");
  if (palette) palette.hidden = true;
}

function paletteIsOpen() {
  const palette = $("command-palette");
  return Boolean(palette && !palette.hidden);
}

function filteredPaletteCommands() {
  const input = $("command-palette-input");
  const query = (input ? input.value : "").trim().toLowerCase();
  const commands = commandPaletteCommands();
  if (!query) return commands;
  return commands.filter((cmd) => cmd.label.toLowerCase().includes(query) || cmd.id.toLowerCase().includes(query));
}

function renderCommandPalette() {
  const results = $("command-palette-results");
  if (!results) return;
  const commands = filteredPaletteCommands();
  if (commandPaletteIndex >= commands.length) commandPaletteIndex = Math.max(0, commands.length - 1);
  results.innerHTML = commands.length
    ? commands.map((cmd, index) => `<div class="command-palette-item${index === commandPaletteIndex ? " is-active" : ""}" role="option" data-command-id="${escapeHtml(cmd.id)}" data-command-index="${index}">${escapeHtml(cmd.label)}</div>`).join("")
    : `<div class="command-palette-empty">No matching commands</div>`;
}

function runActivePaletteCommand() {
  const commands = filteredPaletteCommands();
  const cmd = commands[commandPaletteIndex];
  if (cmd) {
    closeCommandPalette();
    cmd.run();
  }
}

/* ===== Keyboard navigation (j / k / Enter) over list rows ===== */
function activeListView() {
  const active = document.querySelector(".view.is-active");
  if (!active) return null;
  const view = active.id.replace(/^view-/, "");
  return ["agents", "messages", "events", "evidence"].includes(view) ? view : null;
}

function listRowsFor(view) {
  if (view === "evidence") return Array.from(document.querySelectorAll("#evidence-list .audit-card, #evidence-list .list-row"));
  return Array.from(document.querySelectorAll(`#${view}-list .list-row, #${view}-list .agent-card, #${view}-list .audit-card`));
}

function moveListCursor(view, delta) {
  const rows = listRowsFor(view);
  if (!rows.length) return;
  let index = listCursor[view] ?? -1;
  index = Math.max(0, Math.min(rows.length - 1, index + delta));
  listCursor[view] = index;
  rows.forEach((row) => row.classList.remove("is-cursor"));
  const target = rows[index];
  if (target) {
    target.classList.add("is-cursor");
    target.setAttribute("tabindex", "-1");
    target.focus({ preventScroll: false });
    target.scrollIntoView({ block: "nearest" });
  }
}

function activateListCursor(view) {
  const rows = listRowsFor(view);
  const index = listCursor[view] ?? -1;
  const target = rows[index];
  if (target) target.click();
}

function handleListKeyboardNav(event) {
  if (paletteIsOpen()) return;
  const tag = (event.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return;
  const view = activeListView();
  if (!view) return;
  if (event.key === "j") {
    event.preventDefault();
    moveListCursor(view, 1);
  } else if (event.key === "k") {
    event.preventDefault();
    moveListCursor(view, -1);
  } else if (event.key === "Enter") {
    activateListCursor(view);
  }
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

function renderTasksetCompletion() {
  const host = $("taskset-completion-banner");
  if (!host) return;
  const completion = (runtimeState && runtimeState.taskset_completion) || {};
  if (!completion.active) {
    host.hidden = true;
    host.innerHTML = "";
    return;
  }
  host.hidden = false;
  const next = completion.next_suggestion;
  const suggestionMarkup = next
    ? `
      <div class="taskset-completion-next" data-approval="${escapeHtml(next.approval_state || "awaiting_approval")}">
        <span class="taskset-completion-next-label">Next taskset (awaiting approval)</span>
        <strong>${escapeHtml(next.display_name || next.id || "")}</strong>
        <span class="taskset-completion-next-meta">${escapeHtml(next.tasks_open || 0)}/${escapeHtml(next.tasks_total || 0)} open</span>
        <code class="taskset-completion-next-cmd">${escapeHtml(next.start_command || "")}</code>
      </div>`
    : `<div class="taskset-completion-next"><span class="taskset-completion-next-label">No further taskset queued.</span></div>`;
  host.innerHTML = `
    <div class="taskset-completion-head">
      <span class="taskset-completion-badge">Completed</span>
      <b>${escapeHtml(completion.completed_display_name || completion.completed_task_set_id || "")}</b>
      <span class="state-chip">stop &amp; report</span>
    </div>
    <p class="taskset-completion-message">${escapeHtml(completion.message || "")}</p>
    ${suggestionMarkup}
  `;
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
  return `<div class="task-card ${statusClassName(status)}" role="button" tabindex="0" draggable="true" data-task-id="${escapeHtml(task.id)}" data-task-lane="${escapeHtml(task.lane || "")}" data-task-order="${escapeHtml(Number(task.order || 0))}" data-peek-task="${escapeHtml(task.id)}" aria-label="Task ${escapeHtml(task.id)}: ${escapeHtml(task.title)}">
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
    <div class="task-card-actions" aria-label="Quick actions">
      <button type="button" data-quick-action="claim" data-task-id="${escapeHtml(task.id)}">Claim</button>
      <button type="button" data-quick-action="verify" data-task-id="${escapeHtml(task.id)}">Verify</button>
      <button type="button" data-quick-action="close" data-task-id="${escapeHtml(task.id)}">Close</button>
    </div>
  </div>`;
}

const laneStatusDefault = {
  "Backlog": "planned",
  "Ready": "ready",
  "In Progress": "in_progress",
  "Review": "review",
  "Blocked": "blocked",
  "Done": "completed",
};

function laneStatusFor(lane) {
  return laneStatusDefault[lane] || "planned";
}

function boardAnnounce(message) {
  setText("board-dnd-status", message || "");
}

function taskById(taskId) {
  return (runtimeState.tasks || []).find((task) => task.id === taskId);
}

function buildPeekMarkup(task) {
  if (!task) return "";
  const taskSetInfo = taskSetById(task.task_set_id);
  const taskSet = taskSetInfo
    ? `${taskSetInfo.primary_alias || taskSetInfo.id} - ${taskSetInfo.display_name || taskSetInfo.id}`
    : task.task_set_id || "no task set";
  const summary = task.peek_summary || task.description || task.title || "No summary";
  const rows = [
    ["Status", task.status || "unknown"],
    ["Lane", task.lane || "Backlog"],
    ["Priority", task.priority || "none"],
    ["Owner", task.owner_agent || "unassigned"],
    ["Task set", taskSet],
    ["Evidence", evidenceLabelForTask(task)],
    ["Updated", task.last_updated || task.updated_at || "unknown"],
  ];
  if (task.blocked_reason) rows.push(["Blocked", task.blocked_reason]);
  return `<h3><code>${escapeHtml(task.id)}</code> ${escapeHtml(task.title || "")}</h3>
    <p>${escapeHtml(summary)}</p>
    <dl>${rows.map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}</dl>`;
}

function positionPeek(anchor) {
  const peek = $("board-peek");
  if (!peek || !anchor) return;
  const rect = anchor.getBoundingClientRect();
  const margin = 8;
  peek.style.visibility = "hidden";
  peek.hidden = false;
  const peekRect = peek.getBoundingClientRect();
  let left = rect.right + margin;
  if (left + peekRect.width > window.innerWidth - margin) {
    left = Math.max(margin, rect.left - peekRect.width - margin);
  }
  let top = rect.top;
  if (top + peekRect.height > window.innerHeight - margin) {
    top = Math.max(margin, window.innerHeight - peekRect.height - margin);
  }
  peek.style.left = `${Math.round(left)}px`;
  peek.style.top = `${Math.round(top)}px`;
  peek.style.visibility = "visible";
}

function showPeek(anchor) {
  const peek = $("board-peek");
  if (!peek || !anchor) return;
  const task = taskById(anchor.dataset.peekTask);
  if (!task) return;
  peek.innerHTML = buildPeekMarkup(task);
  peek.hidden = false;
  peek.setAttribute("aria-hidden", "false");
  peekAnchorId = anchor.dataset.peekTask;
  positionPeek(anchor);
}

function hidePeek() {
  const peek = $("board-peek");
  if (!peek) return;
  peek.hidden = true;
  peek.setAttribute("aria-hidden", "true");
  peekAnchorId = null;
  if (peekTimer) {
    window.clearTimeout(peekTimer);
    peekTimer = null;
  }
}

function schedulePeek(anchor) {
  if (peekTimer) window.clearTimeout(peekTimer);
  peekTimer = window.setTimeout(() => showPeek(anchor), 300);
}

async function quickAction(action, taskId) {
  const task = taskById(taskId);
  if (!task) return;
  if (action === "claim") {
    await sendJson(`/api/tasks/${encodeURIComponent(taskId)}`, {
      method: "PATCH",
      type: "task.update",
      payload: { status: "claimed", owner: task.owner_agent || "lead-engineer" }
    });
  } else if (action === "verify") {
    await sendJson("/api/commands", {
      type: "runtime.request_review",
      payload: {
        type: "runtime.request_review",
        target: task.owner_agent || "lead-engineer",
        payload: {
          actor: "owner",
          instruction: `${taskId} verify: run the gate chain and report results.`,
          reason: `${taskId} quick verify`,
          task_id: taskId,
          goal_id: task.task_set_id || ""
        }
      }
    });
  } else if (action === "close") {
    if (!window.confirm(`Close ${taskId}?`)) return;
    await sendJson(`/api/tasks/${encodeURIComponent(taskId)}/archive`, { type: "task.archive", payload: {} });
  }
}

function laneTasksFor(lane) {
  return (runtimeState.tasks || []).filter((task) => task.lane === lane);
}

async function commitTaskMove(taskId, targetLane, targetIndex) {
  const task = taskById(taskId);
  if (!task) return;
  const sameLane = task.lane === targetLane;
  const siblings = laneTasksFor(targetLane).filter((item) => item.id !== taskId);
  const clampedIndex = Math.max(0, Math.min(targetIndex, siblings.length));
  const before = siblings[clampedIndex - 1];
  const order = before ? Number(before.order || 0) + 1 : 0;
  if (sameLane && Number(task.order || 0) === order) {
    boardAnnounce(`${taskId} unchanged.`);
    return;
  }
  const payload = { order };
  if (!sameLane) payload.status = laneStatusFor(targetLane);
  boardAnnounce(`Proposing ${taskId} -> ${targetLane} (position ${clampedIndex + 1}).`);
  await sendJson(`/api/tasks/${encodeURIComponent(taskId)}/reorder`, {
    type: "task.reorder",
    payload
  });
}

function clearDropHighlights() {
  document.querySelectorAll(".lane.is-drop-target").forEach((node) => node.classList.remove("is-drop-target"));
  document.querySelectorAll(".lane-body.is-dragover").forEach((node) => node.classList.remove("is-dragover"));
  document.querySelectorAll(".drop-placeholder").forEach((node) => node.remove());
}

function dropIndexForY(laneBody, clientY) {
  const cards = [...laneBody.querySelectorAll(".task-card")];
  for (let index = 0; index < cards.length; index += 1) {
    const rect = cards[index].getBoundingClientRect();
    if (clientY < rect.top + rect.height / 2) return index;
  }
  return cards.length;
}

function wireBoardCard(card) {
  card.addEventListener("click", (event) => {
    if (event.target.closest("[data-quick-action]")) return;
    selectedTaskId = card.dataset.taskId;
    renderDetail();
  });
  card.addEventListener("keydown", (event) => {
    if (boardLifted) return;
    if (event.key === "Enter" || event.key === " ") {
      if (event.target.closest("[data-quick-action]")) return;
      event.preventDefault();
      selectedTaskId = card.dataset.taskId;
      renderDetail();
    }
  });
  card.addEventListener("mouseenter", () => schedulePeek(card));
  card.addEventListener("mouseleave", hidePeek);
  card.addEventListener("focus", () => showPeek(card));
  card.addEventListener("blur", hidePeek);
  card.addEventListener("dragstart", (event) => {
    boardDragId = card.dataset.taskId;
    card.classList.add("is-dragging");
    hidePeek();
    if (event.dataTransfer) {
      event.dataTransfer.setData("text/plain", card.dataset.taskId);
      event.dataTransfer.effectAllowed = "move";
    }
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("is-dragging");
    boardDragId = null;
    clearDropHighlights();
  });
  card.querySelectorAll("[data-quick-action]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      quickAction(button.dataset.quickAction, button.dataset.taskId);
    });
  });
}

function wireLaneDropTarget(lane) {
  const laneName = lane.dataset.lane;
  const body = lane.querySelector(".lane-body");
  if (!body) return;
  lane.addEventListener("dragover", (event) => {
    if (!boardDragId) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
    lane.classList.add("is-drop-target");
    body.classList.add("is-dragover");
  });
  lane.addEventListener("dragleave", (event) => {
    if (lane.contains(event.relatedTarget)) return;
    lane.classList.remove("is-drop-target");
    body.classList.remove("is-dragover");
  });
  lane.addEventListener("drop", (event) => {
    event.preventDefault();
    const taskId = (event.dataTransfer && event.dataTransfer.getData("text/plain")) || boardDragId;
    const index = dropIndexForY(body, event.clientY);
    clearDropHighlights();
    boardDragId = null;
    if (taskId) commitTaskMove(taskId, laneName, index);
  });
}

function clearLift() {
  if (boardLifted) {
    const node = document.querySelector(`.task-card[data-task-id="${CSS.escape(boardLifted.id)}"]`);
    if (node) node.classList.remove("is-lifted");
  }
  boardLifted = null;
}

function renderLift() {
  document.querySelectorAll(".task-card.is-lifted").forEach((node) => node.classList.remove("is-lifted"));
  if (!boardLifted) return;
  const node = document.querySelector(`.task-card[data-task-id="${CSS.escape(boardLifted.id)}"]`);
  if (node) node.classList.add("is-lifted");
}

function liftDescribe() {
  if (!boardLifted) return "";
  const lane = lanes[boardLifted.laneIndex];
  return `${boardLifted.id} held over ${lane}, position ${boardLifted.index + 1}. Arrows move, Space drops, Esc cancels.`;
}

function handleBoardKeyboardDnd(event) {
  if (event.key === "d" && (event.ctrlKey || event.metaKey)) {
    const card = event.target.closest(".task-card");
    if (!card) return;
    event.preventDefault();
    const task = taskById(card.dataset.taskId);
    if (!task) return;
    const laneIndex = Math.max(0, lanes.indexOf(task.lane));
    const index = laneTasksFor(lanes[laneIndex]).findIndex((item) => item.id === task.id);
    boardLifted = { id: task.id, laneIndex, index: index < 0 ? 0 : index };
    renderLift();
    boardAnnounce(`Lifted ${liftDescribe()}`);
    return;
  }
  if (!boardLifted) return;
  if (event.key === "Escape") {
    event.preventDefault();
    const id = boardLifted.id;
    clearLift();
    boardAnnounce(`Cancelled move for ${id}.`);
    return;
  }
  if (event.key === " " || event.key === "Enter") {
    event.preventDefault();
    const held = boardLifted;
    clearLift();
    commitTaskMove(held.id, lanes[held.laneIndex], held.index);
    return;
  }
  if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
    event.preventDefault();
    const delta = event.key === "ArrowRight" ? 1 : -1;
    boardLifted.laneIndex = Math.max(0, Math.min(lanes.length - 1, boardLifted.laneIndex + delta));
    const count = laneTasksFor(lanes[boardLifted.laneIndex]).filter((item) => item.id !== boardLifted.id).length;
    boardLifted.index = Math.max(0, Math.min(boardLifted.index, count));
    boardAnnounce(liftDescribe());
    return;
  }
  if (event.key === "ArrowUp" || event.key === "ArrowDown") {
    event.preventDefault();
    const delta = event.key === "ArrowDown" ? 1 : -1;
    const count = laneTasksFor(lanes[boardLifted.laneIndex]).filter((item) => item.id !== boardLifted.id).length;
    boardLifted.index = Math.max(0, Math.min(count, boardLifted.index + delta));
    boardAnnounce(liftDescribe());
  }
}

function renderKanban() {
  const tasks = runtimeState.tasks || [];
  if (boardLifted && !taskById(boardLifted.id)) clearLift();
  $("kanban").innerHTML = lanes.map((lane) => {
    const laneTasks = tasks.filter((task) => task.lane === lane);
    const body = laneTasks.length ? laneTasks.map(taskCard).join("") : `<div class="empty">No ${escapeHtml(lane)} tasks</div>`;
    return `<section class="lane ${laneClassName(lane)}" data-lane="${escapeHtml(lane)}"><header class="lane-header"><span class="lane-title">${escapeHtml(lane)}<small>Lane</small></span><span class="lane-count" aria-label="${escapeHtml(lane)} task count">${laneTasks.length}</span></header><div class="lane-body">${body}</div></section>`;
  }).join("");
  document.querySelectorAll("#kanban .task-card").forEach(wireBoardCard);
  document.querySelectorAll("#kanban .lane").forEach(wireLaneDropTarget);
  renderLift();
}

function agentProgressLabel(agent) {
  const pct = numericPct(agent.progress_pct);
  return pct === null ? "~" : `${pct}%`;
}

function agentCardTemplate(agent) {
  return `
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
  `;
}

function renderAgents() {
  renderMultipaneAssurance();
  renderTaskSets();
  const agents = runtimeState.agents || [];
  renderGroupedList("agents", agents, agentCardTemplate, "No active sessions");
}

function messageRowTemplate(message) {
  return `
    <article class="list-row">
      <b>${escapeHtml(message.id)}</b>
      <span>${escapeHtml(message.from)} -> ${escapeHtml(message.to)} / ${escapeHtml(message.status)}</span>
      <p>${escapeHtml(message.body).slice(0, 220)}</p>
      <code>${escapeHtml(message.source_path)}</code>
    </article>
  `;
}

function renderMessages() {
  const messages = runtimeState.messages || [];
  renderGroupedList("messages", messages, messageRowTemplate, "No messages");
}

// ----- Channels view (TASK-AR-327) -----
let activeChannelId = null;

function channelsData() {
  return (runtimeState && runtimeState.channels) || { channels: [], owner_input: {} };
}

function channelRoleColorVar(token) {
  // Role colors map to existing semantic tokens; reference them as var(--token).
  const safe = String(token || "primary").replace(/[^a-z0-9-]/gi, "");
  return `var(--${safe || "primary"})`;
}

function channelMessageTemplate(message) {
  const color = channelRoleColorVar(message.role_color);
  return `
    <div class="channel-message">
      <span class="channel-avatar" style="--role-color: ${color}" aria-hidden="true">${escapeHtml(message.avatar || "?")}</span>
      <div class="channel-message-body">
        <div class="channel-message-head">
          <span class="channel-sender" style="--role-color: ${color}">${escapeHtml(message.from || "unknown")}</span>
          <span class="channel-ts">${escapeHtml(message.ts || "")}</span>
        </div>
        <div class="channel-message-text">${escapeHtml(message.body || "")}</div>
      </div>
    </div>`;
}

function channelThreadTemplate(thread) {
  const messages = (thread.messages || []).map(channelMessageTemplate).join("");
  return `
    <article class="channel-thread" data-thread-id="${escapeHtml(thread.id)}">
      <div class="channel-thread-head">
        <span class="channel-thread-title">${escapeHtml(thread.title || thread.id)}</span>
        ${thread.task_id ? `<span class="channel-thread-task">${escapeHtml(thread.task_id)}</span>` : ""}
      </div>
      ${messages || `<div class="channels-empty">No messages in this thread</div>`}
    </article>`;
}

function renderChannelsList() {
  const host = $("channels-list");
  if (!host) return;
  const channels = channelsData().channels || [];
  if (!channels.length) {
    host.innerHTML = `<div class="channels-empty">No channels</div>`;
    return;
  }
  if (!activeChannelId || !channels.some((channel) => channel.id === activeChannelId)) {
    activeChannelId = channels[0].id;
  }
  host.innerHTML = channels
    .map((channel) => `
      <button type="button" role="tab" class="channel-link${channel.id === activeChannelId ? " is-active" : ""}" data-channel-id="${escapeHtml(channel.id)}" aria-selected="${channel.id === activeChannelId ? "true" : "false"}">
        <span class="channel-name">${escapeHtml(channel.name || ("#" + channel.id))}</span>
        <span class="channel-count">${escapeHtml(Number(channel.message_count || 0))}</span>
      </button>`)
    .join("");
  host.querySelectorAll("[data-channel-id]").forEach((button) => {
    button.addEventListener("click", () => {
      activeChannelId = button.dataset.channelId;
      renderChannels();
    });
  });
}

function renderChannelsMain() {
  const channels = channelsData().channels || [];
  const channel = channels.find((item) => item.id === activeChannelId) || channels[0] || null;
  setText("channels-active-name", channel ? (channel.name || "#" + channel.id) : "#general");
  const meta = $("channels-active-meta");
  if (meta) {
    meta.textContent = channel
      ? `${channel.thread_count || (channel.threads || []).length} thread(s) | ${channel.message_count || 0} message(s)`
      : "";
  }
  const host = $("channels-threads");
  if (!host) return;
  const threads = channel ? (channel.threads || []) : [];
  host.innerHTML = threads.length
    ? threads.map(channelThreadTemplate).join("")
    : `<div class="channels-empty">No conversation yet in this channel</div>`;
}

function renderChannels() {
  renderChannelsList();
  renderChannelsMain();
}

// Parse the owner input box into a runtime command. Slash commands:
//   /meeting <topic> @role @role   -> meeting.start
//   /seminar <topic>               -> seminar.start
// Anything else is a directive (runtime.call_agent) to the @target / channel.
function parseChannelInput(raw, { target, channel } = {}) {
  const text = String(raw || "").trim();
  if (!text) return { error: "Enter a message or slash command." };
  const meetingMatch = text.match(/^\/(meeting|seminar)\b\s*(.*)$/i);
  if (meetingMatch) {
    const kind = meetingMatch[1].toLowerCase();
    const rest = meetingMatch[2].trim();
    const roles = (rest.match(/@[\w.-]+/g) || []).map((token) => token.slice(1));
    const topic = rest.replace(/@[\w.-]+/g, "").trim();
    if (!topic) return { error: `Usage: /${kind} <topic>${kind === "meeting" ? " @role @role" : ""}` };
    if (kind === "meeting" && roles.length < 2) {
      return { error: "A meeting needs at least 2 participants: /meeting <topic> @role @role" };
    }
    return {
      command: {
        type: kind === "seminar" ? "seminar.start" : "meeting.start",
        payload: {
          actor: "owner",
          topic,
          participants: roles,
          channel: channel || null,
          rounds: 3,
        },
      },
    };
  }
  // Plain directive message to an agent / channel.
  const to = String(target || "").replace(/^@/, "").trim();
  if (!to) return { error: "Add a @role target for a directive, or use /meeting or /seminar." };
  return {
    command: {
      type: "runtime.call_agent",
      target: to,
      payload: { actor: "owner", instruction: text, reason: `Owner directive in #${channel || "general"}`, channel: channel || null },
    },
  };
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

function eventCardTemplate(event) {
  return `
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
  `;
}

function renderEvents() {
  // Legacy filter-row narrows first, then the shared list toolbar applies filter/sort/group/density.
  const events = filterEvents(runtimeState.events || []).slice(-80).reverse();
  renderGroupedList("events", events, eventCardTemplate, "No events");
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

// ----- Live map: presence + node/edge graph + activity feed (TASK-AR-326) -----
const SVG_NS = "http://www.w3.org/2000/svg";
const LIVE_MAP_KIND_LABELS = { message: "Message", assignment: "Assignment", review: "Review", block: "Block" };
let livePulseTimers = {};

function liveMapData() {
  return runtimeState.live_map || { nodes: [], edges: [], presence: { counts: {}, online: 0, agents: [] }, totals: {} };
}

function liveMapNodePositions(nodes) {
  // Deterministic radial layout: owner at the apex, everyone else on a ring
  // grouped by kind so the graph reads the same across refreshes.
  const positions = {};
  const cx = 500;
  const cy = 300;
  const owner = nodes.find((node) => node.kind === "owner");
  if (owner) positions[owner.id] = { x: cx, y: 70 };
  const ring = nodes.filter((node) => node.kind !== "owner");
  const radius = 220;
  ring.forEach((node, index) => {
    const angle = (index / Math.max(ring.length, 1)) * Math.PI * 2 - Math.PI / 2;
    positions[node.id] = { x: cx + Math.cos(angle) * radius, y: cy + 40 + Math.sin(angle) * (radius * 0.7) };
  });
  return positions;
}

function renderLiveMap() {
  const svg = $("live-map-graph");
  if (!svg) return;
  const data = liveMapData();
  const presence = data.presence || { counts: {}, online: 0, agents: [] };
  const counts = presence.counts || {};
  const summaryParts = Object.keys(counts).sort().map((key) => `${key} ${counts[key]}`);
  setText("live-map-presence", `${presence.online || 0} online - ${summaryParts.join(" / ") || "no presence"}`);

  const legend = $("live-map-legend");
  if (legend) {
    legend.innerHTML = Object.keys(LIVE_MAP_KIND_LABELS).map((kind) =>
      `<li><span class="legend-swatch legend-${kind}"></span>${escapeHtml(LIVE_MAP_KIND_LABELS[kind])}</li>`
    ).join("");
  }

  const nodes = data.nodes || [];
  const edges = data.edges || [];
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!nodes.length) {
    const note = document.createElementNS(SVG_NS, "text");
    note.setAttribute("x", "500");
    note.setAttribute("y", "210");
    note.setAttribute("class", "live-map-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = "No live map data";
    svg.appendChild(note);
    return;
  }
  const positions = liveMapNodePositions(nodes);

  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", `live-map-edge kind-${edge.kind || "edge"}`);
    line.setAttribute("data-edge-id", edge.id);
    edgeLayer.appendChild(line);
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `live-map-node kind-${node.kind || "node"} presence-${node.presence || "offline"}`);
    group.setAttribute("data-node-id", node.id);
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", node.kind === "owner" ? "26" : "18");
    group.appendChild(circle);
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + 34);
    label.textContent = String(node.label || node.id).slice(0, 18);
    group.appendChild(label);
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
}

function pulseLiveElement(selector) {
  const el = document.querySelector(selector);
  if (!el) return;
  el.classList.add("is-pulsing");
  if (livePulseTimers[selector]) clearTimeout(livePulseTimers[selector]);
  livePulseTimers[selector] = setTimeout(() => {
    el.classList.remove("is-pulsing");
    delete livePulseTimers[selector];
  }, 1400);
}

function pulseLiveEdge(edgeId) {
  if (!edgeId) return;
  pulseLiveElement(`.live-map-edge[data-edge-id="${(window.CSS && CSS.escape) ? CSS.escape(edgeId) : edgeId}"]`);
}

function pulseLiveNode(nodeId) {
  if (!nodeId) return;
  pulseLiveElement(`.live-map-node[data-node-id="${(window.CSS && CSS.escape) ? CSS.escape(nodeId) : nodeId}"]`);
}

function pushActivityToast(kind, title, body) {
  const host = $("activity-feed");
  if (!host) return;
  const toast = document.createElement("div");
  toast.className = `activity-toast kind-${kind || "message"}`;
  toast.innerHTML = `<b>${escapeHtml(title || kind || "event")}</b>${escapeHtml(body || "")}`;
  host.appendChild(toast);
  while (host.children.length > 4) host.removeChild(host.firstChild);
  setTimeout(() => {
    toast.classList.add("is-leaving");
    setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 420);
  }, 4200);
}

function presenceMapFor(state) {
  const map = {};
  const lm = (state && state.live_map) || {};
  const presence = lm.presence || {};
  (presence.agents || []).forEach((agent) => { map[agent.role] = agent.presence; });
  return map;
}

function reconcileLiveMap(previous, next) {
  if (!next || !next.live_map) return;
  // New edges since the last snapshot -> pulse them and toast the activity.
  const prevEdges = new Set((((previous || {}).live_map || {}).edges || []).map((edge) => edge.id));
  (next.live_map.edges || []).forEach((edge) => {
    if (!prevEdges.has(edge.id)) {
      pulseLiveEdge(edge.id);
      pulseLiveNode(edge.from);
      pulseLiveNode(edge.to);
      pushActivityToast(edge.kind, LIVE_MAP_KIND_LABELS[edge.kind] || edge.kind, `${edge.from} -> ${edge.to}`);
    }
  });
  // Presence transitions -> pulse the agent node and toast the new state.
  const before = presenceMapFor(previous);
  const after = presenceMapFor(next);
  Object.keys(after).forEach((role) => {
    if (before[role] !== undefined && before[role] !== after[role]) {
      pulseLiveNode(role);
      pushActivityToast("review", "Presence", `${role}: ${before[role]} -> ${after[role]}`);
    }
  });
}

function renderMap() {
  renderLiveMap();
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

function teamAgentsData() {
  return (runtimeState && runtimeState.team_agents) || { teams: [], totals: {} };
}

function teamAgentSearchText(card) {
  return [card.id, card.role, card.callsign, card.display_name, card.model, (card.current_claim || {}).task_id]
    .join(" ").toLowerCase();
}

function agentLevelBar(card) {
  const pct = numericPct(card.xp_pct) ?? 0;
  return `<div class="agent-character-level"><span>Lv <strong>${escapeHtml(card.level ?? 1)}</strong></span><span>${escapeHtml(card.xp ?? 0)} XP (${escapeHtml(card.xp_for_next ?? 0)} to next)</span></div>
    <div class="progress-track" role="img" aria-label="XP ${escapeHtml(pct)}%"><div class="progress-fill" style="width: ${pct}%"></div></div>`;
}

function agentRecentActivity(card) {
  const recent = card.recent_activity || [];
  if (!recent.length) return "";
  return `<ul class="agent-character-activity">${recent.map((item) =>
    `<li>${escapeHtml(item.event || "activity")} <small>${escapeHtml(item.ts || "")}</small></li>`
  ).join("")}</ul>`;
}

function agentCharacterCard(card) {
  const claim = card.current_claim || {};
  const presence = String(card.presence || "offline");
  const currentTask = claim.task_id
    ? `<code>${escapeHtml(claim.task_id)}</code> ${escapeHtml(claim.phase || claim.status || "")}`
    : "idle - no claim";
  return `
    <article class="agent-character-card presence-${escapeHtml(presence)}" data-agent-id="${escapeHtml(card.id)}">
      <header class="agent-character-header">
        <span class="agent-character-avatar">${escapeHtml(card.avatar || "AG")}<span class="presence-ring" title="${escapeHtml(presence)}"></span></span>
        <div class="agent-character-identity">
          <b>${escapeHtml(card.callsign || card.id)}</b>
          <span>${escapeHtml(card.role || "unknown")} - ${escapeHtml(presence)}</span>
        </div>
      </header>
      ${agentLevelBar(card)}
      <div class="agent-character-meta">
        <span><span class="meta-label">Model</span><strong>${escapeHtml(card.model || "default")}</strong></span>
        <span><span class="meta-label">Skills</span><strong>${escapeHtml(card.skill_count ?? 0)}</strong></span>
        <span><span class="meta-label">Tasks done</span><strong>${escapeHtml((card.lifetime || {}).completed_tasks ?? 0)}</strong></span>
        <span><span class="meta-label">Units done</span><strong>${escapeHtml((card.lifetime || {}).completed_units ?? 0)}</strong></span>
      </div>
      <p class="agent-character-task"><span class="meta-label">Current</span> ${currentTask}</p>
      ${agentRecentActivity(card)}
    </article>
  `;
}

function teamGroupBlock(group) {
  const roles = group.role_distribution || {};
  const badges = Object.keys(roles).map((role) =>
    `<span class="team-role-badge">${escapeHtml(role)} ${escapeHtml(roles[role])}</span>`
  ).join("");
  let agents = group.agents || [];
  const query = $("team-filter")?.value.trim().toLowerCase() || "";
  if (teamOnlineOnly) agents = agents.filter((card) => card.online);
  if (query) agents = agents.filter((card) => teamAgentSearchText(card).includes(query));
  const cards = agents.length ? agents.map(agentCharacterCard).join("") : `<div class="empty">No agents</div>`;
  return `
    <section class="team-group" data-team-id="${escapeHtml(group.id)}">
      <header class="team-group-header">
        <b>${escapeHtml(group.team_id || group.id)}</b>
        <span>${escapeHtml(group.online_count ?? 0)} online / ${escapeHtml(group.agent_count ?? 0)} agents</span>
      </header>
      <div class="team-role-badges">${badges}</div>
      <div class="team-cards">${cards}</div>
    </section>
  `;
}

function renderTeamAgents() {
  const host = $("team-org");
  if (!host) return;
  const data = teamAgentsData();
  const totals = data.totals || {};
  setText("team-summary", `${totals.teams ?? 0} teams - ${totals.agents ?? 0} agents - ${totals.online ?? 0} online`);
  const teams = data.teams || [];
  host.innerHTML = teams.length ? teams.map(teamGroupBlock).join("") : `<div class="empty">No teams</div>`;
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
  renderTasksetCompletion();
  renderTasksetBoard();
  renderTeamAgents();
  renderAgents();
  renderChannels();
  renderMessages();
  renderEvents();
  renderEvidence();
  renderPlanning();
  renderRoadmapTimeline();
  renderMap();
  renderSources();
  renderCommands();
  renderSidebarActiveTaskset();
  renderDetail();
}

// ----- Sidebar navigation + URL hash routing -----
function navLinks() {
  return Array.from(document.querySelectorAll(".sidebar-link"));
}

function viewForRoute(route) {
  const link = navLinks().find((item) => item.dataset.route === route);
  return link ? link.dataset.view : null;
}

function routeForView(view) {
  const link = navLinks().find((item) => item.dataset.view === view);
  return link ? link.dataset.route : null;
}

function activateView(view, { updateHash = true } = {}) {
  const target = $(`view-${view}`);
  if (!target) return;
  navLinks().forEach((item) => {
    const isActive = item.dataset.view === view;
    item.classList.toggle("is-active", isActive);
    item.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("is-active"));
  target.classList.add("is-active");
  if (updateHash) {
    const route = routeForView(view);
    if (route) {
      const desired = `#/${route}`;
      if (window.location.hash !== desired) window.location.hash = desired;
    }
  }
  closeMobileSidebar();
}

function routeFromHash() {
  const raw = (window.location.hash || "").replace(/^#\/?/, "");
  if (!raw) return null;
  return viewForRoute(raw) ? raw : null;
}

function applyHashRoute() {
  const route = routeFromHash();
  const view = route ? viewForRoute(route) : "board";
  activateView(view || "board", { updateHash: false });
}

function setSidebarCollapsed(collapsed) {
  const sidebar = $("primary-sidebar");
  const shell = $("runtime-console-app");
  if (sidebar) sidebar.dataset.collapsed = collapsed ? "true" : "false";
  if (shell) shell.dataset.sidebarCollapsed = collapsed ? "true" : "false";
  const collapseBtn = $("sidebar-collapse");
  if (collapseBtn) collapseBtn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  try { window.localStorage.setItem("ar-sidebar-collapsed", collapsed ? "1" : "0"); } catch (error) {}
}

function openMobileSidebar() {
  const sidebar = $("primary-sidebar");
  const scrim = $("sidebar-scrim");
  if (sidebar) sidebar.classList.add("is-open");
  if (scrim) scrim.hidden = false;
  const toggle = $("sidebar-toggle");
  if (toggle) toggle.setAttribute("aria-expanded", "true");
}

function closeMobileSidebar() {
  const sidebar = $("primary-sidebar");
  const scrim = $("sidebar-scrim");
  if (sidebar) sidebar.classList.remove("is-open");
  if (scrim) scrim.hidden = true;
  const toggle = $("sidebar-toggle");
  if (toggle) toggle.setAttribute("aria-expanded", "false");
}

function renderSidebarActiveTaskset() {
  const box = $("sidebar-active-taskset");
  const empty = $("sidebar-active-empty");
  if (!box || !empty) return;
  const taskSets = runtimeState.task_sets || [];
  const active = taskSets.find((set) => set.active) || taskSets.find((set) => set.status === "active") || null;
  if (!active) {
    box.hidden = true;
    empty.hidden = false;
    return;
  }
  box.hidden = false;
  empty.hidden = true;
  setText("sidebar-active-name", active.display_name || active.primary_alias || active.id);
  const progress = $("sidebar-active-progress");
  if (progress) progress.innerHTML = progressBar(active.progress_pct);
  setText("sidebar-active-meta", `${active.tasks_done || 0}/${active.tasks_total || 0} done`);
}

navLinks().forEach((link) => {
  link.addEventListener("click", () => activateView(link.dataset.view));
});

window.addEventListener("hashchange", applyHashRoute);

$("sidebar-collapse")?.addEventListener("click", () => {
  const sidebar = $("primary-sidebar");
  const collapsed = sidebar ? sidebar.dataset.collapsed === "true" : false;
  setSidebarCollapsed(!collapsed);
});
$("sidebar-toggle")?.addEventListener("click", () => {
  const sidebar = $("primary-sidebar");
  if (sidebar && sidebar.classList.contains("is-open")) closeMobileSidebar();
  else openMobileSidebar();
});
$("sidebar-scrim")?.addEventListener("click", closeMobileSidebar);

(() => {
  let collapsed = false;
  try { collapsed = window.localStorage.getItem("ar-sidebar-collapsed") === "1"; } catch (error) {}
  setSidebarCollapsed(collapsed);
  applyHashRoute();
})();

function boardViewActive() {
  const view = $("view-board");
  return Boolean(view && view.classList.contains("is-active"));
}

document.addEventListener("keydown", (event) => {
  // Command palette toggle (Ctrl+K / Cmd+K).
  if ((event.ctrlKey || event.metaKey) && (event.key === "k" || event.key === "K")) {
    event.preventDefault();
    if (paletteIsOpen()) closeCommandPalette();
    else openCommandPalette();
    return;
  }
  if (paletteIsOpen()) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeCommandPalette();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      commandPaletteIndex += 1;
      renderCommandPalette();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      commandPaletteIndex = Math.max(0, commandPaletteIndex - 1);
      renderCommandPalette();
    } else if (event.key === "Enter") {
      event.preventDefault();
      runActivePaletteCommand();
    }
    return;
  }
  if (event.key === "Escape" && peekAnchorId) {
    hidePeek();
    return;
  }
  // j / k / Enter list-row navigation on list views.
  handleListKeyboardNav(event);
  if (!boardViewActive()) return;
  handleBoardKeyboardDnd(event);
});
document.addEventListener("scroll", hidePeek, true);

// Command palette interaction wiring.
wireListToolbars();
(() => {
  const palette = $("command-palette");
  if (!palette) return;
  const input = $("command-palette-input");
  if (input) input.addEventListener("input", () => { commandPaletteIndex = 0; renderCommandPalette(); });
  palette.addEventListener("click", (event) => {
    if (event.target.dataset.commandDismiss) {
      closeCommandPalette();
      return;
    }
    const item = event.target.closest(".command-palette-item");
    if (item) {
      commandPaletteIndex = Number(item.dataset.commandIndex) || 0;
      runActivePaletteCommand();
    }
  });
})();

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
$("team-filter")?.addEventListener("input", renderTeamAgents);
$("team-online-toggle")?.addEventListener("change", (event) => {
  teamOnlineOnly = Boolean(event.target.checked);
  renderTeamAgents();
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
$("channels-input-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const hint = $("channels-input-hint");
  const parsed = parseChannelInput($("channels-input-box").value, {
    target: $("channels-input-target").value,
    channel: activeChannelId || "general",
  });
  if (parsed.error) {
    if (hint) {
      hint.textContent = parsed.error;
      hint.classList.add("is-error");
      hint.classList.remove("is-ok");
    }
    return;
  }
  // sendJson transmits options.payload as the HTTP body; the body must be the
  // full command {type,target,payload} so the server's submit_command sees a
  // top-level type. Match the convention used by every other /api/commands call.
  const result = await sendJson("/api/commands", { type: parsed.command.type, payload: parsed.command });
  if (hint) {
    const ok = result && result.status !== "failed";
    hint.textContent = ok
      ? `Submitted ${parsed.command.type} (${result.status}).`
      : `Failed: ${(result.errors || ["unknown error"]).join("; ")}`;
    hint.classList.toggle("is-ok", ok);
    hint.classList.toggle("is-error", !ok);
  }
  if (result && result.status !== "failed") {
    $("channels-input-box").value = "";
  }
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
        "/api/taskset_completion": "taskset_completion",
        "/api/taskset-completion": "taskset_completion",
        "/api/team_agents": "team_agents",
        "/api/team-agents": "team_agents",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/replay": "replay",
        "/api/graph": "graph",
        "/api/live_map": "live_map",
        "/api/live-map": "live_map",
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
