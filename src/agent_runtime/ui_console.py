from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs
from urllib.parse import urlparse

from . import ui_commands
from . import ui_export
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
      <div class="topbar-search">
        <input id="global-search-input" class="global-search-input" type="search" autocomplete="off"
               placeholder="Search tasks, tasksets, messages, events&hellip; (Ctrl+P)"
               aria-label="Global search" aria-expanded="false" aria-controls="global-search-results" role="combobox">
        <div id="global-search-results" class="global-search-results" role="listbox" aria-label="Search results" hidden></div>
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
          <button class="sidebar-link" type="button" role="tab" data-view="triage" data-route="work/triage" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9873;</span><span class="sidebar-label">Triage</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="roadmap" data-route="work/roadmap" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Roadmap</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="timeline" data-route="work/timeline" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Timeline</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="calendar" data-route="work/calendar" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Calendar</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="deps" data-route="work/dependencies" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Dependencies</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="agents">
          <span class="sidebar-group-title">AGENTS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="team" data-route="agents/team" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9733;</span><span class="sidebar-label">Team</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="workload" data-route="agents/workload" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9638;</span><span class="sidebar-label">Workload</span>
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
          <button class="sidebar-link" type="button" role="tab" data-view="statemachines" data-route="records/state-machines" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">State Machines</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="sources" data-route="records/sources" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Sources</span>
          </button>
        </div>
        <div class="sidebar-group" data-group="ops">
          <span class="sidebar-group-title">OPS</span>
          <button class="sidebar-link" type="button" role="tab" data-view="dashboard" data-route="ops/dashboard" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9683;</span><span class="sidebar-label">Dashboard</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="automation" data-route="ops/automation" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9889;</span><span class="sidebar-label">Automation</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="properties" data-route="ops/properties" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9636;</span><span class="sidebar-label">Properties</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="labels" data-route="ops/labels" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9750;</span><span class="sidebar-label">Labels</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="portability" data-route="ops/portability" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#8645;</span><span class="sidebar-label">Import/Export</span>
          </button>
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
          <div id="board-team-filter" class="board-team-filter" role="status" hidden></div>
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
          <form id="taskset-create-form" class="taskset-create" aria-label="Create taskset">
            <input id="taskset-new-name" name="display_name" placeholder="New taskset name" required>
            <input id="taskset-new-summary" name="summary" placeholder="Summary (optional)">
            <button type="submit">Create taskset</button>
            <span class="taskset-template-label">Templates:</span>
            <div id="taskset-template-buttons" class="taskset-template-buttons" aria-label="Taskset templates"></div>
          </form>
          <div id="taskset-bulk-bar" class="taskset-bulk-bar" role="toolbar" aria-label="Bulk edit selected tasks" hidden>
            <span id="taskset-bulk-count" class="taskset-bulk-count">0 selected</span>
            <select id="taskset-bulk-status" aria-label="Bulk status">
              <option value="">Set status…</option>
              <option value="planned">planned</option>
              <option value="in_progress">in_progress</option>
              <option value="review">review</option>
              <option value="blocked">blocked</option>
              <option value="completed">completed</option>
            </select>
            <select id="taskset-bulk-priority" aria-label="Bulk priority">
              <option value="">Set priority…</option>
              <option value="P0">P0</option>
              <option value="P1">P1</option>
              <option value="P2">P2</option>
              <option value="P3">P3</option>
            </select>
            <input id="taskset-bulk-owner" placeholder="Set owner…" aria-label="Bulk owner">
            <select id="taskset-bulk-move" aria-label="Move selected tasks to taskset">
              <option value="">Move to taskset…</option>
            </select>
            <button id="taskset-bulk-apply" type="button">Apply</button>
            <button id="taskset-bulk-clear" type="button" class="ghost">Clear</button>
          </div>
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
        <div id="view-workload" class="view">
          <section class="workload" aria-label="Workload heatmap">
            <header class="workload-header">
              <h2>Workload Heatmap</h2>
              <p id="workload-summary" class="workload-summary" role="status"></p>
            </header>
            <div class="workload-toolbar">
              <div class="workload-scope" role="tablist" aria-label="Heatmap scope">
                <button id="workload-scope-agents" class="workload-scope-btn is-active" type="button" role="tab" aria-selected="true">By agent</button>
                <button id="workload-scope-teams" class="workload-scope-btn" type="button" role="tab" aria-selected="false">By team</button>
              </div>
              <ul id="workload-legend" class="workload-legend" aria-label="Load bands"></ul>
            </div>
            <div id="workload-grid" class="workload-grid" aria-label="Workload by period"></div>
          </section>
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
        <div id="view-timeline" class="view">
          <section class="timeline" aria-label="Task timeline">
            <header class="timeline-header">
              <h2>Timeline</h2>
              <p id="timeline-summary" class="timeline-summary" role="status"></p>
            </header>
            <p id="timeline-cycle-warning" class="dep-cycle-warning" role="alert" hidden></p>
            <div id="timeline-grid" class="timeline-grid" aria-label="Taskset bars by lane"></div>
          </section>
        </div>
        <div id="view-calendar" class="view">
          <section class="calendar" aria-label="Calendar and scheduling">
            <header class="calendar-header">
              <h2>Calendar</h2>
              <div class="calendar-nav" role="group" aria-label="Calendar navigation">
                <button id="calendar-prev" class="calendar-nav-btn" type="button" aria-label="Previous period">&#8592;</button>
                <span id="calendar-period" class="calendar-period" role="status" aria-live="polite"></span>
                <button id="calendar-next" class="calendar-nav-btn" type="button" aria-label="Next period">&#8594;</button>
                <button id="calendar-today" class="calendar-nav-btn" type="button">Today</button>
                <span class="calendar-view-toggle" role="group" aria-label="Calendar view mode">
                  <button id="calendar-view-month" class="calendar-mode is-active" type="button" aria-pressed="true">Month</button>
                  <button id="calendar-view-week" class="calendar-mode" type="button" aria-pressed="false">Week</button>
                </span>
              </div>
            </header>
            <p id="calendar-summary" class="calendar-summary" role="status" aria-live="polite"></p>
            <div id="calendar-reminders" class="calendar-reminders" aria-label="Due-soon and overdue reminders"></div>
            <ul class="calendar-legend" aria-label="Calendar legend">
              <li><span class="calendar-dot calendar-dot-milestone" aria-hidden="true"></span>Milestone</li>
              <li><span class="calendar-dot calendar-dot-meeting" aria-hidden="true"></span>Meeting/Seminar</li>
              <li><span class="calendar-dot calendar-dot-completion" aria-hidden="true"></span>Completion</li>
              <li><span class="calendar-dot calendar-dot-deadline" aria-hidden="true"></span>Deadline</li>
              <li><span class="calendar-dot calendar-dot-scheduled" aria-hidden="true"></span>Scheduled dispatch</li>
            </ul>
            <div id="calendar-grid" class="calendar-grid" role="grid" aria-label="Calendar grid"></div>
            <section class="calendar-schedule-panel" aria-label="Scheduled dispatches">
              <h3>Scheduled dispatches</h3>
              <p class="calendar-hint">Reserve a one-time or repeating (cron-like) taskset dispatch. This records a proposal only &mdash; a local scheduler dispatches when due. The console never runs the dispatcher.</p>
              <form id="schedule-form" class="config-form" aria-label="Reserve a scheduled dispatch">
                <input id="schedule-name" name="name" placeholder="Schedule name" required>
                <input id="schedule-taskset" name="taskset_id" placeholder="taskset id (e.g. TASKSET-AR-...)" required>
                <select id="schedule-mode" name="mode" aria-label="Schedule mode">
                  <option value="reserve">Reserve (once)</option>
                  <option value="repeat">Repeat (cron)</option>
                </select>
                <input id="schedule-runat" name="run_at" placeholder="run at (YYYY-MM-DDTHH:MM)">
                <input id="schedule-cron" name="cron" placeholder="cron: min hour dom mon dow (e.g. 0 9 * * 1)" hidden>
                <button type="submit">Reserve</button>
              </form>
              <p id="schedule-summary" class="config-summary" role="status" aria-live="polite"></p>
              <div id="schedule-list" class="config-grid" aria-label="Scheduled dispatches"></div>
            </section>
          </section>
        </div>
        <div id="view-deps" class="view">
          <section class="dep-graph" aria-label="Dependency graph">
            <header class="dep-graph-header">
              <h2>Dependencies</h2>
              <p id="dep-graph-summary" class="dep-graph-summary" role="status"></p>
            </header>
            <p id="dep-cycle-warning" class="dep-cycle-warning" role="alert" hidden></p>
            <div class="dep-graph-stage">
              <svg id="dep-graph-svg" class="dep-graph-svg" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Task dependency graph"></svg>
            </div>
            <ul id="dep-graph-legend" class="dep-graph-legend" aria-label="Dependency legend"></ul>
          </section>
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
        <div id="view-statemachines" class="view">
          <section class="state-machine-viewer" aria-label="State machine viewer">
            <header class="state-machine-header">
              <h2>State Machines</h2>
              <p class="state-machine-hint">Read-only lifecycle viewer. The YAML at <code>agents/project/STATE-MACHINES.yml</code> is the source of truth. Pick a machine to render its states and transitions; pick a task to highlight its current state and the path it has traversed (from the event log).</p>
              <div class="state-machine-toolbar">
                <label class="state-machine-field">
                  <span class="state-machine-field-label">Machine</span>
                  <select id="state-machine-select" aria-label="State machine"></select>
                </label>
                <label class="state-machine-field" id="state-machine-task-field" hidden>
                  <span class="state-machine-field-label">Highlight task</span>
                  <select id="state-machine-task-select" aria-label="Highlight task in state machine"></select>
                </label>
              </div>
              <p id="state-machine-summary" class="state-machine-summary" role="status" aria-live="polite"></p>
            </header>
            <div class="state-machine-stage">
              <svg id="state-machine-svg" class="state-machine-svg" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" role="img" aria-label="State machine graph"></svg>
            </div>
            <ul id="state-machine-legend" class="state-machine-legend" aria-label="State machine legend"></ul>
          </section>
        </div>
        <div id="view-sources" class="view">
          <div id="sources-list" class="list-panel"></div>
        </div>
        <div id="view-writes" class="view">
          <div id="command-log" class="list-panel"></div>
        </div>
        <div id="view-triage" class="view">
          <p id="triage-summary" class="triage-summary" role="status" aria-live="polite"></p>
          <div class="triage-toolbar">
            <input id="triage-filter" placeholder="task id, title, owner">
            <select id="triage-reason-filter" aria-label="Triage reason">
              <option value="">All reasons</option>
              <option value="unclassified">Unclassified</option>
              <option value="overdue">Overdue</option>
              <option value="long_blocked">Long blocked</option>
            </select>
          </div>
          <div id="triage-list" class="list-panel" aria-label="Triage queue"></div>
        </div>
        <div id="view-automation" class="view">
          <form id="automation-form" class="config-form" aria-label="Create automation rule">
            <input id="automation-name" name="name" placeholder="Rule name" required>
            <select id="automation-trigger" name="trigger" aria-label="Trigger">
              <option value="status_change">When status changes</option>
              <option value="due_passed">When due passes</option>
              <option value="blocked_too_long">When blocked too long</option>
            </select>
            <span class="config-form-arrow" aria-hidden="true">&#8594;</span>
            <select id="automation-action" name="action" aria-label="Action">
              <option value="board_regen">Regenerate board</option>
              <option value="escalation_message">Send escalation</option>
              <option value="label_apply">Apply label</option>
            </select>
            <input id="automation-param" name="param" placeholder="param (status / label / days)">
            <button type="submit">Create rule</button>
          </form>
          <p id="automation-summary" class="config-summary" role="status" aria-live="polite"></p>
          <div id="automation-list" class="config-grid" aria-label="Automation rules"></div>
        </div>
        <div id="view-properties" class="view">
          <form id="property-form" class="config-form" aria-label="Create custom property">
            <input id="property-key" name="key" placeholder="property key (e.g. severity)" required>
            <input id="property-label" name="label" placeholder="display label">
            <select id="property-type" name="type" aria-label="Property type">
              <option value="text">text</option>
              <option value="select">select</option>
              <option value="number">number</option>
              <option value="date">date</option>
            </select>
            <input id="property-options" name="options" placeholder="select options (comma separated)">
            <button type="submit">Create property</button>
          </form>
          <p id="property-summary" class="config-summary" role="status" aria-live="polite"></p>
          <div id="property-list" class="config-grid" aria-label="Custom properties"></div>
        </div>
        <div id="view-labels" class="view">
          <form id="label-form" class="config-form" aria-label="Create label">
            <input id="label-name" name="name" placeholder="label name" required>
            <select id="label-color" name="color" aria-label="Label color"></select>
            <input id="label-description" name="description" placeholder="description (optional)">
            <button type="submit">Create label</button>
          </form>
          <p id="label-summary" class="config-summary" role="status" aria-live="polite"></p>
          <div id="label-list" class="config-grid" aria-label="Labels"></div>
        </div>
        <div id="view-portability" class="view">
          <section class="portability-section" aria-label="Export">
            <h2>Export</h2>
            <p class="portability-hint">Download the current state in a portable format. Export is read-only.</p>
            <div class="portability-actions">
              <a class="portability-btn" href="/api/export/board.csv" download="board.csv">Board &rarr; CSV</a>
              <a class="portability-btn" href="/api/export/taskset.md" download="taskset.md">Taskset &rarr; Markdown</a>
              <a class="portability-btn" href="/api/export/status.json" download="status.json">Status &rarr; JSON</a>
              <a class="portability-btn" href="/api/export/backup.zip" download="agent-runtime-backup.zip">Full backup &rarr; ZIP</a>
            </div>
          </section>
          <section class="portability-section" aria-label="Import">
            <h2>Import</h2>
            <p class="portability-hint">Paste a CSV (exported board) or a Markdown checklist. Preview detects duplicates; nothing is created until you commit. Import creates <code>task.create</code> proposals only.</p>
            <form id="import-form" class="portability-import" aria-label="Import tasks">
              <label class="portability-field">
                <span>Format</span>
                <select id="import-format" name="format" aria-label="Import format">
                  <option value="csv">CSV</option>
                  <option value="md">Markdown checklist</option>
                </select>
              </label>
              <textarea id="import-content" name="content" rows="8" placeholder="Paste CSV or Markdown checklist here" aria-label="Import content"></textarea>
              <div class="portability-actions">
                <button id="import-preview-btn" type="submit">Preview</button>
                <button id="import-commit-btn" type="button" disabled>Commit selected</button>
              </div>
            </form>
            <p id="import-summary" class="portability-summary" role="status" aria-live="polite"></p>
            <div id="import-preview" class="portability-preview" aria-label="Import preview"></div>
          </section>
        </div>
        <div id="view-dashboard" class="view">
          <section class="opsdash" aria-label="Operations dashboard">
            <header class="opsdash-header">
              <h2>Ops Dashboard</h2>
              <p id="opsdash-summary" class="opsdash-summary" role="status"></p>
            </header>
            <div class="opsdash-grid">
              <article class="opsdash-card" aria-label="Token and cost trend">
                <header class="opsdash-card-head">
                  <h3>Token &amp; Cost</h3>
                  <span id="opsdash-tokens-meta" class="opsdash-card-meta"></span>
                </header>
                <div id="opsdash-tokens" class="opsdash-tokens"></div>
                <a id="opsdash-tokens-src" class="opsdash-src" href="#" hidden>source</a>
              </article>
              <article class="opsdash-card" aria-label="Eval score trend">
                <header class="opsdash-card-head">
                  <h3>Eval Scores</h3>
                  <span id="opsdash-eval-meta" class="opsdash-card-meta"></span>
                </header>
                <div id="opsdash-eval" class="opsdash-eval"></div>
              </article>
              <article class="opsdash-card" aria-label="Gate status board">
                <header class="opsdash-card-head">
                  <h3>Gate Board</h3>
                  <span id="opsdash-gates-meta" class="opsdash-card-meta"></span>
                </header>
                <div id="opsdash-gates" class="opsdash-gates"></div>
              </article>
              <article class="opsdash-card" aria-label="Taskset burndown and velocity">
                <header class="opsdash-card-head">
                  <h3>Burndown &amp; Velocity</h3>
                  <span id="opsdash-burndown-meta" class="opsdash-card-meta"></span>
                </header>
                <div id="opsdash-burndown" class="opsdash-burndown"></div>
                <div id="opsdash-velocity" class="opsdash-velocity"></div>
              </article>
            </div>
          </section>
        </div>
      </section>

      <aside id="detail-panel" class="detail-panel" aria-label="Task detail">
        <div class="detail-empty">No task selected</div>
      </aside>
    </main>
  </div>
  <div id="undo-toast-region" class="undo-toast-region" role="region" aria-live="assertive" aria-label="Undo"></div>
  <div id="command-palette" class="command-palette" role="dialog" aria-modal="true" aria-label="Command palette" hidden>
    <div class="command-palette-backdrop" data-command-dismiss="1"></div>
    <div class="command-palette-panel" role="document">
      <input id="command-palette-input" class="command-palette-input" type="text" placeholder="Type a command or view (Ctrl+K)" aria-label="Command palette search" autocomplete="off">
      <div id="command-palette-results" class="command-palette-results" role="listbox" aria-label="Command palette results"></div>
    </div>
  </div>
  <div id="quick-open" class="quick-open" role="dialog" aria-modal="true" aria-label="Quick open" hidden>
    <div class="quick-open-backdrop" data-quickopen-dismiss="1"></div>
    <div class="quick-open-panel" role="document">
      <input id="quick-open-input" class="quick-open-input" type="text" placeholder="Quick open entities &mdash; type:task status:blocked (Ctrl+P)" aria-label="Quick open search" autocomplete="off" role="combobox" aria-expanded="true" aria-controls="quick-open-results">
      <div id="quick-open-results" class="quick-open-results" role="listbox" aria-label="Quick open results"></div>
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
  /* State machine viewer highlights (TASK-AR-336) */
  --sm-current: var(--primary);
  --sm-path: var(--violet);
  /* Workload heatmap (TASK-AR-337). Cell intensity is opacity over --heat-base;
     bands map to existing semantic tokens so no per-cell raw color is needed. */
  --heat-base: var(--primary);
  --heat-idle: var(--line);
  --heat-normal: var(--primary);
  --heat-busy: var(--warning);
  --heat-overload: var(--danger);
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
  /* State machine viewer highlights (TASK-AR-336) */
  --sm-current: var(--primary-hover);
  --sm-path: var(--violet);
  /* Workload heatmap (TASK-AR-337) */
  --heat-base: var(--primary-hover);
  --heat-idle: var(--line-strong);
  --heat-normal: var(--primary-hover);
  --heat-busy: var(--warning);
  --heat-overload: var(--danger);
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
.board-team-filter {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  padding: 6px 12px;
  border: 1px solid var(--primary-line);
  background: var(--primary-soft);
  border-radius: 999px;
  font-size: 13px;
  width: fit-content;
}
.board-team-filter button {
  background: transparent;
  border: 0;
  color: var(--primary-hover);
  font-weight: 600;
  cursor: pointer;
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
.taskset-create {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--tile);
}
.taskset-create input {
  min-width: 160px;
  flex: 1 1 160px;
}
.taskset-create button[type="submit"] {
  background: var(--primary);
  color: var(--on-accent);
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  padding: 6px 12px;
  cursor: pointer;
}
.taskset-template-label {
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.taskset-template-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.taskset-template-btn {
  font-size: 12px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--raise);
  color: var(--ink);
  padding: 5px 10px;
  cursor: pointer;
}
.taskset-template-btn:hover {
  border-color: var(--primary);
  color: var(--primary);
}
.taskset-bulk-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  padding: 8px 10px;
  border: 1px solid var(--primary-line);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius);
  background: var(--primary-soft);
}
.taskset-bulk-count {
  font-weight: 600;
  font-size: 12px;
  color: var(--ink);
}
.taskset-bulk-bar select,
.taskset-bulk-bar input {
  font-size: 12px;
}
.taskset-bulk-bar button {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--primary);
  color: var(--on-accent);
  padding: 5px 10px;
  cursor: pointer;
}
.taskset-bulk-bar button.ghost {
  background: var(--raise);
  color: var(--muted);
  border-color: var(--border);
}
.taskset-task-select {
  margin-right: 6px;
}
.taskset-card-tasks {
  display: grid;
  gap: 4px;
  margin-top: 6px;
  border-top: 1px solid var(--line);
  padding-top: 6px;
}
.taskset-task-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--ink);
}
.taskset-task-row.is-selected {
  background: var(--primary-soft);
  border-radius: var(--radius);
}
.taskset-task-row code {
  color: var(--muted);
}
.undo-toast-region {
  position: fixed;
  bottom: 18px;
  left: 50%;
  transform: translateX(-50%);
  display: grid;
  gap: 8px;
  z-index: 60;
  pointer-events: none;
}
.undo-toast {
  display: flex;
  align-items: center;
  gap: 12px;
  pointer-events: auto;
  background: var(--panel-strong);
  color: var(--ink);
  border: 1px solid var(--border);
  border-left: 3px solid var(--success);
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  padding: 10px 14px;
  font-size: 13px;
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.undo-toast.is-leaving {
  opacity: 0;
  transform: translateY(8px);
}
.undo-toast button {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--primary);
  color: var(--on-accent);
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
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
/* TASK-AR-332: file attachments (drop zone, thumbnails, lightbox, preview) */
.attachments {
  margin-top: 14px;
  border-top: 1px solid var(--line);
  padding-top: 12px;
}
.attachments-title {
  font-size: 12px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}
.attach-dropzone {
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: 14px;
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  background: var(--inset-soft);
  cursor: pointer;
  transition: border-color 0.15s ease, background 0.15s ease;
}
.attach-dropzone:hover,
.attach-dropzone:focus-within {
  border-color: var(--primary-line);
  background: var(--primary-soft);
}
.attach-dropzone.is-dragover {
  border-color: var(--primary);
  background: var(--primary-soft-strong);
  color: var(--ink);
}
.attach-hint {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: var(--subtle);
}
.attach-error {
  margin-top: 8px;
  color: var(--danger);
  font-size: 12px;
}
.attach-list {
  list-style: none;
  margin: 10px 0 0;
  padding: 0;
  display: grid;
  gap: 8px;
}
.attach-item {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 8px;
  background: var(--tile);
}
.attach-thumb {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  object-fit: cover;
  border: 1px solid var(--line);
  background: var(--panel);
  cursor: zoom-in;
  flex: 0 0 auto;
}
.attach-icon {
  width: 44px;
  height: 44px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  flex: 0 0 auto;
}
.attach-body {
  min-width: 0;
  flex: 1 1 auto;
}
.attach-name {
  display: block;
  font-size: 13px;
  overflow-wrap: anywhere;
  color: var(--ink);
}
.attach-meta {
  display: block;
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}
.attach-actions {
  display: flex;
  gap: 6px;
  flex: 0 0 auto;
}
.attach-actions a,
.attach-actions button {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid var(--line-strong);
  background: var(--surface-raised);
  color: var(--primary);
  cursor: pointer;
  text-decoration: none;
}
.attach-preview {
  margin-top: 8px;
  max-width: 100%;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--pre-bg);
  color: var(--pre-ink);
  padding: 10px;
  font-size: 12px;
  line-height: 1.45;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.attach-lightbox {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--scrim);
  padding: 24px;
}
.attach-lightbox img {
  max-width: 92vw;
  max-height: 88vh;
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  background: var(--paper);
}
.attach-lightbox-close {
  position: absolute;
  top: 16px;
  right: 20px;
  font-size: 22px;
  line-height: 1;
  border: 1px solid var(--line-strong);
  background: var(--surface-raised);
  color: var(--ink);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  cursor: pointer;
}
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
  background: var(--panel);
  cursor: pointer;
}
.team-role-badge:hover { color: var(--nav-active-text); border-color: var(--primary-line); background: var(--primary-soft); }
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

/* ===== Workload heatmap (TASK-AR-337) =====
 * Cell color is ALWAYS a semantic token (--heat-*); per-cell load is expressed
 * only as opacity via the inline --cell-intensity custom property, so no raw
 * rgba/hex is ever emitted (tokenization gate stays green). */
.workload-header { display: flex; align-items: baseline; gap: 12px; }
.workload-summary { color: var(--muted); font-size: 13px; margin: 0; }
.workload-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 12px 0; flex-wrap: wrap; }
.workload-scope { display: inline-flex; border: 1px solid var(--line-strong); border-radius: 999px; overflow: hidden; }
.workload-scope-btn { background: var(--panel); color: var(--muted); border: 0; padding: 6px 14px; font-size: 13px; cursor: pointer; }
.workload-scope-btn.is-active { background: var(--primary-soft); color: var(--nav-active-text); font-weight: 600; }
.workload-legend { list-style: none; display: flex; gap: 12px; margin: 0; padding: 0; font-size: 12px; color: var(--muted); }
.workload-legend li { display: inline-flex; align-items: center; gap: 6px; }
.workload-legend .heat-swatch { width: 14px; height: 14px; border-radius: 3px; border: 1px solid var(--line); }
.heat-swatch.band-idle { background: var(--heat-idle); }
.heat-swatch.band-normal { background: var(--heat-normal); }
.heat-swatch.band-busy { background: var(--heat-busy); }
.heat-swatch.band-overload { background: var(--heat-overload); }
.workload-grid { display: grid; gap: 4px; overflow-x: auto; }
.workload-row { display: grid; grid-template-columns: var(--heat-label-col, 200px) 1fr; gap: 4px; align-items: stretch; }
.workload-row.is-head .workload-label { color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; }
.workload-label { display: flex; flex-direction: column; justify-content: center; padding: 6px 10px; font-size: 13px; overflow-wrap: anywhere; }
.workload-label small { color: var(--muted); font-size: 11px; }
.workload-cells { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(56px, 1fr); gap: 4px; }
.workload-cell {
  position: relative;
  border: 1px solid var(--line);
  border-radius: 6px;
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  background: var(--panel);
}
.workload-cell.is-head { background: transparent; border: 0; color: var(--muted); font-size: 11px; font-weight: 500; cursor: default; }
/* The fill layer is a single token color; opacity (--cell-intensity) is the
 * only per-cell variable, so the rendered color is always var(--heat-base). */
.workload-cell .heat-fill {
  position: absolute;
  inset: 0;
  border-radius: 6px;
  background: var(--heat-base);
  opacity: var(--cell-intensity, 0);
  pointer-events: none;
}
.workload-cell.band-idle .heat-fill { background: var(--heat-idle); }
.workload-cell.band-normal .heat-fill { background: var(--heat-normal); }
.workload-cell.band-busy .heat-fill { background: var(--heat-busy); }
.workload-cell.band-overload .heat-fill { background: var(--heat-overload); }
.workload-cell .heat-count { position: relative; z-index: 1; }
.workload-cell.band-overload { border-color: var(--danger-line); }
.workload-empty { color: var(--muted); padding: 20px; }

/* ===== Custom properties / labels / automation / triage (TASK-AR-331) ===== */
/* Label colors flow through a FIXED token palette. The JS only ever sets
 * data-color="<token>"; these rules resolve each token via var(--token) so no
 * raw/user CSS is ever injected (tokenization gate stays green). */
.label-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  background: var(--raise);
  border: 1px solid var(--line);
}
.label-chip::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--subtle);
}
.label-chip[data-color="primary"]::before { background: var(--primary); }
.label-chip[data-color="success"]::before { background: var(--success); }
.label-chip[data-color="warning"]::before { background: var(--warning); }
.label-chip[data-color="danger"]::before { background: var(--danger); }
.label-chip[data-color="violet"]::before { background: var(--violet); }
.label-chip[data-color="teal"]::before { background: var(--teal); }
.label-chip[data-color="amber"]::before { background: var(--amber); }
.label-chip[data-color="info"]::before { background: var(--info); }
.label-chip[data-color="purple"]::before { background: var(--purple); }
.label-chip[data-color="blue"]::before { background: var(--blue); }
.config-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 14px;
}
.config-form input,
.config-form select {
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.config-form button {
  padding: 8px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--primary);
  background: var(--primary);
  color: var(--on-accent);
  font: inherit;
  cursor: pointer;
}
.config-form button:hover { background: var(--primary-hover); }
.config-form-arrow { color: var(--muted); font-weight: 700; }
.config-summary { color: var(--muted); font-size: 13px; margin-bottom: 12px; }
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.config-card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.config-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.config-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  font-size: 12px;
  color: var(--muted);
}
.config-card-meta strong { color: var(--ink); }
.config-card-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.config-action {
  padding: 4px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.config-action:hover { background: var(--raise-strong); }
.rule-state {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
}
.rule-state.is-active { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
.rule-state.is-inactive { color: var(--muted); background: var(--raise); }
.rule-state.is-invalid { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.rule-flow {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  flex-wrap: wrap;
}
.rule-token {
  padding: 2px 8px;
  border-radius: var(--radius);
  background: var(--primary-soft);
  color: var(--primary-hover);
  font-weight: 600;
}
.rule-flow-arrow { color: var(--muted); }
/* Calendar / scheduling (TASK-AR-335). All colors are theme tokens. */
.calendar-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 10px; }
.calendar-header h2 { margin: 0; font-size: 16px; color: var(--ink); }
.calendar-nav { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.calendar-period { font-weight: 600; color: var(--ink); min-width: 140px; text-align: center; }
.calendar-nav-btn, .calendar-mode {
  padding: 4px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
.calendar-nav-btn:hover, .calendar-mode:hover { background: var(--raise-strong); }
.calendar-mode.is-active { background: var(--primary-soft); color: var(--primary-hover); border-color: var(--primary-line); }
.calendar-view-toggle { display: inline-flex; gap: 4px; }
.calendar-summary { color: var(--muted); font-size: 13px; margin-bottom: 10px; }
.calendar-summary strong { color: var(--ink); }
.calendar-reminders { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.calendar-reminder {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--warning-line);
  background: var(--warning-soft);
  color: var(--warning);
}
.calendar-reminder.is-overdue { border-color: var(--danger-line); background: var(--danger-soft); color: var(--danger); }
.calendar-reminder strong { color: var(--ink); }
.calendar-reminder-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid currentColor;
}
.calendar-legend { display: flex; flex-wrap: wrap; gap: 8px 16px; list-style: none; padding: 0; margin: 0 0 12px; font-size: 12px; color: var(--muted); }
.calendar-legend li { display: flex; align-items: center; gap: 6px; }
.calendar-dot { width: 10px; height: 10px; border-radius: 999px; display: inline-block; background: var(--muted); }
.calendar-dot-milestone { background: var(--violet); }
.calendar-dot-meeting { background: var(--primary); }
.calendar-dot-completion { background: var(--success); }
.calendar-dot-deadline { background: var(--warning); }
.calendar-dot-scheduled { background: var(--teal); }
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: 6px;
}
.calendar-weekday { font-size: 11px; font-weight: 600; color: var(--muted); text-align: center; padding: 4px 0; text-transform: uppercase; }
.calendar-cell {
  min-height: 84px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--tile);
  padding: 4px 6px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  overflow: hidden;
}
.calendar-cell.is-outside { background: var(--inset-soft); color: var(--subtle); }
.calendar-cell.is-today { border-color: var(--primary-line); box-shadow: var(--focus); }
.calendar-cell-date { font-size: 12px; font-weight: 600; color: var(--ink); }
.calendar-cell.is-outside .calendar-cell-date { color: var(--subtle); }
.calendar-event {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: var(--raise);
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.calendar-event-milestone { border-color: var(--violet); background: var(--violet-soft); }
.calendar-event-meeting,
.calendar-event-seminar { border-color: var(--primary-line); background: var(--primary-soft); }
.calendar-event-completion { border-color: var(--success-line); background: var(--success-soft); }
.calendar-event-deadline { border-color: var(--warning-line); background: var(--warning-soft); }
.calendar-event-scheduled { border-color: var(--teal-line); background: var(--teal-soft); }
.calendar-event.is-overdue { border-color: var(--danger-line); background: var(--danger-soft); color: var(--danger); }
.calendar-schedule-panel { margin-top: 18px; }
.calendar-schedule-panel h3 { margin: 0 0 4px; font-size: 14px; color: var(--ink); }
.calendar-hint { color: var(--muted); font-size: 12px; margin: 0 0 12px; }
.calendar-cron-badge { font-family: monospace; font-size: 11px; color: var(--teal); }
.triage-summary { color: var(--muted); font-size: 13px; margin-bottom: 10px; }
.triage-summary strong { color: var(--ink); }
.triage-toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.triage-toolbar input,
.triage-toolbar select {
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.triage-reason {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--warning-line);
  color: var(--warning);
  background: var(--warning-soft);
}
.triage-reason[data-reason="unclassified"] { color: var(--info); background: var(--info-soft); border-color: var(--primary-line); }
.triage-reason[data-reason="long_blocked"] { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.config-prop-values {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  font-size: 12px;
  color: var(--muted);
}
.portability-section {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: 14px 16px;
  margin-bottom: 16px;
}
.portability-section h2 { margin: 0 0 6px; font-size: 15px; color: var(--ink); }
.portability-hint { color: var(--muted); font-size: 13px; margin: 0 0 12px; }
.portability-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.portability-btn {
  padding: 8px 14px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
  text-decoration: none;
}
.portability-btn:hover { background: var(--raise-strong); }
#import-commit-btn {
  border-color: var(--primary);
  background: var(--primary);
  color: var(--on-accent);
}
#import-commit-btn:hover:not(:disabled) { background: var(--primary-hover); }
#import-commit-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.portability-import { display: flex; flex-direction: column; gap: 10px; }
.portability-field { display: flex; flex-direction: column; gap: 4px; max-width: 220px; }
.portability-field span { font-size: 12px; color: var(--muted); }
.portability-import select,
.portability-import textarea {
  padding: 8px 10px;
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.portability-import textarea { font-family: ui-monospace, monospace; font-size: 12px; }
.portability-summary { color: var(--muted); font-size: 13px; margin: 12px 0 8px; }
.portability-summary strong { color: var(--ink); }
.portability-preview { display: flex; flex-direction: column; gap: 6px; }
.portability-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--paper);
  font-size: 13px;
}
.portability-row .portability-row-title { flex: 1; color: var(--ink); }
.portability-row .portability-row-id { color: var(--muted); font-size: 12px; }
.portability-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
}
.portability-badge.is-new { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
.portability-badge.is-duplicate { color: var(--warning); background: var(--warning-soft); border-color: var(--warning-line); }
.portability-badge.is-invalid { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.portability-row-reason { color: var(--muted); font-size: 12px; }

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

/* ===== Subtask + dependency model: timeline + graph (TASK-AR-330) ===== */
.timeline,
.dep-graph {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
}
.timeline-header,
.dep-graph-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}
.timeline-header h2,
.dep-graph-header h2 { margin: 0; }
.timeline-summary,
.dep-graph-summary {
  margin: 0;
  font-size: 12px;
  color: var(--muted);
}
.dep-cycle-warning {
  margin: 0;
  padding: 8px 12px;
  border: 1px solid var(--danger-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: 12px;
  font-weight: 600;
}
.timeline-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-x: auto;
}
.timeline-lane {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 10px;
  align-items: center;
}
.timeline-lane-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.timeline-track {
  position: relative;
  display: flex;
  gap: 6px;
  min-height: 30px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--tile);
}
.timeline-bar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  background: var(--raise);
  color: var(--ink);
  font-size: 11px;
  white-space: nowrap;
}
.timeline-bar.status-completed { border-color: var(--success-line); background: var(--success-soft); }
.timeline-bar.status-in_progress { border-color: var(--warning-line); background: var(--warning-soft); }
.timeline-bar.status-planned { border-color: var(--primary-line); background: var(--primary-soft); }
.timeline-bar.is-cycle {
  border-color: var(--danger);
  background: var(--danger-soft);
  color: var(--danger);
}
.timeline-bar-id { font-weight: 600; }
.timeline-bar-dep {
  font-size: 10px;
  color: var(--muted);
}
.timeline-arrows {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 6px;
  font-size: 11px;
  color: var(--muted);
}
.timeline-arrow {
  display: inline-flex;
  gap: 6px;
  align-items: center;
}
.timeline-arrow.is-cycle { color: var(--danger); }
.dep-graph-stage {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--canvas-grad);
  overflow: hidden;
}
.dep-graph-svg {
  display: block;
  width: 100%;
  height: 420px;
}
.dep-edge {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: none;
  opacity: 0.6;
}
.dep-edge.kind-parent { stroke: var(--subtle); stroke-dasharray: 4 3; }
.dep-edge.kind-dependency { stroke: var(--blue); }
.dep-edge.is-cycle {
  stroke: var(--danger);
  stroke-width: 3;
  opacity: 1;
}
.dep-node circle {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: var(--panel);
}
.dep-node.kind-task circle { fill: var(--panel-strong); }
.dep-node.kind-parent circle { fill: var(--primary-soft-strong); stroke: var(--primary-line); }
.dep-node.kind-missing circle { fill: var(--warning-soft); stroke: var(--warning-line); }
.dep-node.is-cycle circle { stroke: var(--danger); stroke-width: 2.5; }
.dep-node text {
  fill: var(--muted);
  font-size: 10px;
  text-anchor: middle;
}
.dep-graph-empty { fill: var(--subtle); font-size: 14px; }
.dep-graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  color: var(--muted);
}
.dep-graph-legend .legend-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 5px;
  border-radius: 3px;
  vertical-align: middle;
}
.dep-graph-legend .legend-dependency { background: var(--blue); }
.dep-graph-legend .legend-parent { background: var(--subtle); }
.dep-graph-legend .legend-cycle { background: var(--danger); }

/* ===== State machine interactive viewer (TASK-AR-336) ===== */
.state-machine-viewer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.state-machine-hint {
  font-size: 12px;
  color: var(--muted);
  margin: 4px 0 0;
}
.state-machine-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  margin-top: 8px;
}
.state-machine-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.state-machine-field-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.state-machine-field select {
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  color: var(--ink);
  padding: 5px 8px;
  font-size: 12px;
  min-width: 180px;
}
.state-machine-summary {
  font-size: 12px;
  color: var(--muted);
  margin: 0;
}
.state-machine-stage {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
}
.state-machine-svg {
  display: block;
  width: 100%;
  height: 460px;
}
.state-machine-edge {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: none;
  opacity: 0.6;
}
.state-machine-edge.is-wildcard { stroke-dasharray: 5 4; opacity: 0.4; }
.state-machine-edge.is-traversed {
  stroke: var(--sm-path);
  stroke-width: 3;
  opacity: 1;
}
.state-machine-edge-label {
  fill: var(--subtle);
  font-size: 9px;
  text-anchor: middle;
}
.state-machine-node circle {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: var(--panel-strong);
}
.state-machine-node.signal-success circle { fill: var(--success-soft); stroke: var(--success-line); }
.state-machine-node.signal-warning circle { fill: var(--warning-soft); stroke: var(--warning-line); }
.state-machine-node.signal-danger circle { fill: var(--danger-soft); stroke: var(--danger-line); }
.state-machine-node.is-initial circle { stroke: var(--primary); stroke-width: 2.5; }
.state-machine-node.is-current circle {
  stroke: var(--sm-current);
  stroke-width: 4;
}
.state-machine-node.is-traversed circle { stroke: var(--sm-path); stroke-width: 2.5; }
.state-machine-node text {
  fill: var(--ink);
  font-size: 10px;
  text-anchor: middle;
}
.state-machine-node-score { fill: var(--muted); font-size: 8px; text-anchor: middle; }
.state-machine-empty { fill: var(--subtle); font-size: 14px; }
.state-machine-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 11px;
  color: var(--muted);
}
.state-machine-legend .legend-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: 5px;
  border-radius: 3px;
  vertical-align: middle;
}
.state-machine-legend .legend-pass { background: var(--success); }
.state-machine-legend .legend-watch { background: var(--warning); }
.state-machine-legend .legend-block { background: var(--danger); }
.state-machine-legend .legend-current { background: var(--sm-current); }
.state-machine-legend .legend-path { background: var(--sm-path); }

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
/* Global search box in the topbar + results dropdown (TASK-AR-334). */
.topbar-search {
  position: relative;
  flex: 1 1 320px;
  max-width: 480px;
  margin: 0 16px;
}
.global-search-input {
  width: 100%;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  color: var(--ink);
  border-radius: var(--radius);
  padding: 8px 12px;
  font-size: 13px;
}
.global-search-input:focus {
  outline: 2px solid var(--primary);
  outline-offset: 1px;
}
.global-search-results {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 25;
  max-height: 60vh;
  overflow-y: auto;
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.global-search-results[hidden] {
  display: none;
}
.search-result {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  border-bottom: 1px solid var(--line);
  background: transparent;
  color: var(--ink);
  padding: 10px 14px;
  cursor: pointer;
  font: inherit;
}
.search-result.is-active,
.search-result:hover {
  background: var(--primary-soft-strong);
}
.search-result-head {
  display: flex;
  align-items: center;
  gap: 8px;
}
.search-result-type {
  flex: none;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 1px 6px;
}
.search-result-title {
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-result-meta {
  font-size: 11px;
  color: var(--muted);
  margin-top: 2px;
}
.search-result-links {
  font-size: 11px;
  color: var(--primary);
  margin-top: 2px;
}
.search-result-group {
  padding: 6px 14px;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  background: var(--panel);
  border-bottom: 1px solid var(--line);
}
.search-empty {
  padding: 14px;
  color: var(--muted);
  font-size: 13px;
}
/* Quick open overlay (Ctrl+P): recent + favorites + live search. */
.quick-open {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: flex-start;
  justify-content: center;
}
.quick-open[hidden] {
  display: none;
}
.quick-open-backdrop {
  position: absolute;
  inset: 0;
  background: var(--scrim);
}
.quick-open-panel {
  position: relative;
  margin-top: 12vh;
  width: min(620px, 92vw);
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
}
.quick-open-input {
  width: 100%;
  border: none;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
  color: var(--ink);
  padding: 14px 16px;
  font-size: 15px;
}
.quick-open-input:focus {
  outline: none;
}
.quick-open-results {
  max-height: 56vh;
  overflow-y: auto;
}
/* Deep-link target highlight applied after a search/quick-open jump. */
.is-deeplinked {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
  box-shadow: var(--shadow-pop);
}
/* ----- TASK-AR-339: ops dashboard (token/cost, eval, gates, burndown) ----- */
/* All colors reference theme tokens; charts are inline SVG / token-styled divs
   so they retheme automatically and pass the no-raw-color tokenization gate. */
.opsdash {
  padding: 4px 2px 16px;
}
.opsdash-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.opsdash-summary {
  color: var(--muted);
  font-size: 13px;
}
.opsdash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.opsdash-card {
  background: var(--tile);
  border: 1px solid var(--tile-line);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow);
}
.opsdash-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 10px;
}
.opsdash-card-head h3 {
  margin: 0;
  font-size: 14px;
  color: var(--ink);
}
.opsdash-card-meta {
  color: var(--muted);
  font-size: 12px;
}
.opsdash-src {
  display: inline-block;
  margin-top: 8px;
  color: var(--primary);
  font-size: 12px;
  text-decoration: none;
}
.opsdash-empty {
  color: var(--muted);
  font-size: 13px;
  padding: 10px 0;
}
/* Token/cost bars: estimate track + actual fill over token colors. */
.opsdash-bar-row {
  margin-bottom: 10px;
}
.opsdash-bar-label {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: var(--ink);
  margin-bottom: 4px;
}
.opsdash-bar-label small {
  color: var(--muted);
}
.opsdash-bar-track {
  position: relative;
  height: 12px;
  border-radius: 6px;
  background: var(--progress-track);
  overflow: hidden;
}
.opsdash-bar-est {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  background: var(--primary-soft-strong);
}
.opsdash-bar-actual {
  position: absolute;
  inset: 0 auto 0 0;
  height: 100%;
  background: var(--primary);
}
.opsdash-bar-actual.is-over {
  background: var(--danger);
}
.opsdash-totals {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--line);
}
.opsdash-stat {
  display: flex;
  flex-direction: column;
}
.opsdash-stat b {
  font-size: 18px;
  color: var(--ink);
}
.opsdash-stat span {
  font-size: 11px;
  color: var(--muted);
}
/* Eval trend: inline SVG line + axis labels, stroke via token. */
.opsdash-chart {
  width: 100%;
  height: auto;
  display: block;
}
.opsdash-line {
  fill: none;
  stroke: var(--primary);
  stroke-width: 2;
}
.opsdash-line-min {
  fill: none;
  stroke: var(--warning);
  stroke-width: 1;
  stroke-dasharray: 4 3;
}
.opsdash-dot {
  fill: var(--primary);
}
.opsdash-dot.is-watch {
  fill: var(--warning);
}
.opsdash-dot.is-block {
  fill: var(--danger);
}
.opsdash-axis {
  fill: var(--muted);
  font-size: 9px;
}
.opsdash-grid-line {
  stroke: var(--line);
  stroke-width: 1;
}
/* Gate board: pass/watch/block pills mapped to semantic tokens. */
.opsdash-gate-counts {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.opsdash-gate-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 56px;
  padding: 6px 8px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
}
.opsdash-gate-count b {
  font-size: 18px;
}
.opsdash-gate-count span {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.opsdash-gate-count.is-pass {
  background: var(--success-soft);
  border-color: var(--success-line);
  color: var(--success);
}
.opsdash-gate-count.is-watch {
  background: var(--warning-soft);
  border-color: var(--warning-line);
  color: var(--warning);
}
.opsdash-gate-count.is-block {
  background: var(--danger-soft);
  border-color: var(--danger-line);
  color: var(--danger);
}
.opsdash-gate-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 260px;
  overflow-y: auto;
}
.opsdash-gate-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--line);
  font-size: 12px;
}
.opsdash-gate-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex: none;
  background: var(--muted);
}
.opsdash-gate-dot.is-pass {
  background: var(--success);
}
.opsdash-gate-dot.is-watch {
  background: var(--warning);
}
.opsdash-gate-dot.is-block {
  background: var(--danger);
}
.opsdash-gate-name {
  flex: 1;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.opsdash-gate-ref {
  color: var(--muted);
  font-size: 11px;
}
/* Burndown + velocity: token-styled progress + SVG bar chart. */
.opsdash-burndown-bars {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}
.opsdash-velocity-head {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 6px;
}
.opsdash-velocity-bars {
  display: flex;
  align-items: flex-end;
  gap: 6px;
  height: 80px;
}
.opsdash-vbar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 2px;
}
.opsdash-vbar-fill {
  width: 100%;
  background: var(--success);
  border-radius: 3px 3px 0 0;
  min-height: 2px;
}
.opsdash-vbar-label {
  font-size: 9px;
  color: var(--muted);
}
.opsdash-vbar-count {
  font-size: 10px;
  color: var(--ink);
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
// TASK-AR-329: taskset lifecycle + bulk command types accepted by the
// ui_commands COMMAND_TYPES allowlist. Every mutation below routes through
// /api/commands -> submit_command (proposal-only for taskset.* registry writes).
const tasksetCommandTypes = ["taskset.create", "taskset.rename", "taskset.archive", "taskset.template", "task.move", "task.bulk_edit"];
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
// TASK-AR-336: interactive state-machine viewer selection (machine + task).
let selectedStateMachineId = null;
let selectedStateMachineTaskId = null;
// TASK-AR-329: taskset lifecycle UI selection + templates.
let selectedBulkTaskIds = new Set();
const tasksetTemplates = [
  { key: "analysis-suite", label: "Analysis Suite" },
  { key: "release-cycle", label: "Release Cycle" },
];
let teamOnlineOnly = false;
let peekTimer = null;
let peekAnchorId = null;
let boardDragId = null;
let boardLifted = null;
// TASK-AR-335: calendar view state (anchor day + month/week mode).
let calendarAnchor = null;
let calendarMode = "month";

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
  "messages", "events", "evidence", "planner", "triage", "roadmap", "map", "sources",
  "automation", "properties", "labels", "portability", "writes",
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

/* ===== Global search + quick open (TASK-AR-334) =====================
 * Full-text search across >=5 entity types (task/taskset/message/event/
 * evidence/review) from a single box, with Slack-style operators
 * (type:/status:/owner:/date:). Results deep-link via the AR-321 hash
 * route. Ctrl+P opens a quick-open overlay (recent + favorites + live
 * search) and is gated so it never collides with the Ctrl+K command
 * palette nor hijacks typing inside inputs. */
const SEARCH_RECENT_KEY = "ar-search-recent";
const SEARCH_FAVORITES_KEY = "ar-search-favorites";
let searchResults = [];
let searchActiveIndex = 0;
let searchDebounce = null;
let quickOpenResults = [];
let quickOpenActiveIndex = 0;
let quickOpenDebounce = null;

function readJsonStore(key) {
  try {
    const raw = window.localStorage.getItem(key);
    const value = raw ? JSON.parse(raw) : [];
    return Array.isArray(value) ? value : [];
  } catch (error) { return []; }
}

function writeJsonStore(key, value) {
  try { window.localStorage.setItem(key, JSON.stringify(value)); } catch (error) {}
}

function recordRecentEntity(entry) {
  if (!entry || !entry.id) return;
  const recent = readJsonStore(SEARCH_RECENT_KEY)
    .filter((item) => !(item.id === entry.id && item.entity_type === entry.entity_type));
  recent.unshift({ id: entry.id, entity_type: entry.entity_type, title: entry.title, deep_link: entry.deep_link });
  writeJsonStore(SEARCH_RECENT_KEY, recent.slice(0, 12));
}

function favoriteEntities() {
  return readJsonStore(SEARCH_FAVORITES_KEY);
}

async function fetchSearch(query) {
  const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function searchResultRow(item, index, active) {
  const type = escapeHtml(item.entity_type || "");
  const title = escapeHtml(item.title || item.id || "");
  const metaParts = [];
  if (item.status) metaParts.push(escapeHtml(item.status));
  if (item.owner) metaParts.push(escapeHtml(item.owner));
  if (item.date) metaParts.push(escapeHtml(item.date));
  if (item.id) metaParts.push(escapeHtml(item.id));
  const links = (item.related || []).map((rel) => {
    if (rel.sha) return `commit ${escapeHtml(rel.label || rel.sha)}`;
    return `doc ${escapeHtml(rel.label || rel.path || "")}`;
  });
  const linkHtml = links.length ? `<div class="search-result-links">${links.join(" &middot; ")}</div>` : "";
  return `<button type="button" class="search-result${active ? " is-active" : ""}" role="option"`
    + ` data-result-index="${index}" data-deep-link="${escapeHtml(item.deep_link || "")}"`
    + ` data-entity-id="${escapeHtml(item.id || "")}" data-entity-type="${type}">`
    + `<div class="search-result-head"><span class="search-result-type">${type}</span>`
    + `<span class="search-result-title">${title}</span></div>`
    + `<div class="search-result-meta">${metaParts.join(" &middot; ")}</div>${linkHtml}</button>`;
}

function renderGlobalSearchResults(query) {
  const box = $("global-search-results");
  const input = $("global-search-input");
  if (!box) return;
  if (!query) {
    box.hidden = true;
    if (input) input.setAttribute("aria-expanded", "false");
    return;
  }
  box.hidden = false;
  if (input) input.setAttribute("aria-expanded", "true");
  if (!searchResults.length) {
    // Query is echoed back to the user; escapeHtml guards against XSS.
    box.innerHTML = `<div class="search-empty">No matches for &ldquo;${escapeHtml(query)}&rdquo;</div>`;
    return;
  }
  if (searchActiveIndex >= searchResults.length) searchActiveIndex = searchResults.length - 1;
  if (searchActiveIndex < 0) searchActiveIndex = 0;
  box.innerHTML = searchResults
    .map((item, index) => searchResultRow(item, index, index === searchActiveIndex))
    .join("");
}

function runGlobalSearch() {
  const input = $("global-search-input");
  const query = input ? input.value.trim() : "";
  if (!query) {
    searchResults = [];
    renderGlobalSearchResults("");
    return;
  }
  fetchSearch(query)
    .then((payload) => {
      searchResults = payload.items || [];
      searchActiveIndex = 0;
      renderGlobalSearchResults(query);
    })
    .catch(() => {
      searchResults = [];
      renderGlobalSearchResults(query);
    });
}

function navigateToResult(item) {
  if (!item) return;
  recordRecentEntity(item);
  closeGlobalSearch();
  closeQuickOpen();
  const link = item.deep_link || (item.route ? `#/${item.route}` : "");
  if (link) {
    // Force hashchange even if only the select= param changed.
    if (window.location.hash === link) applyHashRoute();
    else window.location.hash = link;
  }
}

function closeGlobalSearch() {
  const box = $("global-search-results");
  if (box) box.hidden = true;
  const input = $("global-search-input");
  if (input) input.setAttribute("aria-expanded", "false");
}

function globalSearchOpen() {
  const box = $("global-search-results");
  return Boolean(box && !box.hidden);
}

/* ----- Ctrl+P quick open ----- */
function quickOpenIsOpen() {
  const overlay = $("quick-open");
  return Boolean(overlay && !overlay.hidden);
}

function quickOpenDefaultItems() {
  const recent = readJsonStore(SEARCH_RECENT_KEY).map((item) => ({ ...item, _group: "Recent" }));
  const favorites = favoriteEntities().map((item) => ({ ...item, _group: "Favorites" }));
  return favorites.concat(recent);
}

function renderQuickOpen() {
  const box = $("quick-open-results");
  const input = $("quick-open-input");
  if (!box) return;
  const query = input ? input.value.trim() : "";
  const items = query ? quickOpenResults : quickOpenDefaultItems();
  if (!items.length) {
    box.innerHTML = query
      ? `<div class="search-empty">No matches for &ldquo;${escapeHtml(query)}&rdquo;</div>`
      : `<div class="search-empty">Recent and favorite entities appear here.</div>`;
    return;
  }
  if (quickOpenActiveIndex >= items.length) quickOpenActiveIndex = items.length - 1;
  if (quickOpenActiveIndex < 0) quickOpenActiveIndex = 0;
  let lastGroup = null;
  const rows = [];
  items.forEach((item, index) => {
    if (item._group && item._group !== lastGroup) {
      rows.push(`<div class="search-result-group">${escapeHtml(item._group)}</div>`);
      lastGroup = item._group;
    }
    rows.push(searchResultRow(item, index, index === quickOpenActiveIndex));
  });
  box.innerHTML = rows.join("");
}

function quickOpenCurrentItems() {
  const input = $("quick-open-input");
  const query = input ? input.value.trim() : "";
  return query ? quickOpenResults : quickOpenDefaultItems();
}

function runQuickOpenSearch() {
  const input = $("quick-open-input");
  const query = input ? input.value.trim() : "";
  if (!query) {
    quickOpenResults = [];
    renderQuickOpen();
    return;
  }
  fetchSearch(query)
    .then((payload) => {
      quickOpenResults = payload.items || [];
      quickOpenActiveIndex = 0;
      renderQuickOpen();
    })
    .catch(() => { quickOpenResults = []; renderQuickOpen(); });
}

function openQuickOpen() {
  const overlay = $("quick-open");
  if (!overlay) return;
  overlay.hidden = false;
  quickOpenActiveIndex = 0;
  quickOpenResults = [];
  const input = $("quick-open-input");
  if (input) { input.value = ""; input.focus(); }
  renderQuickOpen();
}

function closeQuickOpen() {
  const overlay = $("quick-open");
  if (overlay) overlay.hidden = true;
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
  if (paletteIsOpen() || quickOpenIsOpen()) return;
  // Single-key (j/k/Enter) nav must never fire while typing in a text field
  // (input/textarea/select/contentEditable) -- shared guard, also used to
  // reason about the Ctrl+P/Ctrl+K shortcuts below.
  if (eventTargetIsTextInput(event)) return;
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
  host.querySelectorAll("[data-taskset-lifecycle]").forEach((button) => {
    button.addEventListener("click", () => {
      submitTasksetLifecycle(button.dataset.tasksetLifecycle, button.dataset.tasksetId, button.dataset.tasksetName);
    });
  });
  host.querySelectorAll("[data-bulk-task-id]").forEach((box) => {
    box.addEventListener("change", () => {
      toggleBulkTask(box.dataset.bulkTaskId, box.checked);
    });
  });
}

function toggleBulkTask(taskId, on) {
  if (on) selectedBulkTaskIds.add(taskId);
  else selectedBulkTaskIds.delete(taskId);
  renderBulkBar();
  renderTaskSetDirectory();
}

function clearBulkSelection() {
  selectedBulkTaskIds.clear();
  renderBulkBar();
  renderTaskSetDirectory();
}

function renderBulkBar() {
  const bar = $("taskset-bulk-bar");
  if (!bar) return;
  const count = selectedBulkTaskIds.size;
  bar.hidden = count === 0;
  const label = $("taskset-bulk-count");
  if (label) label.textContent = `${count} selected`;
}

function populateBulkMoveOptions() {
  const select = $("taskset-bulk-move");
  if (!select) return;
  const current = select.value;
  const options = ['<option value="">Move to taskset…</option>'].concat(
    (runtimeState.task_sets || []).map((ts) => `<option value="${escapeHtml(ts.id)}">${escapeHtml(ts.display_name || ts.id)}</option>`)
  );
  select.innerHTML = options.join("");
  select.value = current;
}

async function submitTasksetLifecycle(action, taskSetId, currentName) {
  const payload = { actor: "owner", task_set_id: taskSetId };
  let type = "taskset.archive";
  if (action === "rename") {
    type = "taskset.rename";
    const name = window.prompt("New taskset name", currentName || taskSetId);
    if (!name) return;
    payload.display_name = name;
  }
  const result = await sendJson("/api/commands", { type, payload: { type, target: taskSetId, payload } });
  pushActivityToast("assignment", `taskset ${action}`, `${taskSetId} (${(result && result.status) || "queued"})`);
}

async function submitTasksetCreate(displayName, summary) {
  const payload = { actor: "owner", display_name: displayName };
  if (summary) payload.summary = summary;
  const result = await sendJson("/api/commands", { type: "taskset.create", payload: { type: "taskset.create", payload } });
  pushActivityToast("assignment", "taskset created", `${displayName} (${(result && result.status) || "queued"})`);
  return result;
}

async function instantiateTasksetTemplate(templateKey) {
  const result = await sendJson("/api/commands", {
    type: "taskset.template",
    payload: { type: "taskset.template", payload: { actor: "owner", template: templateKey } }
  });
  const created = (result && result.result) || {};
  pushActivityToast("assignment", "template instantiated", `${templateKey}: ${created.task_count || 0} tasks`);
  return result;
}

async function applyBulkEdit() {
  const ids = Array.from(selectedBulkTaskIds);
  if (!ids.length) return;
  const status = $("taskset-bulk-status")?.value || "";
  const priority = $("taskset-bulk-priority")?.value || "";
  const owner = $("taskset-bulk-owner")?.value.trim() || "";
  const moveTo = $("taskset-bulk-move")?.value || "";

  if (moveTo) {
    for (const id of ids) {
      await sendJson("/api/commands", { type: "task.move", payload: { type: "task.move", target: id, payload: { task_set_id: moveTo } } });
    }
    pushUndoToast(`${ids.length} task(s) moved`, null);
    clearBulkSelection();
    return;
  }

  const fields = {};
  if (status) fields.status = status;
  if (priority) fields.priority = priority;
  if (owner) fields.owner = owner;
  if (!Object.keys(fields).length) return;

  const result = await sendJson("/api/commands", {
    type: "task.bulk_edit",
    payload: { type: "task.bulk_edit", payload: Object.assign({ task_ids: ids }, fields) }
  });
  const undo = result && result.result && result.result.undo;
  pushUndoToast(`${ids.length} task(s) edited`, undo);
  clearBulkSelection();
}

function pushUndoToast(message, undo) {
  const host = $("undo-toast-region");
  if (!host) return;
  const toast = document.createElement("div");
  toast.className = "undo-toast";
  const text = document.createElement("span");
  text.textContent = message;
  toast.appendChild(text);
  if (undo && Array.isArray(undo.items) && undo.items.length) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Undo";
    button.addEventListener("click", async () => {
      await runUndo(undo);
      dismissToast(toast);
    });
    toast.appendChild(button);
  }
  host.appendChild(toast);
  while (host.children.length > 3) host.removeChild(host.firstChild);
  setTimeout(() => dismissToast(toast), 8000);
}

function dismissToast(toast) {
  if (!toast || !toast.parentNode) return;
  toast.classList.add("is-leaving");
  setTimeout(() => { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 240);
}

async function runUndo(undo) {
  // Rebuild a single bulk_edit per restored field-value combination from the
  // captured before-state. Each task may have had a distinct prior value, so we
  // group identical restores into batched commands.
  const byValue = {};
  (undo.items || []).forEach((item) => {
    const before = item.before || {};
    const key = JSON.stringify(before);
    (byValue[key] = byValue[key] || { fields: before, ids: [] }).ids.push(item.id);
  });
  for (const key of Object.keys(byValue)) {
    const group = byValue[key];
    const fields = {};
    Object.keys(group.fields).forEach((field) => {
      if (group.fields[field] !== null && group.fields[field] !== undefined) fields[field] = group.fields[field];
    });
    if (!Object.keys(fields).length) continue;
    await sendJson("/api/commands", {
      type: "task.bulk_edit",
      payload: { type: "task.bulk_edit", payload: Object.assign({ task_ids: group.ids }, fields) }
    });
  }
  pushActivityToast("review", "undo applied", `${(undo.items || []).length} task(s) restored`);
}

function renderTasksetTemplates() {
  const host = $("taskset-template-buttons");
  if (!host) return;
  host.innerHTML = tasksetTemplates.map((tpl) =>
    `<button class="taskset-template-btn" type="button" data-template-key="${escapeHtml(tpl.key)}">${escapeHtml(tpl.label)}</button>`
  ).join("");
  host.querySelectorAll("[data-template-key]").forEach((button) => {
    button.addEventListener("click", () => instantiateTasksetTemplate(button.dataset.templateKey));
  });
}

function tasksForTaskSet(taskSetId) {
  return (runtimeState.tasks || []).filter((task) => (task.task_set_id || "") === taskSetId);
}

function tasksetTaskRows(taskSet) {
  const tasks = tasksForTaskSet(taskSet.id);
  if (!tasks.length) return "";
  const rows = tasks.slice(0, 12).map((task) => {
    const checked = selectedBulkTaskIds.has(task.id) ? " checked" : "";
    const selectedClass = selectedBulkTaskIds.has(task.id) ? " is-selected" : "";
    return `<label class="taskset-task-row${selectedClass}">
      <input class="taskset-task-select" type="checkbox" data-bulk-task-id="${escapeHtml(task.id)}"${checked} aria-label="Select ${escapeHtml(task.id)}">
      <code>${escapeHtml(task.id)}</code>
      <span class="meta-label">${escapeHtml(task.status || "")}</span>
      <span>${escapeHtml(task.title || "")}</span>
    </label>`;
  }).join("");
  return `<div class="taskset-card-tasks" aria-label="Tasks in ${escapeHtml(taskSet.id)}">${rows}</div>`;
}

function taskSetCards(taskSets, options = {}) {
  const compact = Boolean(options.compact);
  return taskSets.map((taskSet) => {
    const aliases = (taskSet.quick_aliases || taskSet.aliases || []).slice(0, compact ? 2 : 4);
    const nextTask = taskSet.next_task_id || "no open task";
    const taskCount = `${taskSet.tasks_done || 0}/${taskSet.tasks_total || 0}`;
    const command = taskSetCommand(taskSet, "start") || taskSetCommand(taskSet, "plan");
    return `
      <article class="taskset-card ${taskSetStatusClass(taskSet.status)}" tabindex="0" data-taskset-id="${escapeHtml(taskSet.id)}" data-entity-id="${escapeHtml(taskSet.id)}">
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
        ${compact ? "" : tasksetTaskRows(taskSet)}
        ${compact ? "" : `<code class="taskset-command">${escapeHtml(command)}</code>`}
        ${compact ? "" : `<div class="taskset-actions">
          <button class="taskset-action" type="button" data-taskset-action="plan" data-taskset-id="${escapeHtml(taskSet.id)}">Plan</button>
          <button class="taskset-action" type="button" data-taskset-action="start" data-taskset-id="${escapeHtml(taskSet.id)}">Start</button>
          <button class="taskset-action" type="button" data-taskset-action="gate" data-taskset-id="${escapeHtml(taskSet.id)}">Gate</button>
          <button class="taskset-action" type="button" data-taskset-lifecycle="rename" data-taskset-id="${escapeHtml(taskSet.id)}" data-taskset-name="${escapeHtml(taskSet.display_name || taskSet.id)}">Rename</button>
          <button class="taskset-action" type="button" data-taskset-lifecycle="archive" data-taskset-id="${escapeHtml(taskSet.id)}">Archive</button>
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
  populateBulkMoveOptions();
  renderBulkBar();
  renderTasksetTemplates();
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

// Board team/role filter (AR-337). Set by org-chart / heatmap drill-down so the
// board shows only the tasks RESOLVED to a team/role. Consistency: this reads
// the same task.assigned_team/assigned_role the heatmap and org chart use.
let boardTeamFilter = null;

function setBoardTeamFilter(team, role) {
  boardTeamFilter = (team || role) ? { team: team || null, role: role || null } : null;
  renderKanban();
}

function taskMatchesTeamFilter(task) {
  if (!boardTeamFilter) return true;
  if (boardTeamFilter.team && task.assigned_team !== boardTeamFilter.team) return false;
  if (boardTeamFilter.role && task.assigned_role !== boardTeamFilter.role) return false;
  return true;
}

function renderBoardTeamFilterBanner() {
  const host = $("board-team-filter");
  if (!host) return;
  if (!boardTeamFilter) {
    host.hidden = true;
    host.innerHTML = "";
    return;
  }
  const label = [boardTeamFilter.team, boardTeamFilter.role].filter(Boolean).join(" / ");
  host.hidden = false;
  host.innerHTML = `<span>Filtered to <strong>${escapeHtml(label)}</strong></span>` +
    `<button type="button" id="board-team-filter-clear">Clear</button>`;
  const clear = $("board-team-filter-clear");
  if (clear) clear.addEventListener("click", () => setBoardTeamFilter(null));
}

function renderKanban() {
  const tasks = (runtimeState.tasks || []).filter(taskMatchesTeamFilter);
  renderBoardTeamFilterBanner();
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
    <article class="list-row" data-entity-id="${escapeHtml(message.id)}">
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
    <article class="audit-card event-card ${auditToneClass(event)}" data-entity-id="${escapeHtml(event.id || "")}">
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
    <article class="audit-card evidence-card pass" data-entity-id="${escapeHtml(item.id || "")}">
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

// ----- TASK-AR-336: interactive state-machine viewer -----
const SM_SIGNAL_LABELS = { pass: "Proceed (pass)", watch: "Needs attention (watch)", block: "Stop until fixed (block)" };

function stateMachinesData() {
  return runtimeState.state_machines || [];
}

function selectedStateMachine() {
  const machines = stateMachinesData();
  if (!machines.length) return null;
  return machines.find((machine) => machine.id === selectedStateMachineId) || machines[0];
}

// Public entry: deep-link from a task into the state-machine viewer with the
// task machine selected and the task highlighted. Read-only navigation.
function viewTaskInStateMachine(taskId) {
  selectedStateMachineId = "task";
  selectedStateMachineTaskId = taskId || null;
  activateView("statemachines");
  renderStateMachineViewer();
}

function stateMachineNodePositions(nodes) {
  // Deterministic horizontal lifecycle layout: states are laid out left to
  // right in declaration order and wrapped onto rows so larger machines stay
  // readable. Same input always yields the same coordinates.
  const positions = {};
  const perRow = Math.min(4, Math.max(1, nodes.length));
  const marginX = 140;
  const marginY = 110;
  const spanX = nodes.length > 1 ? (1000 - marginX * 2) / Math.max(1, perRow - 1) : 0;
  const rows = Math.ceil(nodes.length / perRow) || 1;
  const spanY = rows > 1 ? (600 - marginY * 2) / (rows - 1) : 0;
  nodes.forEach((node, index) => {
    const row = Math.floor(index / perRow);
    let col = index % perRow;
    // Serpentine rows so consecutive states stay adjacent across wraps.
    if (row % 2 === 1) col = perRow - 1 - col;
    positions[node.id] = {
      x: perRow === 1 ? 500 : marginX + col * spanX,
      y: rows === 1 ? 300 : marginY + row * spanY,
    };
  });
  return positions;
}

function renderStateMachineViewer() {
  const machines = stateMachinesData();
  const select = $("state-machine-select");
  if (select) {
    select.innerHTML = machines.length
      ? machines.map((machine) => `<option value="${escapeHtml(machine.id)}">${escapeHtml(machine.id)} (${(machine.scope || "lifecycle")})</option>`).join("")
      : `<option value="">No machines</option>`;
    if (selectedStateMachine()) select.value = selectedStateMachine().id;
  }

  const machine = selectedStateMachine();
  const taskField = $("state-machine-task-field");
  const taskSelect = $("state-machine-task-select");
  const taskStates = (machine && machine.task_states) || {};
  const taskIds = Object.keys(taskStates).sort();
  if (taskField) taskField.hidden = !(machine && machine.id === "task" && taskIds.length);
  if (taskSelect) {
    taskSelect.innerHTML = `<option value="">None (machine only)</option>`
      + taskIds.map((tid) => {
          const info = taskStates[tid] || {};
          return `<option value="${escapeHtml(tid)}">${escapeHtml(tid)} - ${escapeHtml(info.current_state || "?")}</option>`;
        }).join("");
    if (selectedStateMachineTaskId && taskStates[selectedStateMachineTaskId]) {
      taskSelect.value = selectedStateMachineTaskId;
    } else {
      taskSelect.value = "";
      selectedStateMachineTaskId = null;
    }
  }

  const legend = $("state-machine-legend");
  if (legend) {
    legend.innerHTML = [
      `<li><span class="legend-swatch legend-pass"></span>pass</li>`,
      `<li><span class="legend-swatch legend-watch"></span>watch</li>`,
      `<li><span class="legend-swatch legend-block"></span>block</li>`,
      `<li><span class="legend-swatch legend-current"></span>current state</li>`,
      `<li><span class="legend-swatch legend-path"></span>traversed path</li>`,
    ].join("");
  }

  const svg = $("state-machine-svg");
  if (!svg) return;
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  if (!machine) {
    setText("state-machine-summary", "No state machines defined (agents/project/STATE-MACHINES.yml missing or empty).");
    const note = document.createElementNS(SVG_NS, "text");
    note.setAttribute("x", "500");
    note.setAttribute("y", "300");
    note.setAttribute("class", "state-machine-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = "No state machine data";
    svg.appendChild(note);
    return;
  }

  const nodes = machine.state_nodes || [];
  const edges = machine.transition_edges || [];
  const taskInfo = selectedStateMachineTaskId ? (taskStates[selectedStateMachineTaskId] || null) : null;
  const currentState = taskInfo ? taskInfo.current_state : machine.current_state;
  const traversedEdgeIds = new Set((taskInfo ? (taskInfo.transition_path || []) : []).map((edge) => edge.id));
  const traversedStates = new Set();
  (taskInfo ? (taskInfo.state_sequence || []) : []).forEach((sid) => traversedStates.add(sid));

  const summaryParts = [
    `${nodes.length} states`,
    `${edges.length} transitions`,
    `current: ${currentState || machine.initial || "unknown"}`,
  ];
  if (taskInfo) summaryParts.push(`task ${selectedStateMachineTaskId}: ${(taskInfo.transition_path || []).length} hops traversed`);
  setText("state-machine-summary", summaryParts.join(" - "));

  if (!nodes.length) {
    const note = document.createElementNS(SVG_NS, "text");
    note.setAttribute("x", "500");
    note.setAttribute("y", "300");
    note.setAttribute("class", "state-machine-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = "Machine has no states";
    svg.appendChild(note);
    return;
  }

  const positions = stateMachineNodePositions(nodes);

  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    // A wildcard edge (from "*") is drawn from the current/last-traversed state
    // (if known) or its declared target's incoming hub, falling back skipped.
    let fromId = edge.from;
    if (edge.wildcard) {
      const hub = currentState && currentState !== edge.to ? currentState : (edge.wildcard_sources || [])[0];
      fromId = hub || edge.from;
    }
    const a = positions[fromId];
    const b = positions[edge.to];
    if (!a || !b) return;
    const traversed = traversedEdgeIds.has(edge.id);
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", a.x);
    line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x);
    line.setAttribute("y2", b.y);
    line.setAttribute("class", `state-machine-edge ${edge.wildcard ? "is-wildcard" : ""} ${traversed ? "is-traversed" : ""}`);
    line.setAttribute("data-edge-id", edge.id);
    edgeLayer.appendChild(line);
    if (edge.trigger) {
      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", (a.x + b.x) / 2);
      label.setAttribute("y", (a.y + b.y) / 2 - 4);
      label.setAttribute("class", "state-machine-edge-label");
      label.textContent = String(edge.trigger).slice(0, 22);
      edgeLayer.appendChild(label);
    }
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const isCurrent = node.id === currentState;
    const isTraversed = traversedStates.has(node.id);
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute(
      "class",
      `state-machine-node signal-${node.signal_token || "subtle"} ${node.is_initial ? "is-initial" : ""} ${isCurrent ? "is-current" : ""} ${isTraversed ? "is-traversed" : ""}`
    );
    group.setAttribute("data-state-id", node.id);
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", "26");
    group.appendChild(circle);
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + 2);
    label.textContent = String(node.id).slice(0, 14);
    group.appendChild(label);
    if (node.score !== null && node.score !== undefined) {
      const score = document.createElementNS(SVG_NS, "text");
      score.setAttribute("x", pos.x);
      score.setAttribute("y", pos.y + 42);
      score.setAttribute("class", "state-machine-node-score");
      score.textContent = `${node.signal || ""} ${node.score}`.trim();
      group.appendChild(score);
    }
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
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

// ----- Subtask + dependency model: timeline + graph (TASK-AR-330) -----
const DEP_KIND_LABELS = { dependency: "Dependency (blocks)", parent: "Subtask (parent)", cycle: "Cycle" };

function timelineData() {
  return runtimeState.timeline || { lanes: [], arrows: [], cycles: [], has_cycle: false, totals: {} };
}

function dependencyGraphData() {
  return runtimeState.dependency_graph || { nodes: [], edges: [], cycles: [], has_cycle: false, totals: {} };
}

function renderCycleWarning(id, cycles) {
  const host = $(id);
  if (!host) return;
  const list = cycles || [];
  if (!list.length) {
    host.hidden = true;
    host.textContent = "";
    return;
  }
  host.hidden = false;
  const chains = list.map((cycle) => (cycle || []).map((node) => escapeHtml(node)).join(" -> "));
  host.innerHTML = `(!) Dependency cycle detected (${list.length}): ` + chains.join("; ");
}

function renderTimeline() {
  const data = timelineData();
  const totals = data.totals || {};
  setText("timeline-summary",
    `${totals.lanes || 0} lanes - ${totals.bars || 0} tasks - ${totals.arrows || 0} dependencies`
    + (data.has_cycle ? ` - ${(data.cycles || []).length} cycle(s)` : ""));
  renderCycleWarning("timeline-cycle-warning", data.cycles);

  const cycleEdges = new Set();
  (data.arrows || []).forEach((arrow) => { if (arrow.in_cycle) cycleEdges.add(arrow.id); });
  const cycleNodes = new Set();
  (data.cycles || []).forEach((cycle) => (cycle || []).forEach((node) => cycleNodes.add(node)));

  const grid = $("timeline-grid");
  if (!grid) return;
  const lanes = data.lanes || [];
  if (!lanes.length) {
    grid.innerHTML = `<div class="empty">No timeline data</div>`;
    return;
  }
  const laneHtml = lanes.map((lane) => {
    const bars = (lane.bars || []).map((bar) => {
      const bucket = bar.status_bucket || "planned";
      const isCycle = cycleNodes.has(bar.id);
      const deps = [];
      if ((bar.blocked_by || []).length) deps.push(`waits: ${bar.blocked_by.map(escapeHtml).join(", ")}`);
      if ((bar.blocks || []).length) deps.push(`blocks: ${bar.blocks.map(escapeHtml).join(", ")}`);
      const depLabel = deps.length ? `<span class="timeline-bar-dep">${deps.join(" / ")}</span>` : "";
      return `<span class="timeline-bar status-${escapeHtml(bucket)} ${isCycle ? "is-cycle" : ""}" data-task-id="${escapeHtml(bar.id)}" title="${escapeHtml(bar.label || bar.id)}">`
        + `<span class="timeline-bar-id">${escapeHtml(bar.id)}</span>${depLabel}</span>`;
    }).join("");
    return `<div class="timeline-lane" data-lane-id="${escapeHtml(lane.id)}">`
      + `<div class="timeline-lane-label" title="${escapeHtml(lane.label || lane.id)}">${escapeHtml(lane.label || lane.id)}</div>`
      + `<div class="timeline-track">${bars || `<span class="empty">empty lane</span>`}</div></div>`;
  }).join("");

  const arrows = (data.arrows || []).map((arrow) =>
    `<div class="timeline-arrow ${arrow.in_cycle ? "is-cycle" : ""}" data-arrow-id="${escapeHtml(arrow.id)}">`
    + `<span>${escapeHtml(arrow.from)}</span><span>-&gt;</span><span>${escapeHtml(arrow.to)}</span></div>`).join("");
  const arrowBlock = arrows
    ? `<div class="timeline-arrows" aria-label="Dependency arrows">${arrows}</div>`
    : "";
  grid.innerHTML = laneHtml + arrowBlock;
}

function dependencyNodePositions(nodes) {
  // Deterministic ring layout (mirrors the live map) so the graph reads the
  // same across refreshes; parent nodes sit on an inner ring.
  const positions = {};
  const cx = 500;
  const cy = 300;
  const parents = nodes.filter((node) => node.kind === "parent");
  const others = nodes.filter((node) => node.kind !== "parent");
  parents.forEach((node, index) => {
    const angle = (index / Math.max(parents.length, 1)) * Math.PI * 2 - Math.PI / 2;
    positions[node.id] = { x: cx + Math.cos(angle) * 110, y: cy + Math.sin(angle) * 90 };
  });
  others.forEach((node, index) => {
    const angle = (index / Math.max(others.length, 1)) * Math.PI * 2 - Math.PI / 2;
    positions[node.id] = { x: cx + Math.cos(angle) * 230, y: cy + Math.sin(angle) * 200 };
  });
  return positions;
}

function renderDependencyGraph() {
  const data = dependencyGraphData();
  const totals = data.totals || {};
  setText("dep-graph-summary",
    `${totals.nodes || 0} nodes - ${totals.dependency_edges || 0} deps - ${totals.parent_edges || 0} subtasks`
    + (data.has_cycle ? ` - ${(data.cycles || []).length} cycle(s)` : ""));
  renderCycleWarning("dep-cycle-warning", data.cycles);

  const legend = $("dep-graph-legend");
  if (legend) {
    legend.innerHTML = ["dependency", "parent", "cycle"].map((kind) =>
      `<li><span class="legend-swatch legend-${kind}"></span>${escapeHtml(DEP_KIND_LABELS[kind] || kind)}</li>`).join("");
  }

  const svg = $("dep-graph-svg");
  if (!svg) return;
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!nodes.length) {
    const note = document.createElementNS(SVG_NS, "text");
    note.setAttribute("x", "500");
    note.setAttribute("y", "300");
    note.setAttribute("class", "dep-graph-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = "No dependency data";
    svg.appendChild(note);
    return;
  }
  const positions = dependencyNodePositions(nodes);

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
    line.setAttribute("class", `dep-edge kind-${edge.kind || "dependency"} ${edge.in_cycle ? "is-cycle" : ""}`);
    line.setAttribute("data-edge-id", edge.id);
    edgeLayer.appendChild(line);
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `dep-node kind-${node.kind || "task"} ${node.in_cycle ? "is-cycle" : ""}`);
    group.setAttribute("data-node-id", node.id);
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", pos.x);
    circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", node.kind === "parent" ? "20" : "14");
    group.appendChild(circle);
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", pos.x);
    label.setAttribute("y", pos.y + 28);
    label.textContent = String(node.id).slice(0, 18);
    group.appendChild(label);
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
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

/* ===== Custom properties / labels / automation / triage (TASK-AR-331) ===== */
// Label colors are rendered ONLY via data-color="<token>" so the CSS resolves
// var(--token); the JS never emits an inline color, keeping label colors as a
// fixed, tokenized palette (no user-injected raw CSS).
const LABEL_COLOR_TOKENS = ["primary", "success", "warning", "danger", "violet", "teal", "amber", "info", "purple", "blue"];

function labelChip(label) {
  const token = LABEL_COLOR_TOKENS.includes(label.color_token) ? label.color_token : "primary";
  return `<span class="label-chip" data-color="${escapeHtml(token)}">${escapeHtml(label.name)}</span>`;
}

function renderTriage() {
  const host = $("triage-list");
  if (!host) return;
  const triage = (runtimeState && runtimeState.triage) || { items: [], totals: {} };
  const totals = triage.totals || {};
  setText("triage-summary", "");
  const summary = $("triage-summary");
  if (summary) {
    summary.innerHTML = `<strong>${escapeHtml(totals.total || 0)}</strong> tasks need triage`
      + ` &middot; unclassified <strong>${escapeHtml(totals.unclassified || 0)}</strong>`
      + ` &middot; overdue <strong>${escapeHtml(totals.overdue || 0)}</strong>`
      + ` &middot; long blocked <strong>${escapeHtml(totals.long_blocked || 0)}</strong>`;
  }
  const query = ($("triage-filter")?.value || "").trim().toLowerCase();
  const reasonFilter = $("triage-reason-filter")?.value || "";
  const items = (triage.items || []).filter((item) => {
    if (reasonFilter && !(item.reasons || []).includes(reasonFilter)) return false;
    if (!query) return true;
    return [item.id, item.title, item.owner_agent, item.status].join(" ").toLowerCase().includes(query);
  });
  host.innerHTML = items.length ? items.map((item) => `
    <article class="config-card">
      <div class="config-card-header">
        <b>${escapeHtml(item.id || "task")}</b>
        <span class="state-chip">${escapeHtml(item.status || "unknown")}</span>
      </div>
      <div>${escapeHtml(item.title || "")}</div>
      <div class="rule-flow">
        ${(item.reasons || []).map((reason) => `<span class="triage-reason" data-reason="${escapeHtml(reason)}">${escapeHtml(reason.replace(/_/g, " "))}</span>`).join("")}
      </div>
      <div class="config-card-meta">
        <span>Owner <strong>${escapeHtml(item.owner_agent || "unassigned")}</strong></span>
        <span>Taskset <strong>${escapeHtml(item.task_set_id || "none")}</strong></span>
        ${item.details && item.details.blocked_days !== undefined ? `<span>Blocked <strong>${escapeHtml(item.details.blocked_days)}d</strong></span>` : ""}
        ${item.details && item.details.overdue_days !== undefined ? `<span>Overdue <strong>${escapeHtml(item.details.overdue_days)}d</strong></span>` : ""}
      </div>
      ${(item.labels || []).length ? `<div class="config-prop-values">${item.labels.map((name) => labelChip({ name, color_token: "primary" })).join("")}</div>` : ""}
    </article>
  `).join("") : `<div class="empty">Triage inbox is clear</div>`;
}

// ----- Calendar / scheduling (TASK-AR-335) -----
const CALENDAR_WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const CALENDAR_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

function calendarToday() {
  const data = (runtimeState && runtimeState.calendar) || {};
  if (data.today) {
    const parts = String(data.today).split("-");
    if (parts.length === 3) return new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
  }
  return new Date();
}

function calendarDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function calendarAnchorDate() {
  if (!calendarAnchor) calendarAnchor = calendarToday();
  return calendarAnchor;
}

function calendarShift(days, months) {
  const base = calendarAnchorDate();
  calendarAnchor = new Date(base.getFullYear(), base.getMonth() + (months || 0), base.getDate() + (days || 0));
  renderCalendar();
}

function calendarVisibleDays() {
  const anchor = calendarAnchorDate();
  const days = [];
  if (calendarMode === "week") {
    const start = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate() - anchor.getDay());
    for (let i = 0; i < 7; i += 1) {
      const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
      days.push({ date, outside: false });
    }
    return days;
  }
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const gridStart = new Date(first.getFullYear(), first.getMonth(), 1 - first.getDay());
  for (let i = 0; i < 42; i += 1) {
    const date = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i);
    days.push({ date, outside: date.getMonth() !== anchor.getMonth() });
  }
  return days;
}

function calendarPeriodLabel() {
  const anchor = calendarAnchorDate();
  if (calendarMode === "week") {
    const start = new Date(anchor.getFullYear(), anchor.getMonth(), anchor.getDate() - anchor.getDay());
    const end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6);
    return `${calendarDateKey(start)} - ${calendarDateKey(end)}`;
  }
  return `${CALENDAR_MONTHS[anchor.getMonth()]} ${anchor.getFullYear()}`;
}

function renderCalendar() {
  const grid = $("calendar-grid");
  if (!grid) return;
  const data = (runtimeState && runtimeState.calendar) || { by_date: {}, reminders: [], totals: {} };
  const byDate = data.by_date || {};
  const totals = data.totals || {};
  const todayKey = data.today || calendarDateKey(new Date());

  const period = $("calendar-period");
  if (period) period.textContent = calendarPeriodLabel();
  const modeMonth = $("calendar-view-month");
  const modeWeek = $("calendar-view-week");
  if (modeMonth) { modeMonth.classList.toggle("is-active", calendarMode === "month"); modeMonth.setAttribute("aria-pressed", calendarMode === "month" ? "true" : "false"); }
  if (modeWeek) { modeWeek.classList.toggle("is-active", calendarMode === "week"); modeWeek.setAttribute("aria-pressed", calendarMode === "week" ? "true" : "false"); }

  const summary = $("calendar-summary");
  if (summary) {
    const byKind = totals.by_kind || {};
    summary.innerHTML = `<strong>${escapeHtml(totals.events || 0)}</strong> events`
      + ` &middot; milestones <strong>${escapeHtml(byKind.milestone || 0)}</strong>`
      + ` &middot; meetings <strong>${escapeHtml((byKind.meeting || 0) + (byKind.seminar || 0))}</strong>`
      + ` &middot; completions <strong>${escapeHtml(byKind.completion || 0)}</strong>`
      + ` &middot; scheduled <strong>${escapeHtml(byKind.scheduled || 0)}</strong>`
      + ` &middot; reminders <strong>${escapeHtml(totals.reminders || 0)}</strong>`;
  }

  const reminderHost = $("calendar-reminders");
  if (reminderHost) {
    const reminders = data.reminders || [];
    reminderHost.innerHTML = reminders.length ? reminders.map((item) => {
      const overdue = item.severity === "overdue";
      const label = overdue ? "overdue" : "due soon";
      return `<div class="calendar-reminder ${overdue ? "is-overdue" : ""}">
        <span class="calendar-reminder-badge">${escapeHtml(label)}</span>
        <span><strong>${escapeHtml(item.title || item.entity_id || "")}</strong> ${item.date ? "&middot; " + escapeHtml(item.date) : ""} (${escapeHtml(item.calendar_kind || "")})</span>
      </div>`;
    }).join("") : "";
  }

  const days = calendarVisibleDays();
  const header = CALENDAR_WEEKDAYS.map((name) => `<div class="calendar-weekday" role="columnheader">${escapeHtml(name)}</div>`).join("");
  const cells = days.map(({ date, outside }) => {
    const key = calendarDateKey(date);
    const events = byDate[key] || [];
    const isToday = key === todayKey;
    const eventHtml = events.map((event) => {
      const overdue = event.reminder === "overdue";
      const kindClass = `calendar-event-${(event.kind || "").replace(/[^a-z]/g, "")}`;
      return `<span class="calendar-event ${kindClass} ${overdue ? "is-overdue" : ""}" title="${escapeHtml(event.title || "")}" data-entity-id="${escapeHtml(event.id || "")}">${escapeHtml(event.title || "")}</span>`;
    }).join("");
    return `<div class="calendar-cell ${outside ? "is-outside" : ""} ${isToday ? "is-today" : ""}" role="gridcell">
      <span class="calendar-cell-date">${escapeHtml(date.getDate())}</span>
      ${eventHtml}
    </div>`;
  }).join("");
  grid.innerHTML = header + cells;
}

function renderSchedules() {
  const host = $("schedule-list");
  if (!host) return;
  const data = (runtimeState && runtimeState.schedules) || { schedules: [], totals: {} };
  const totals = data.totals || {};
  const summary = $("schedule-summary");
  if (summary) {
    summary.innerHTML = `<strong>${escapeHtml(totals.schedules || 0)}</strong> schedules`
      + ` &middot; active <strong>${escapeHtml(totals.active || 0)}</strong>`
      + ` &middot; reserve <strong>${escapeHtml(totals.reserve || 0)}</strong>`
      + ` &middot; repeat <strong>${escapeHtml(totals.repeat || 0)}</strong>`
      + ` &middot; proposal-only (local scheduler dispatches)`;
  }
  const schedules = data.schedules || [];
  host.innerHTML = schedules.length ? schedules.map((schedule) => {
    const invalid = (schedule.invalid || []).length > 0;
    const stateClass = invalid ? "is-invalid" : (schedule.active ? "is-active" : "is-inactive");
    const stateLabel = invalid ? "invalid" : (schedule.active ? "active" : "inactive");
    const cadence = schedule.mode === "repeat"
      ? `<span class="calendar-cron-badge">${escapeHtml(schedule.cron || "?")}</span>`
      : `<span>${escapeHtml(schedule.run_at || "?")}</span>`;
    return `
    <article class="config-card">
      <div class="config-card-header">
        <b>${escapeHtml(schedule.name || schedule.id)}</b>
        <span class="rule-state ${stateClass}">${escapeHtml(stateLabel)}</span>
      </div>
      <div class="rule-flow">
        <span class="rule-token">${escapeHtml(schedule.mode || "?")}</span>
        <span class="rule-flow-arrow" aria-hidden="true">&#8594;</span>
        ${cadence}
      </div>
      <div class="config-card-meta">
        <span>Taskset <strong>${escapeHtml(schedule.taskset_id || "?")}</strong></span>
        <span>Id <strong>${escapeHtml(schedule.id)}</strong></span>
        ${invalid ? `<span>Issue <strong>${escapeHtml((schedule.invalid || []).join("; "))}</strong></span>` : ""}
      </div>
      <div class="config-card-actions">
        <button class="config-action" type="button" onclick="cancelSchedule('${escapeHtml(schedule.id)}')">Cancel</button>
      </div>
    </article>`;
  }).join("") : `<div class="empty">No scheduled dispatches</div>`;
}

function cancelSchedule(scheduleId) {
  return sendJson("/api/commands", { type: "schedule.cancel", payload: { type: "schedule.cancel", target: scheduleId, payload: { actor: "ui" } } });
}

function renderAutomation() {
  const host = $("automation-list");
  if (!host) return;
  const data = (runtimeState && runtimeState.automation_rules) || { rules: [], totals: {} };
  const totals = data.totals || {};
  const summary = $("automation-summary");
  if (summary) {
    summary.innerHTML = `<strong>${escapeHtml(totals.rules || 0)}</strong> rules`
      + ` &middot; active <strong>${escapeHtml(totals.active || 0)}</strong>`
      + ` &middot; inactive <strong>${escapeHtml(totals.inactive || 0)}</strong>`
      + ` &middot; invalid <strong>${escapeHtml(totals.invalid || 0)}</strong>`
      + ` &middot; execution via gate chain (proposal-only CRUD)`;
  }
  const rules = data.rules || [];
  host.innerHTML = rules.length ? rules.map((rule) => {
    const invalid = (rule.invalid || []).length > 0;
    const stateClass = invalid ? "is-invalid" : (rule.active ? "is-active" : "is-inactive");
    const stateLabel = invalid ? "invalid" : (rule.active ? "active" : "inactive");
    return `
    <article class="config-card">
      <div class="config-card-header">
        <b>${escapeHtml(rule.name || rule.id)}</b>
        <span class="rule-state ${stateClass}">${escapeHtml(stateLabel)}</span>
      </div>
      ${rule.description ? `<div>${escapeHtml(rule.description)}</div>` : ""}
      <div class="rule-flow">
        <span class="rule-token">${escapeHtml((rule.trigger || "?").replace(/_/g, " "))}</span>
        <span class="rule-flow-arrow" aria-hidden="true">&#8594;</span>
        <span class="rule-token">${escapeHtml((rule.action || "?").replace(/_/g, " "))}</span>
      </div>
      <div class="config-card-meta">
        <span>Id <strong>${escapeHtml(rule.id)}</strong></span>
        <span>Source <strong>${escapeHtml(rule.source_path || "declarative file")}</strong></span>
        ${invalid ? `<span>Issue <strong>${escapeHtml((rule.invalid || []).join("; "))}</strong></span>` : ""}
      </div>
      <div class="config-card-actions">
        <button class="config-action" type="button" onclick="toggleAutomationRule('${escapeHtml(rule.id)}', ${rule.active ? "false" : "true"})">${rule.active ? "Deactivate" : "Activate"}</button>
        <button class="config-action" type="button" onclick="deleteAutomationRule('${escapeHtml(rule.id)}')">Delete</button>
      </div>
    </article>`;
  }).join("") : `<div class="empty">No automation rules</div>`;
}

function renderProperties() {
  const host = $("property-list");
  if (!host) return;
  const data = (runtimeState && runtimeState.custom_properties) || { definitions: [] };
  const defs = data.definitions || [];
  const summary = $("property-summary");
  if (summary) summary.innerHTML = `<strong>${escapeHtml(defs.length)}</strong> custom properties (text / select / number / date) extend task frontmatter`;
  host.innerHTML = defs.length ? defs.map((def) => `
    <article class="config-card">
      <div class="config-card-header">
        <b>${escapeHtml(def.label || def.key)}</b>
        <span class="state-chip">${escapeHtml(def.type)}</span>
      </div>
      <div class="config-card-meta">
        <span>Key <strong>${escapeHtml(def.key)}</strong></span>
        <span>Filterable <strong>${escapeHtml(def.filterable ? "yes" : "no")}</strong></span>
        ${(def.options || []).length ? `<span>Options <strong>${escapeHtml((def.options || []).join(", "))}</strong></span>` : ""}
      </div>
      <div class="config-card-actions">
        <button class="config-action" type="button" onclick="deleteProperty('${escapeHtml(def.key)}')">Delete</button>
      </div>
    </article>
  `).join("") : `<div class="empty">No custom properties</div>`;
}

function renderLabels() {
  const host = $("label-list");
  if (!host) return;
  const data = (runtimeState && runtimeState.labels) || { labels: [], totals: {}, color_tokens: LABEL_COLOR_TOKENS };
  const select = $("label-color");
  if (select && !select.dataset.populated) {
    const tokens = data.color_tokens || LABEL_COLOR_TOKENS;
    select.innerHTML = tokens.map((token) => `<option value="${escapeHtml(token)}">${escapeHtml(token)}</option>`).join("");
    select.dataset.populated = "1";
  }
  const totals = data.totals || {};
  const summary = $("label-summary");
  if (summary) summary.innerHTML = `<strong>${escapeHtml(totals.labels || 0)}</strong> labels &middot; defined <strong>${escapeHtml(totals.defined || 0)}</strong> &middot; in use <strong>${escapeHtml(totals.used || 0)}</strong>`;
  const labels = data.labels || [];
  host.innerHTML = labels.length ? labels.map((label) => `
    <article class="config-card">
      <div class="config-card-header">
        ${labelChip(label)}
        <span class="state-chip">${escapeHtml(label.usage_count || 0)} uses</span>
      </div>
      <div class="config-card-meta">
        <span>Color <strong>${escapeHtml(label.color_token)}</strong></span>
        <span>Defined <strong>${escapeHtml(label.defined ? "yes" : "tag-only")}</strong></span>
        ${label.description ? `<span>${escapeHtml(label.description)}</span>` : ""}
      </div>
      <div class="config-card-actions">
        <button class="config-action" type="button" onclick="deleteLabel('${escapeHtml(label.name)}')">Delete</button>
      </div>
    </article>
  `).join("") : `<div class="empty">No labels</div>`;
}

function toggleAutomationRule(ruleId, active) {
  return sendJson("/api/commands", { type: "automation.toggle", payload: { type: "automation.toggle", target: ruleId, payload: { actor: "ui", active } } });
}

function deleteAutomationRule(ruleId) {
  return sendJson("/api/commands", { type: "automation.delete", payload: { type: "automation.delete", target: ruleId, payload: { actor: "ui" } } });
}

function deleteProperty(key) {
  return sendJson("/api/commands", { type: "property.delete", payload: { type: "property.delete", target: key, payload: { actor: "ui" } } });
}

function deleteLabel(name) {
  return sendJson("/api/commands", { type: "label.delete", payload: { type: "label.delete", target: name, payload: { actor: "ui" } } });
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
  // Role badges drill down to the tasks assigned to that team/role (AR-337
  // org-chart drill-down). Clicking navigates to the board with the team filter
  // pre-applied so the org chart, heatmap and board all agree on the team.
  const badges = Object.keys(roles).map((role) =>
    `<button type="button" class="team-role-badge" data-drill-team="${escapeHtml(group.id)}" data-drill-role="${escapeHtml(role)}" title="Show ${escapeHtml(role)} tasks">${escapeHtml(role)} ${escapeHtml(roles[role])}</button>`
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

// AR-337: a role node (org chart) or a heatmap row drills down to the board
// filtered by that team/role. Single entry point keeps the team consistent.
function drillToTeamTasks(team, role) {
  if (!team && !role) return;
  setBoardTeamFilter(team || null, role || null);
  activateView("board");
}

function wireTeamDrilldown(host) {
  if (!host) return;
  host.querySelectorAll("[data-drill-team], [data-drill-role]").forEach((node) => {
    const team = node.dataset.drillTeam || null;
    const role = node.dataset.drillRole || null;
    if (!team && !role) return;
    node.addEventListener("click", () => drillToTeamTasks(team, role));
  });
}

function renderTeamAgents() {
  const host = $("team-org");
  if (!host) return;
  const data = teamAgentsData();
  const totals = data.totals || {};
  setText("team-summary", `${totals.teams ?? 0} teams - ${totals.agents ?? 0} agents - ${totals.online ?? 0} online`);
  const teams = data.teams || [];
  host.innerHTML = teams.length ? teams.map(teamGroupBlock).join("") : `<div class="empty">No teams</div>`;
  wireTeamDrilldown(host);
}

// ----- TASK-AR-337: workload heatmap (agent/team x period, overload/idle) -----
let workloadScope = "agents";

function workloadData() {
  return (runtimeState && runtimeState.workload) || { agents: [], teams: [], periods: [], totals: {}, bands: [] };
}

function workloadCell(cell, rowId, rowKind) {
  // Intensity is applied ONLY as opacity via the inline --cell-intensity custom
  // property; the fill color is always the band token (no raw rgba from JS).
  const intensity = Math.max(0, Math.min(1, Number(cell.intensity) || 0));
  const band = String(cell.band || "idle");
  const count = Number(cell.load) || 0;
  const title = `${escapeHtml(rowId)} - ${escapeHtml(cell.period)}: ${escapeHtml(count)} open (${escapeHtml(band)})`;
  const drill = rowKind === "team"
    ? `data-drill-team="${escapeHtml(rowId)}"`
    : `data-drill-role="${escapeHtml(rowId)}"`;
  return `<button type="button" class="workload-cell band-${escapeHtml(band)}" style="--cell-intensity: ${intensity}" ` +
    `${drill} data-wl-period="${escapeHtml(cell.period)}" title="${title}" aria-label="${title}">` +
    `<span class="heat-fill" aria-hidden="true"></span><span class="heat-count">${escapeHtml(count)}</span></button>`;
}

function workloadRow(row, periods) {
  const cells = periods.map((period) => {
    const cell = (row.cells || []).find((item) => item.period === period) || { period, load: 0, band: "idle", intensity: 0 };
    return workloadCell(cell, row.id, row.kind);
  }).join("");
  const drill = row.kind === "team"
    ? `data-drill-team="${escapeHtml(row.id)}"`
    : `data-drill-role="${escapeHtml(row.id)}"`;
  return `<div class="workload-row">` +
    `<button type="button" class="workload-label" ${drill} title="Show ${escapeHtml(row.id)} tasks">` +
    `${escapeHtml(row.id)}<small>${escapeHtml(row.open_total ?? 0)} open - peak ${escapeHtml(row.peak_band || "idle")}</small></button>` +
    `<div class="workload-cells">${cells}</div></div>`;
}

function renderWorkloadLegend(bands) {
  const host = $("workload-legend");
  if (!host) return;
  const list = (bands && bands.length) ? bands : ["idle", "normal", "busy", "overload"];
  host.innerHTML = list.map((band) =>
    `<li><span class="heat-swatch band-${escapeHtml(band)}"></span>${escapeHtml(band)}</li>`
  ).join("");
}

function renderWorkloadHeatmap() {
  const grid = $("workload-grid");
  if (!grid) return;
  const data = workloadData();
  const totals = data.totals || {};
  setText("workload-summary",
    `${totals.open_tasks ?? 0} open - ${totals.overloaded ?? 0} overloaded - ${totals.idle ?? 0} idle`);
  renderWorkloadLegend(data.bands);
  const periods = data.periods || [];
  const rows = workloadScope === "teams" ? (data.teams || []) : (data.agents || []);
  if (!rows.length) {
    grid.innerHTML = `<div class="workload-empty">No workload data</div>`;
    return;
  }
  const headCells = periods.map((period) =>
    `<span class="workload-cell is-head">${escapeHtml(period)}</span>`
  ).join("");
  const head = `<div class="workload-row is-head"><span class="workload-label">${escapeHtml(workloadScope === "teams" ? "Team" : "Agent")}</span><div class="workload-cells">${headCells}</div></div>`;
  grid.innerHTML = head + rows.map((row) => workloadRow(row, periods)).join("");
  wireTeamDrilldown(grid);
}

function setWorkloadScope(scope) {
  workloadScope = scope === "teams" ? "teams" : "agents";
  const agentsBtn = $("workload-scope-agents");
  const teamsBtn = $("workload-scope-teams");
  if (agentsBtn) {
    agentsBtn.classList.toggle("is-active", workloadScope === "agents");
    agentsBtn.setAttribute("aria-selected", workloadScope === "agents" ? "true" : "false");
  }
  if (teamsBtn) {
    teamsBtn.classList.toggle("is-active", workloadScope === "teams");
    teamsBtn.setAttribute("aria-selected", workloadScope === "teams" ? "true" : "false");
  }
  renderWorkloadHeatmap();
}

// ----- TASK-AR-339: ops dashboard (token/cost, eval, gates, burndown) -----
// Read-only render over runtimeState.ops_metrics. Charts are inline SVG or
// token-styled divs so they retheme automatically; all classes carry color via
// CSS var(--token), never a literal color from JS. Every rendered field is
// escapeHtml'd. Strings are ASCII-only to satisfy the cp949 node-check guard.
function opsMetricsData() {
  return (runtimeState && runtimeState.ops_metrics) || {
    resources: { tasksets: [], tasks: [] },
    eval_trend: { points: [], available: false },
    gates: { gates: [], counts: {}, total: 0 },
    burndown: { tasksets: [] },
    velocity: { weeks: [], available: false },
  };
}

function opsFormatTokens(value) {
  const n = Number(value) || 0;
  if (n >= 1000000) return (n / 1000000).toFixed(2) + "M";
  if (n >= 1000) return (n / 1000).toFixed(1) + "k";
  return String(n);
}

function opsFormatCost(value) {
  return "$" + (Number(value) || 0).toFixed(2);
}

function renderOpsResources(data) {
  const host = $("opsdash-tokens");
  if (!host) return;
  const res = data.resources || {};
  setText("opsdash-tokens-meta", `${res.actuals_label || "estimate-only"} - ` +
    `${opsFormatTokens(res.est_tokens)} est tokens`);
  const totals =
    `<div class="opsdash-totals">` +
    `<div class="opsdash-stat"><b>${escapeHtml(opsFormatTokens(res.est_tokens))}</b><span>est tokens</span></div>` +
    `<div class="opsdash-stat"><b>${escapeHtml(opsFormatTokens(res.actual_tokens))}</b><span>actual tokens</span></div>` +
    `<div class="opsdash-stat"><b>${escapeHtml(opsFormatCost(res.est_cost))}</b><span>est cost</span></div>` +
    `<div class="opsdash-stat"><b>${escapeHtml(opsFormatCost(res.actual_cost))}</b><span>actual cost</span></div>` +
    `</div>`;
  const rows = (res.tasksets || []).slice(0, 8);
  if (!rows.length) {
    host.innerHTML = totals + `<div class="opsdash-empty">No token estimates recorded</div>`;
    return;
  }
  const maxEst = Math.max(1, ...rows.map((r) => Number(r.est_tokens) || 0));
  const bars = rows.map((row) => {
    const est = Number(row.est_tokens) || 0;
    const actual = Number(row.actual_tokens) || 0;
    // The est bar scales tokens against the largest taskset; the actual bar is
    // the consumed fraction of that taskset's own estimate (capped at est).
    const estPct = Math.max(0, Math.min(100, (est / maxEst) * 100));
    const actualWidth = est ? Math.max(0, Math.min(estPct, (actual / est) * estPct)) : 0;
    const over = row.over_budget ? " is-over" : "";
    const consumed = (row.consumed_pct === null || row.consumed_pct === undefined)
      ? "est-only"
      : `${escapeHtml(row.consumed_pct)}% used`;
    const name = escapeHtml(row.display_name || row.task_set_id || "");
    return `<div class="opsdash-bar-row">` +
      `<div class="opsdash-bar-label"><span>${name}</span>` +
      `<small>${escapeHtml(opsFormatTokens(est))} est - ${consumed}</small></div>` +
      `<div class="opsdash-bar-track" role="img" aria-label="${name}: ${escapeHtml(opsFormatTokens(est))} estimated tokens">` +
      `<div class="opsdash-bar-est" style="width: ${estPct.toFixed(1)}%"></div>` +
      `<div class="opsdash-bar-actual${over}" style="width: ${actualWidth.toFixed(1)}%"></div>` +
      `</div></div>`;
  }).join("");
  host.innerHTML = totals + bars;
  const src = $("opsdash-tokens-src");
  if (src) src.hidden = true;
}

function renderOpsEvalTrend(data) {
  const host = $("opsdash-eval");
  if (!host) return;
  const trend = data.eval_trend || {};
  const points = trend.points || [];
  if (!points.length) {
    setText("opsdash-eval-meta", "no eval evidence");
    host.innerHTML = `<div class="opsdash-empty">No eval evidence found</div>`;
    return;
  }
  setText("opsdash-eval-meta",
    `${trend.count || points.length} runs - latest ${escapeHtml(String(trend.latest_score))}`);
  // Inline SVG line chart. Y axis fixed to 0..1 (scores are ratios). Stroke and
  // dot fills come from token-backed CSS classes (no literal color here).
  const W = 300;
  const H = 120;
  const padL = 26;
  const padB = 16;
  const padT = 8;
  const innerW = W - padL - 6;
  const innerH = H - padB - padT;
  const n = points.length;
  const xFor = (i) => padL + (n <= 1 ? innerW / 2 : (i / (n - 1)) * innerW);
  const yFor = (score) => padT + (1 - Math.max(0, Math.min(1, Number(score) || 0))) * innerH;
  const linePts = points.map((p, i) => `${xFor(i).toFixed(1)},${yFor(p.score).toFixed(1)}`).join(" ");
  const gridY = [0, 0.5, 1].map((v) => {
    const y = yFor(v).toFixed(1);
    return `<line class="opsdash-grid-line" x1="${padL}" y1="${y}" x2="${W - 6}" y2="${y}"></line>` +
      `<text class="opsdash-axis" x="2" y="${(Number(y) + 3).toFixed(1)}">${v}</text>`;
  }).join("");
  const dots = points.map((p, i) => {
    const cls = p.status === "block" ? " is-block" : (p.status === "watch" ? " is-watch" : "");
    const label = `${escapeHtml(p.id)}: ${escapeHtml(String(p.score))}`;
    return `<circle class="opsdash-dot${cls}" cx="${xFor(i).toFixed(1)}" cy="${yFor(p.score).toFixed(1)}" r="3">` +
      `<title>${label}</title></circle>`;
  }).join("");
  host.innerHTML =
    `<svg class="opsdash-chart" viewBox="0 0 ${W} ${H}" role="img" ` +
    `aria-label="Eval score trend, ${escapeHtml(String(trend.count || n))} runs">` +
    gridY +
    `<polyline class="opsdash-line" points="${linePts}"></polyline>` +
    dots +
    `</svg>`;
}

function renderOpsGateBoard(data) {
  const host = $("opsdash-gates");
  if (!host) return;
  const board = data.gates || {};
  const counts = board.counts || {};
  const gates = board.gates || [];
  setText("opsdash-gates-meta", `${board.total || gates.length} gates - ${counts.block || 0} blocking`);
  if (!gates.length) {
    host.innerHTML = `<div class="opsdash-empty">No gate records found</div>`;
    return;
  }
  const countsRow =
    `<div class="opsdash-gate-counts">` +
    ["pass", "watch", "block"].map((status) =>
      `<div class="opsdash-gate-count is-${status}"><b>${escapeHtml(counts[status] || 0)}</b><span>${escapeHtml(status)}</span></div>`
    ).join("") +
    `</div>`;
  const items = gates.slice(0, 30).map((gate) => {
    const status = ["pass", "watch", "block"].indexOf(gate.status) >= 0 ? gate.status : "";
    const ref = gate.task_ref ? `<span class="opsdash-gate-ref">${escapeHtml(gate.task_ref)}</span>` : "";
    return `<li class="opsdash-gate-item">` +
      `<span class="opsdash-gate-dot is-${escapeHtml(status)}" aria-hidden="true"></span>` +
      `<span class="opsdash-gate-name" title="${escapeHtml(gate.id)}">${escapeHtml(gate.kind || gate.id)}</span>` +
      ref +
      `<span class="opsdash-gate-ref">${escapeHtml(gate.status)}</span>` +
      `</li>`;
  }).join("");
  host.innerHTML = countsRow + `<ul class="opsdash-gate-list">${items}</ul>`;
}

function renderOpsBurndown(data) {
  const burnHost = $("opsdash-burndown");
  const velHost = $("opsdash-velocity");
  const burn = data.burndown || {};
  const vel = data.velocity || {};
  if (burnHost) {
    setText("opsdash-burndown-meta",
      `${burn.done || 0}/${burn.total || 0} done - ${escapeHtml(String(burn.pct_done || 0))}%`);
    const rows = (burn.tasksets || []).filter((r) => Number(r.total) > 0).slice(0, 8);
    if (!rows.length) {
      burnHost.innerHTML = `<div class="opsdash-empty">No taskset progress</div>`;
    } else {
      const bars = rows.map((row) => {
        const name = escapeHtml(row.display_name || row.task_set_id || "");
        const label = `${escapeHtml(row.done)}/${escapeHtml(row.total)} done`;
        return `<div class="opsdash-bar-row">` +
          `<div class="opsdash-bar-label"><span>${name}</span><small>${label}</small></div>` +
          progressBar(row.pct_done) +
          `</div>`;
      }).join("");
      burnHost.innerHTML = `<div class="opsdash-burndown-bars">${bars}</div>`;
    }
  }
  if (velHost) {
    const weeks = vel.weeks || [];
    if (!weeks.length) {
      velHost.innerHTML = `<div class="opsdash-velocity-head">Weekly velocity</div>` +
        `<div class="opsdash-empty">No completion history</div>`;
      return;
    }
    const peak = Math.max(1, ...weeks.map((w) => Number(w.done) || 0));
    const bars = weeks.map((w) => {
      const h = Math.max(2, Math.round(((Number(w.done) || 0) / peak) * 70));
      const wk = String(w.week || "").slice(5);
      return `<div class="opsdash-vbar" title="${escapeHtml(w.week)}: ${escapeHtml(w.done)} done">` +
        `<span class="opsdash-vbar-count">${escapeHtml(w.done)}</span>` +
        `<span class="opsdash-vbar-fill" style="height: ${h}px"></span>` +
        `<span class="opsdash-vbar-label">${escapeHtml(wk)}</span>` +
        `</div>`;
    }).join("");
    velHost.innerHTML = `<div class="opsdash-velocity-head">Weekly velocity - ` +
      `avg ${escapeHtml(String(vel.avg_per_week || 0))}/wk, peak ${escapeHtml(String(vel.peak_week || 0))}</div>` +
      `<div class="opsdash-velocity-bars">${bars}</div>`;
  }
}

function renderOpsDashboard() {
  if (!$("opsdash-tokens")) return;
  const data = opsMetricsData();
  const res = data.resources || {};
  const board = data.gates || {};
  const trend = data.eval_trend || {};
  setText("opsdash-summary",
    `${res.task_count || 0} tasks tracked - ${opsFormatTokens(res.est_tokens)} est tokens - ` +
    `${(board.counts && board.counts.block) || 0} blocking gates - ` +
    `eval ${trend.available ? trend.latest_score : "n/a"}`);
  renderOpsResources(data);
  renderOpsEvalTrend(data);
  renderOpsGateBoard(data);
  renderOpsBurndown(data);
}

// ----- TASK-AR-332: file attachments (drag/drop + paste, preview, lightbox) -----
const ATTACH_MAX_BYTES = 5 * 1024 * 1024;
const ATTACH_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "text/plain", "text/markdown", "text/x-markdown", "application/pdf"];

function attachExtBadge(item) {
  const name = String(item.filename || "");
  const dot = name.lastIndexOf(".");
  const ext = dot >= 0 ? name.slice(dot + 1) : (item.content_type || "file");
  return escapeHtml(ext.slice(0, 4));
}

function formatBytes(value) {
  const n = Number(value || 0);
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

function attachmentItemTemplate(item) {
  // filename / metadata are user-controlled => escapeHtml everything rendered.
  const url = escapeHtml(item.download_url || `/api/attachments/${encodeURIComponent(item.id)}/download`);
  const name = escapeHtml(item.filename || "attachment");
  const id = escapeHtml(item.id || "");
  const thumb = item.is_image
    ? `<img class="attach-thumb" src="${url}" alt="${name}" data-attach-zoom="${url}" data-attach-alt="${name}">`
    : `<span class="attach-icon" aria-hidden="true">${attachExtBadge(item)}</span>`;
  const previewBtn = (item.is_text || item.is_image)
    ? `<button type="button" class="attach-preview-btn" data-attach-preview="${id}">Preview</button>`
    : "";
  return `<li class="attach-item" data-attach-id="${id}">
    ${thumb}
    <span class="attach-body">
      <span class="attach-name">${name}</span>
      <span class="attach-meta">${escapeHtml(item.content_type || "")} | ${escapeHtml(formatBytes(item.size_bytes))}</span>
    </span>
    <span class="attach-actions">
      ${previewBtn}
      <a href="${url}" download="${name}">Download</a>
    </span>
  </li>`;
}

function attachmentsSection(task) {
  const items = task.attachments || [];
  const list = items.length
    ? `<ul class="attach-list">${items.map(attachmentItemTemplate).join("")}</ul>`
    : `<div class="empty">No attachments yet</div>`;
  return `<section class="attachments" id="attachments-section">
    <div class="attachments-title">Attachments (${items.length})</div>
    <div id="attach-dropzone" class="attach-dropzone" tabindex="0" role="button" aria-label="Attach files: drop, paste, or click to browse">
      Drop files, paste a screenshot, or click to browse
      <span class="attach-hint">images / md / text / pdf, up to ${formatBytes(ATTACH_MAX_BYTES)}</span>
      <input id="attach-input" type="file" multiple hidden accept="image/*,text/plain,text/markdown,.md,.markdown,application/pdf">
    </div>
    <div id="attach-error" class="attach-error" hidden></div>
    <div id="attach-preview" class="attach-preview" hidden></div>
    ${list}
  </section>`;
}

function attachError(message) {
  const node = $("attach-error");
  if (!node) return;
  node.textContent = message || "";
  node.hidden = !message;
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = () => reject(reader.error || new Error("read failed"));
    reader.readAsDataURL(file);
  });
}

async function uploadAttachment(task, file) {
  const type = (file.type || "").split(";")[0].trim().toLowerCase();
  if (!ATTACH_TYPES.includes(type)) {
    attachError(`Unsupported type: ${type || "unknown"}`);
    return;
  }
  if (file.size > ATTACH_MAX_BYTES) {
    attachError(`Too large: ${formatBytes(file.size)} (max ${formatBytes(ATTACH_MAX_BYTES)})`);
    return;
  }
  attachError("");
  let content_b64;
  try {
    content_b64 = await readFileAsBase64(file);
  } catch (error) {
    attachError(`Read failed: ${error.message}`);
    return;
  }
  const response = await fetch("/api/attachments", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      filename: file.name || "pasted-image.png",
      content_type: type,
      content_b64,
      task_id: task.id,
      actor: "ui",
    }),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.status === "failed") {
    attachError((payload.errors || ["upload failed"]).join("; "));
    return;
  }
  await loadState();
}

async function uploadFiles(task, files) {
  for (const file of Array.from(files || [])) {
    await uploadAttachment(task, file);
  }
}

function openAttachLightbox(url, alt) {
  closeAttachLightbox();
  const box = document.createElement("div");
  box.className = "attach-lightbox";
  box.id = "attach-lightbox";
  box.innerHTML = `<button type="button" class="attach-lightbox-close" aria-label="Close">&times;</button><img src="${escapeHtml(url)}" alt="${escapeHtml(alt || "attachment")}">`;
  box.addEventListener("click", (event) => {
    if (event.target === box || event.target.classList.contains("attach-lightbox-close")) closeAttachLightbox();
  });
  document.body.appendChild(box);
}

function closeAttachLightbox() {
  const box = $("attach-lightbox");
  if (box) box.remove();
}

async function showAttachPreview(item) {
  const node = $("attach-preview");
  if (!node) return;
  if (item.is_image) {
    openAttachLightbox(item.download_url, item.filename);
    return;
  }
  try {
    const response = await fetch(item.download_url, { cache: "no-store" });
    const text = await response.text();
    node.textContent = text.slice(0, 20000);
    node.hidden = false;
  } catch (error) {
    attachError(`Preview failed: ${error.message}`);
  }
}

function bindAttachments(task) {
  const zone = $("attach-dropzone");
  const input = $("attach-input");
  if (!zone || !input) return;
  zone.addEventListener("click", () => input.click());
  zone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") { event.preventDefault(); input.click(); }
  });
  input.addEventListener("change", () => uploadFiles(task, input.files));
  zone.addEventListener("dragover", (event) => { event.preventDefault(); zone.classList.add("is-dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("is-dragover"));
  zone.addEventListener("drop", (event) => {
    event.preventDefault();
    zone.classList.remove("is-dragover");
    if (event.dataTransfer && event.dataTransfer.files) uploadFiles(task, event.dataTransfer.files);
  });
  zone.addEventListener("paste", (event) => {
    const items = (event.clipboardData && event.clipboardData.items) || [];
    const files = [];
    for (const it of items) {
      if (it.kind === "file") { const f = it.getAsFile(); if (f) files.push(f); }
    }
    if (files.length) { event.preventDefault(); uploadFiles(task, files); }
  });
  const section = $("attachments-section");
  if (section) {
    section.querySelectorAll("[data-attach-zoom]").forEach((img) => {
      img.addEventListener("click", () => openAttachLightbox(img.dataset.attachZoom, img.dataset.attachAlt));
    });
    section.querySelectorAll("[data-attach-preview]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const item = (task.attachments || []).find((a) => a.id === btn.dataset.attachPreview);
        if (item) showAttachPreview(item);
      });
    });
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
        <button id="view-state-machine" type="button">View in state machine</button>
      </div>
      <textarea id="detail-comment" placeholder="Comment or message"></textarea>
      <button id="send-comment" type="button">Send Comment</button>
    </form>
    ${attachmentsSection(task)}
  </article>`;
  bindAttachments(task);
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
  $("view-state-machine")?.addEventListener("click", () => viewTaskInStateMachine(task.id));
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
  renderWorkloadHeatmap();
  renderOpsDashboard();
  renderAgents();
  renderChannels();
  renderMessages();
  renderEvents();
  renderEvidence();
  renderPlanning();
  renderRoadmapTimeline();
  renderTimeline();
  renderDependencyGraph();
  renderMap();
  renderStateMachineViewer();
  renderSources();
  renderCommands();
  renderTriage();
  renderCalendar();
  renderSchedules();
  renderAutomation();
  renderProperties();
  renderLabels();
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

function parseHash() {
  // Hash shape: #/<route>?select=<entityId>  (AR-321 routing + AR-334 select).
  const raw = (window.location.hash || "").replace(/^#\/?/, "");
  if (!raw) return { route: null, select: null };
  const [routePart, queryPart] = raw.split("?");
  let select = null;
  if (queryPart) {
    try {
      select = new URLSearchParams(queryPart).get("select");
    } catch (error) { select = null; }
  }
  return { route: viewForRoute(routePart) ? routePart : null, select };
}

function routeFromHash() {
  return parseHash().route;
}

// Deep-link selection: highlight + scroll the entity identified in the hash
// (TASK-AR-334). Used after a search/quick-open result navigates to a view.
function selectEntityFromHash(select) {
  if (!select) return;
  const apply = () => {
    const safe = (window.CSS && CSS.escape) ? CSS.escape(select) : select.replace(/"/g, '\\"');
    const node = document.querySelector(`[data-task-id="${safe}"], [data-entity-id="${safe}"], [data-peek-task="${safe}"], [data-taskset-id="${safe}"]`);
    if (node) {
      document.querySelectorAll(".is-deeplinked").forEach((el) => el.classList.remove("is-deeplinked"));
      node.classList.add("is-deeplinked");
      node.scrollIntoView({ block: "center", behavior: "smooth" });
      if (typeof node.focus === "function") node.focus({ preventScroll: true });
    }
  };
  // Defer one frame so the activated view has rendered its rows.
  if (window.requestAnimationFrame) window.requestAnimationFrame(apply);
  else setTimeout(apply, 0);
}

function applyHashRoute() {
  const { route, select } = parseHash();
  const view = route ? viewForRoute(route) : "board";
  activateView(view || "board", { updateHash: false });
  selectEntityFromHash(select);
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

function eventTargetIsTextInput(event) {
  const tag = (event.target && event.target.tagName ? event.target.tagName : "").toLowerCase();
  return tag === "input" || tag === "textarea" || tag === "select" || (event.target && event.target.isContentEditable);
}

document.addEventListener("keydown", (event) => {
  // Command palette toggle (Ctrl+K / Cmd+K). Distinct from Ctrl+P quick open.
  if ((event.ctrlKey || event.metaKey) && (event.key === "k" || event.key === "K")) {
    event.preventDefault();
    if (quickOpenIsOpen()) closeQuickOpen();
    if (paletteIsOpen()) closeCommandPalette();
    else openCommandPalette();
    return;
  }
  // Quick open toggle (Ctrl+P / Cmd+P) - entities, NOT the command palette.
  // The Ctrl/Cmd modifier requirement means a plain "p" while typing in an
  // input is never intercepted here; single-key nav (j/k) is separately gated
  // by eventTargetIsTextInput in handleListKeyboardNav. It is a different key
  // from Ctrl+K so the two overlays never collide.
  if ((event.ctrlKey || event.metaKey) && (event.key === "p" || event.key === "P")) {
    event.preventDefault();
    if (paletteIsOpen()) closeCommandPalette();
    if (quickOpenIsOpen()) closeQuickOpen();
    else openQuickOpen();
    return;
  }
  if (quickOpenIsOpen()) {
    if (event.key === "Escape") {
      event.preventDefault();
      closeQuickOpen();
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      quickOpenActiveIndex += 1;
      renderQuickOpen();
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      quickOpenActiveIndex = Math.max(0, quickOpenActiveIndex - 1);
      renderQuickOpen();
    } else if (event.key === "Enter") {
      event.preventDefault();
      navigateToResult(quickOpenCurrentItems()[quickOpenActiveIndex]);
    }
    return;
  }
  // Global search box keyboard navigation (when its dropdown is open and the
  // search input itself has focus - never steals keys from other inputs).
  if (globalSearchOpen() && event.target === $("global-search-input")) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      searchActiveIndex += 1;
      renderGlobalSearchResults($("global-search-input").value.trim());
      return;
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      searchActiveIndex = Math.max(0, searchActiveIndex - 1);
      renderGlobalSearchResults($("global-search-input").value.trim());
      return;
    } else if (event.key === "Enter") {
      event.preventDefault();
      navigateToResult(searchResults[searchActiveIndex]);
      return;
    } else if (event.key === "Escape") {
      closeGlobalSearch();
      return;
    }
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
  if (event.key === "Escape" && $("attach-lightbox")) {
    closeAttachLightbox();
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

// Global search + quick open interaction wiring (TASK-AR-334).
(() => {
  const input = $("global-search-input");
  if (input) {
    input.addEventListener("input", () => {
      searchActiveIndex = 0;
      if (searchDebounce) clearTimeout(searchDebounce);
      searchDebounce = setTimeout(runGlobalSearch, 140);
    });
    input.addEventListener("focus", () => {
      if (input.value.trim() && searchResults.length) renderGlobalSearchResults(input.value.trim());
    });
  }
  const box = $("global-search-results");
  if (box) {
    box.addEventListener("click", (event) => {
      const row = event.target.closest(".search-result");
      if (!row) return;
      navigateToResult(searchResults[Number(row.dataset.resultIndex) || 0]);
    });
  }
  // Click outside the search box closes the dropdown.
  document.addEventListener("click", (event) => {
    const wrap = document.querySelector(".topbar-search");
    if (wrap && !wrap.contains(event.target)) closeGlobalSearch();
  });

  const overlay = $("quick-open");
  if (overlay) {
    const qinput = $("quick-open-input");
    if (qinput) {
      qinput.addEventListener("input", () => {
        quickOpenActiveIndex = 0;
        if (quickOpenDebounce) clearTimeout(quickOpenDebounce);
        quickOpenDebounce = setTimeout(runQuickOpenSearch, 140);
      });
    }
    overlay.addEventListener("click", (event) => {
      if (event.target.dataset.quickopenDismiss) { closeQuickOpen(); return; }
      const row = event.target.closest(".search-result");
      if (row) navigateToResult(quickOpenCurrentItems()[Number(row.dataset.resultIndex) || 0]);
    });
  }
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
$("taskset-create-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("taskset-new-name")?.value.trim() || "";
  if (!name) return;
  const summary = $("taskset-new-summary")?.value.trim() || "";
  await submitTasksetCreate(name, summary);
  if ($("taskset-new-name")) $("taskset-new-name").value = "";
  if ($("taskset-new-summary")) $("taskset-new-summary").value = "";
});
$("taskset-bulk-apply")?.addEventListener("click", applyBulkEdit);
$("taskset-bulk-clear")?.addEventListener("click", clearBulkSelection);
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
$("state-machine-select")?.addEventListener("change", (event) => {
  selectedStateMachineId = event.target.value || null;
  // Switching machines drops a task overlay that may not apply to the new one.
  selectedStateMachineTaskId = null;
  renderStateMachineViewer();
});
$("state-machine-task-select")?.addEventListener("change", (event) => {
  selectedStateMachineTaskId = event.target.value || null;
  renderStateMachineViewer();
});
$("workload-scope-agents")?.addEventListener("click", () => setWorkloadScope("agents"));
$("workload-scope-teams")?.addEventListener("click", () => setWorkloadScope("teams"));
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
// ----- TASK-AR-331: triage filters + property/label/automation CRUD forms -----
["triage-filter", "triage-reason-filter"].forEach((id) => {
  const node = $(id);
  if (node) {
    node.addEventListener("input", renderTriage);
    node.addEventListener("change", renderTriage);
  }
});
$("automation-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const trigger = $("automation-trigger").value;
  const action = $("automation-action").value;
  const paramRaw = ($("automation-param").value || "").trim();
  const params = {};
  if (paramRaw) {
    if (trigger === "status_change") params.status = paramRaw;
    else if (trigger === "blocked_too_long") params.days = Number(paramRaw) || paramRaw;
    if (action === "label_apply") params.label = paramRaw;
  }
  await sendJson("/api/commands", {
    type: "automation.create",
    payload: {
      type: "automation.create",
      payload: { actor: "ui", name: $("automation-name").value, trigger, action, params, active: true },
    },
  });
  $("automation-name").value = "";
  $("automation-param").value = "";
});
$("property-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const options = ($("property-options").value || "").split(",").map((value) => value.trim()).filter(Boolean);
  await sendJson("/api/commands", {
    type: "property.create",
    payload: {
      type: "property.create",
      payload: { actor: "ui", key: $("property-key").value, label: $("property-label").value, type: $("property-type").value, options },
    },
  });
  $("property-key").value = "";
  $("property-label").value = "";
  $("property-options").value = "";
});
$("label-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendJson("/api/commands", {
    type: "label.create",
    payload: {
      type: "label.create",
      payload: { actor: "ui", name: $("label-name").value, color: $("label-color").value, description: $("label-description").value },
    },
  });
  $("label-name").value = "";
  $("label-description").value = "";
});

// ----- Calendar / scheduling listeners (TASK-AR-335) -----
$("calendar-prev")?.addEventListener("click", () => calendarShift(calendarMode === "week" ? -7 : 0, calendarMode === "week" ? 0 : -1));
$("calendar-next")?.addEventListener("click", () => calendarShift(calendarMode === "week" ? 7 : 0, calendarMode === "week" ? 0 : 1));
$("calendar-today")?.addEventListener("click", () => { calendarAnchor = calendarToday(); renderCalendar(); });
$("calendar-view-month")?.addEventListener("click", () => { calendarMode = "month"; renderCalendar(); });
$("calendar-view-week")?.addEventListener("click", () => { calendarMode = "week"; renderCalendar(); });
$("schedule-mode")?.addEventListener("change", (event) => {
  const repeat = event.target.value === "repeat";
  const runAt = $("schedule-runat");
  const cron = $("schedule-cron");
  if (runAt) runAt.hidden = repeat;
  if (cron) cron.hidden = !repeat;
});
$("schedule-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const mode = $("schedule-mode").value;
  const payload = { actor: "ui", name: $("schedule-name").value, taskset_id: $("schedule-taskset").value, mode };
  if (mode === "repeat") payload.cron = ($("schedule-cron").value || "").trim();
  else payload.run_at = ($("schedule-runat").value || "").trim();
  await sendJson("/api/commands", { type: "schedule.create", payload: { type: "schedule.create", payload } });
  $("schedule-name").value = "";
  $("schedule-taskset").value = "";
  $("schedule-runat").value = "";
  $("schedule-cron").value = "";
});

// ----- Import/Export (TASK-AR-333) -----
// Import is preview-first: parse + duplicate-check server-side, render an
// advisory preview, then commit creates task.create proposals only.
let importPreviewState = null;

function renderImportPreview(preview) {
  importPreviewState = preview;
  const host = $("import-preview");
  const summary = $("import-summary");
  const commitBtn = $("import-commit-btn");
  const counts = (preview && preview.counts) || { total: 0, new: 0, duplicate: 0, invalid: 0 };
  if (summary) {
    summary.innerHTML = `<strong>${escapeHtml(counts.total)}</strong> rows`
      + ` &middot; new <strong>${escapeHtml(counts.new)}</strong>`
      + ` &middot; duplicate <strong>${escapeHtml(counts.duplicate)}</strong>`
      + ` &middot; invalid <strong>${escapeHtml(counts.invalid)}</strong>`;
  }
  if (commitBtn) commitBtn.disabled = !(counts.new > 0);
  const items = (preview && preview.items) || [];
  if (!host) return;
  host.innerHTML = items.length ? items.map((item) => {
    const invalid = (item.errors || []).length > 0;
    const badgeClass = invalid ? "is-invalid" : (item.duplicate ? "is-duplicate" : "is-new");
    const badgeLabel = invalid ? "invalid" : (item.duplicate ? "duplicate" : "new");
    const reasons = invalid ? (item.errors || []) : (item.duplicate_reasons || []);
    return `<div class="portability-row">
      <span class="portability-badge ${badgeClass}">${escapeHtml(badgeLabel)}</span>
      <span class="portability-row-title">${escapeHtml(item.title || "(no title)")}</span>
      ${item.id ? `<span class="portability-row-id">${escapeHtml(item.id)}</span>` : ""}
      ${reasons.length ? `<span class="portability-row-reason">${escapeHtml(reasons.join("; "))}</span>` : ""}
    </div>`;
  }).join("") : `<div class="empty">No rows parsed</div>`;
}

async function requestImportPreview() {
  const format = $("import-format").value;
  const content = $("import-content").value;
  const response = await fetch("/api/import/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, content }),
  });
  const payload = await response.json();
  if (!response.ok) {
    const summary = $("import-summary");
    if (summary) summary.innerHTML = `<strong>Preview failed:</strong> ${escapeHtml((payload.errors || ["unknown error"]).join("; "))}`;
    return;
  }
  renderImportPreview(payload);
}

async function commitImport() {
  if (!importPreviewState) return;
  const format = $("import-format").value;
  const content = $("import-content").value;
  const commitBtn = $("import-commit-btn");
  if (commitBtn) commitBtn.disabled = true;
  const response = await fetch("/api/import/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format, content }),
  });
  const payload = await response.json();
  const summary = $("import-summary");
  if (summary) {
    const counts = (payload && payload.counts) || { created: 0, skipped: 0 };
    summary.innerHTML = `Committed: created <strong>${escapeHtml(counts.created)}</strong>`
      + ` &middot; skipped <strong>${escapeHtml(counts.skipped)}</strong>`
      + ` (task.create proposals)`;
  }
  importPreviewState = null;
  await loadState();
}

$("import-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  await requestImportPreview();
});
$("import-commit-btn")?.addEventListener("click", async (event) => {
  event.preventDefault();
  await commitImport();
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


def _attachment_upload_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    """Validate + persist an uploaded attachment, returning the evidence record."""
    try:
        data = ui_state.decode_attachment_payload(payload.get("content_b64") or payload.get("content"))
        record = ui_state.save_attachment(
            root_path,
            filename=payload.get("filename"),
            content_type=payload.get("content_type"),
            data=data,
            task_id=payload.get("task_id"),
            message_id=payload.get("message_id"),
            actor=payload.get("actor"),
        )
    except ui_state.AttachmentError as exc:
        return _json_response({"status": "failed", "errors": [str(exc)]}, status=400)
    return _json_response({"status": "accepted", "attachment": record}, status=201)


def _attachment_download_id(request_path: str) -> str | None:
    parts = [part for part in request_path.split("/") if part]
    if len(parts) == 4 and parts[:2] == ["api", "attachments"] and parts[3] == "download":
        return parts[2]
    return None


def _attachment_download_response(root_path: Path, attachment_id: str) -> ConsoleResponse:
    result = ui_state.read_attachment_blob(root_path, attachment_id)
    if result is None:
        return ConsoleResponse(404, "text/plain; charset=utf-8", b"not found\n")
    body, content_type, _filename = result
    return ConsoleResponse(200, content_type, body)


def _export_response(root_path: Path, fmt: str) -> ConsoleResponse:
    """Serialize the current state snapshot to a read-only download.

    Supported formats: ``board.csv``, ``taskset.md``, ``status.json``,
    ``backup.zip``. Export never mutates state.
    """

    state = ui_state.build_state(root_path)
    if fmt == "board.csv":
        body = ui_export.export_board_csv(state).encode("utf-8")
        return ConsoleResponse(200, "text/csv; charset=utf-8", body)
    if fmt == "taskset.md":
        body = ui_export.export_taskset_markdown(state).encode("utf-8")
        return ConsoleResponse(200, "text/markdown; charset=utf-8", body)
    if fmt == "status.json":
        body = ui_export.export_status_snapshot(state).encode("utf-8")
        return ConsoleResponse(200, "application/json; charset=utf-8", body)
    if fmt == "backup.zip":
        body = ui_export.export_backup_zip(state)
        return ConsoleResponse(200, "application/zip", body)
    return ConsoleResponse(404, "text/plain; charset=utf-8", b"unknown export format\n")


def _import_candidates_from_payload(payload: dict[str, object]) -> tuple[list[dict[str, object]], list[str]]:
    """Parse an upload payload (``format`` + ``content``) into candidates."""

    fmt = str(payload.get("format") or "").strip().lower()
    content = payload.get("content")
    if not isinstance(content, str):
        return [], ["content must be a string"]
    if fmt == "csv":
        return ui_export.parse_csv_import(content), []
    if fmt in {"md", "markdown"}:
        return ui_export.parse_markdown_import(content), []
    return [], [f"unsupported import format: {fmt!r} (expected csv or md)"]


def _import_preview_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    candidates, errors = _import_candidates_from_payload(payload)
    if errors:
        return _json_response({"status": "failed", "errors": errors}, status=400)
    state = ui_state.build_state(root_path)
    preview = ui_export.build_import_preview(candidates, state)
    return _json_response(preview, status=200)


def _import_commit_response(root_path: Path, payload: dict[str, object]) -> ConsoleResponse:
    """Create task.create proposals for each non-duplicate candidate.

    Re-parses + re-checks server-side (never trusts the client's preview) and
    only emits a task.create command for candidates the server considers new
    and valid. Each command flows through ui_commands.submit_command, so the
    proposal/board-sync gate chain is the only writer.
    """

    candidates, errors = _import_candidates_from_payload(payload)
    if errors:
        return _json_response({"status": "failed", "errors": errors}, status=400)
    state = ui_state.build_state(root_path)
    preview = ui_export.build_import_preview(candidates, state)

    results: list[dict[str, object]] = []
    created = 0
    skipped = 0
    for item in preview["items"]:
        if item.get("action") != "create":
            skipped += 1
            results.append({"line": item.get("line"), "title": item.get("title"), "status": "skipped", "reason": item.get("duplicate_reasons") or item.get("errors")})
            continue
        create_payload = ui_export.candidate_to_task_create_payload(item)
        command_result = ui_commands.submit_command(root_path, {"type": "task.create", "payload": create_payload})
        if command_result.get("status") == "accepted":
            created += 1
        else:
            skipped += 1
        results.append({
            "line": item.get("line"),
            "title": item.get("title"),
            "status": command_result.get("status"),
            "command_id": command_result.get("id"),
            "errors": command_result.get("errors"),
        })
    summary = {
        "status": "accepted",
        "resource": "import_commit",
        "counts": {"created": created, "skipped": skipped, "total": len(preview["items"])},
        "results": results,
    }
    return _json_response(summary, status=202)


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
        # Import preview (TASK-AR-333): parse the uploaded payload and return a
        # duplicate-checked preview. This NEVER writes — preview only.
        if method == "POST" and request_path == "/api/import/preview":
            return _import_preview_response(root_path, payload)
        # Import commit (TASK-AR-333): turn each selected, non-duplicate
        # candidate into a task.create proposal via submit_command. No direct
        # task-file writes happen in the console.
        if method == "POST" and request_path == "/api/import/commit":
            return _import_commit_response(root_path, payload)
        task_match = re_api_task_route(request_path)
        if task_match and method == "PATCH":
            return _command_response(root_path, {"type": "task.update", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "reorder":
            return _command_response(root_path, {"type": "task.reorder", "target": task_match[0], "payload": payload})
        if task_match and method == "POST" and task_match[1] == "archive":
            return _command_response(root_path, {"type": "task.archive", "target": task_match[0], "payload": payload})
        # TASK-AR-332: file upload is the ONE legitimate file-write path. It is
        # NOT a ui_commands proposal: it validates/normalizes and writes the
        # bytes + an evidence sidecar under the attachments dir only.
        if method == "POST" and request_path == "/api/attachments":
            return _attachment_upload_response(root_path, payload)
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
    download_id = _attachment_download_id(request_path)
    if download_id is not None:
        return _attachment_download_response(root_path, download_id)

    # Export routes (TASK-AR-333) are strictly read-only downloads: they
    # serialize the current ui_state snapshot to a portable format.
    if request_path.startswith("/api/export/"):
        return _export_response(root_path, request_path[len("/api/export/") :])

    if request_path == "/api/search":
        state = ui_state.build_state(root_path)
        params = parse_qs(parsed_url.query)
        query = (params.get("q", [""])[0] or "").strip()
        results = ui_state.run_search(state["search_index"], query) if query else []
        parsed_query = ui_state.parse_search_query(query)
        return _json_response(
            {
                "generated_at": state["generated_at"],
                "resource": "search",
                "query": query,
                "operators": parsed_query["operators"],
                "terms": parsed_query["terms"],
                "entity_types": list(ui_state.SEARCH_ENTITY_TYPES),
                "items": results,
                "total": len(results),
            }
        )

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
        "/api/teams": "teams",
        "/api/workload": "workload",
        "/api/sources": "sources",
        "/api/errors": "errors",
        "/api/evidence": "evidence",
        "/api/attachments": "attachments",
        "/api/replay": "replay",
        "/api/graph": "graph",
        "/api/live_map": "live_map",
        "/api/live-map": "live_map",
        "/api/state-machines": "state_machines",
        "/api/roadmap": "roadmap",
        "/api/roadmap-timeline": "roadmap_timeline",
        "/api/roadmap_timeline": "roadmap_timeline",
        "/api/planning": "planning",
        "/api/custom_properties": "custom_properties",
        "/api/custom-properties": "custom_properties",
        "/api/labels": "labels",
        "/api/automation_rules": "automation_rules",
        "/api/automation-rules": "automation_rules",
        "/api/triage": "triage",
        "/api/reviews": "reviews",
        "/api/schedules": "schedules",
        "/api/calendar": "calendar",
        "/api/search_index": "search_index",
        "/api/search-index": "search_index",
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
