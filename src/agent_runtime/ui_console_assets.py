"""Served HTML/CSS/JS assets for the Agent Runtime console.

This module owns the large static asset strings so ``ui_console.py`` can
stay focused on HTTP routing, API responses, and data wiring.

Graph layout (TASK-AR-588):
  Dependency, state-machine, and knowledge graph views use
  ``patternSvgLayeredDagreLayout`` backed by the locally vendored
  ``@dagrejs/dagre`` 3.0.0 UMD script when available, then render our own
  token-driven SVG. Edges carry Datadog-style encodings
  (stroke-width = magnitude metric, stroke color = health semantic token) and
  nodes carry GitHub-Actions-style status icons.

  The live agent map uses ``patternSvgForceAgentLayout`` backed by locally
  vendored d3-force 3.0.0 plus local d3 dependencies when available. Nodes are
  rendered as embedded ``patternAgentAvatar`` SVGs with status badges.

  Do NOT adopt elkjs (EPL-2.0 weak copyleft) or 3d-force-graph (WebGL).
"""
from __future__ import annotations

from . import ui_design_assets


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
    // No-flash policy bootstrap (TASK-AR-340): apply the microinteraction /
    // gamification policy attributes on the root BEFORE first paint so CSS keys
    // off them with no flash of animation. Defaults = calm serious mode:
    // motion ON (but always honors prefers-reduced-motion via CSS), gamify OFF.
    (function () {
      var root = document.documentElement;
      var motion = "on";
      var gamify = "off";
      var quest = "off";
      try {
        var rawMotion = window.localStorage.getItem("agent-runtime-motion");
        if (rawMotion === "off") motion = "off";
        var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (prefersReduced && rawMotion !== "on") motion = "off";
        if (window.localStorage.getItem("agent-runtime-gamify") === "on") gamify = "on";
        if (window.localStorage.getItem("agent-runtime-quest-mode") === "on") quest = "on";
      } catch (error) { /* storage blocked: keep calm-serious defaults */ }
      root.setAttribute("data-motion", motion);
      root.setAttribute("data-gamify", gamify);
      root.setAttribute("data-quest-mode", quest);
    })();
  </script>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <div id="runtime-console-app" class="shell" data-work-surface-open="false">
    <header class="topbar">
      <div class="brand">
        <svg class="brand-mark" viewBox="0 0 48 48" role="img" aria-label="Agent Runtime">
          <rect x="6" y="8" width="36" height="32" rx="6"></rect>
          <path d="M14 18h20M14 24h12M14 30h16"></path>
          <circle cx="35" cy="30" r="3"></circle>
        </svg>
        <div>
          <h1>Agent Runtime Console</h1>
          <p id="status-line" data-i18n="common.loading">Loading runtime state</p>
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
        <div class="workspace-switcher">
          <button id="workspace-switcher-toggle" class="workspace-switcher-toggle" type="button" aria-haspopup="true" aria-expanded="false" aria-controls="workspace-switcher-menu" title="Switch workspace">
            <span class="workspace-switcher-icon" aria-hidden="true">&#9783;</span>
            <span id="workspace-switcher-label" class="workspace-switcher-label">Workspace</span>
          </button>
          <div id="workspace-switcher-menu" class="workspace-switcher-menu" role="menu" aria-label="Registered workspaces" hidden></div>
        </div>
        <label class="lang-toggle" title="Language / Settings" data-i18n-title="common.language">
          <span id="lang-toggle-label" class="lang-toggle-label">Lang</span>
          <select id="lang-toggle" class="lang-toggle-select" aria-label="Language" data-i18n-aria-label="common.language">
            <option value="ko">KR</option>
            <option value="en">EN</option>
          </select>
        </label>
        <button id="theme-toggle" class="theme-toggle" type="button" aria-pressed="false" aria-label="Toggle dark mode" title="Toggle light/dark theme">
          <span class="theme-toggle-icon" aria-hidden="true"></span>
          <span id="theme-toggle-label" class="theme-toggle-label">Light</span>
        </button>
        <button id="refresh-button" type="button" data-i18n="button.refresh">Refresh</button>
        <button id="experience-settings-toggle" class="experience-settings-toggle" type="button"
                aria-haspopup="dialog" aria-controls="experience-settings" aria-expanded="false"
                aria-label="Experience settings" title="Microinteractions and gamification settings">
          <span class="experience-settings-icon" aria-hidden="true">&#9881;</span>
          <span class="experience-settings-label">Experience</span>
        </button>
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
        <div class="sidebar-core" aria-label="Core navigation">
          <button class="sidebar-link is-active" type="button" role="tab" data-view="board" data-route="home/board" aria-selected="true">
            <span class="sidebar-icon" aria-hidden="true">&#8962;</span><span class="sidebar-label">Home</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="work" data-route="work/explorer" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Work</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="team" data-route="agents/team" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9733;</span><span class="sidebar-label">Agents</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="meeting" data-route="comms/meetings" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9786;</span><span class="sidebar-label">Decisions</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="events" data-route="records/events" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9201;</span><span class="sidebar-label">Records</span>
          </button>
          <button class="sidebar-link" type="button" role="tab" data-view="search" data-route="search" aria-selected="false">
            <span class="sidebar-icon" aria-hidden="true">&#9906;</span><span class="sidebar-label">Search</span>
          </button>
        </div>
        <details class="sidebar-more" data-group="more">
          <summary class="sidebar-more-summary">
            <span class="sidebar-icon" aria-hidden="true">&#8942;</span><span class="sidebar-label">More</span>
          </summary>
          <div class="sidebar-more-content">
            <div class="sidebar-group" data-group="work">
              <span class="sidebar-group-title" data-i18n="nav.group.work">WORK</span>
              <button class="sidebar-link" type="button" role="tab" data-view="tasksets" data-route="work/tasksets" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9635;</span><span class="sidebar-label">Tasksets</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="tsboard" data-route="work/board" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Taskset Board</span>
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
              <span class="sidebar-group-title" data-i18n="nav.group.agents">AGENTS</span>
              <button class="sidebar-link" type="button" role="tab" data-view="growth" data-route="agents/growth" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9650;</span><span class="sidebar-label">Growth</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="workload" data-route="agents/workload" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9638;</span><span class="sidebar-label">Workload</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="agents" data-route="agents/list" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9737;</span><span class="sidebar-label">Agent List</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="map" data-route="agents/map" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Live Map</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="office" data-route="agents/office" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9971;</span><span class="sidebar-label">Office Map</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="org" data-route="agents/org" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label" data-i18n="nav.org">Org Chart</span>
              </button>
            </div>
            <div class="sidebar-group" data-group="comms">
              <span class="sidebar-group-title" data-i18n="nav.group.comms">COMMS</span>
              <button class="sidebar-link" type="button" role="tab" data-view="inbox" data-route="comms/inbox" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Inbox</span><span id="inbox-nav-badge" class="sidebar-badge" hidden>0</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="channels" data-route="comms/channels" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Channels</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="messages" data-route="comms/messages" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Messages</span>
              </button>
            </div>
            <div class="sidebar-group" data-group="records">
              <span class="sidebar-group-title" data-i18n="nav.group.records">RECORDS</span>
              <button class="sidebar-link" type="button" role="tab" data-view="evidence" data-route="records/evidence" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9745;</span><span class="sidebar-label">Evidence</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="statemachines" data-route="records/state-machines" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">State Machines</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="sources" data-route="records/sources" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Sources</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="knowledge-graph" data-route="records/knowledge-graph" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9901;</span><span class="sidebar-label">Knowledge Graph</span>
              </button>
            </div>
            <div class="sidebar-group" data-group="ops">
              <span class="sidebar-group-title" data-i18n="nav.group.ops">OPS</span>
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
              <button class="sidebar-link" type="button" role="tab" data-view="notifications" data-route="ops/notifications" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Notifications</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="portability" data-route="ops/portability" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#8645;</span><span class="sidebar-label">Import/Export</span>
              </button>
              <button class="sidebar-link" type="button" role="tab" data-view="writes" data-route="ops/writes" aria-selected="false">
                <span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">Writes</span>
              </button>
            </div>
          </div>
        </details>
      </div>
      <button id="sidebar-collapse" class="sidebar-collapse" type="button" aria-label="Collapse sidebar">
        <span class="sidebar-collapse-icon" aria-hidden="true">&#8676;</span><span class="sidebar-label">Collapse</span>
      </button>
    </nav>
    <div id="sidebar-scrim" class="sidebar-scrim" hidden></div>

    <main class="layout" id="main">
      <section class="home-verdict" id="home-verdict" aria-live="polite" hidden>
        <span id="verdict-badge" class="verdict-badge"></span>
        <span id="verdict-line" class="verdict-line"></span>
      </section>
      <section class="cockpit" id="cockpit" data-home-default="cockpit" aria-label="Attention inbox - what needs you now" data-i18n-aria-label="cockpit.aria">
        <header class="cockpit-head">
          <h2 class="cockpit-title" data-i18n="cockpit.title">What needs you now</h2>
          <span class="cockpit-total" id="inbox-total" aria-live="polite"></span>
        </header>
        <div class="cockpit-grid" id="inbox-groups" role="list"></div>
        <p class="cockpit-empty" id="inbox-empty" hidden>
          <span data-i18n="cockpit.empty">Nothing needs you right now.</span>
          <span class="cockpit-empty-asof" id="inbox-empty-asof"></span>
        </p>
      </section>
      <section class="home-strip" id="home-strip" aria-label="Summary strip" data-i18n-aria-label="strip.aria">
        <span id="strip-line"></span>
      </section>
      <section class="flow-tiles" id="flow-tiles" aria-label="Flow metrics" data-i18n-aria-label="tiles.aria"></section>
      <div id="inbox-detail-backdrop" class="inbox-detail-backdrop" hidden></div>
      <aside id="inbox-detail-drawer" class="inbox-detail-drawer" role="dialog" aria-modal="true"
             aria-labelledby="inbox-detail-title" hidden tabindex="-1">
        <header class="inbox-detail-head">
          <div>
            <p class="inbox-detail-kicker" data-i18n="cockpit.detail.kicker">Attention detail</p>
            <h2 id="inbox-detail-title" data-i18n="cockpit.detail.title">Inbox detail</h2>
          </div>
          <button id="inbox-detail-close" class="inbox-detail-close" type="button" aria-label="Close attention detail" data-i18n-aria-label="cockpit.detail.close">&times;</button>
        </header>
        <p id="inbox-detail-summary" class="inbox-detail-summary"></p>
        <div id="inbox-detail-list" class="inbox-detail-list" role="list"></div>
      </aside>

      <section class="work-state-hero" id="work-state-hero" aria-labelledby="work-state-title">
        <header class="work-state-head">
          <div>
            <p class="work-state-kicker" data-i18n="work_state.kicker">Work</p>
            <h2 id="work-state-title" data-i18n="work_state.title">Work state</h2>
          </div>
          <span id="work-state-total" class="work-state-total" aria-live="polite"></span>
          <button type="button" id="work-state-collapse" class="work-state-collapse"
                  aria-expanded="true" aria-controls="work-state-board"
                  aria-label="Toggle work state" data-i18n-aria-label="work_state.collapse">
            <span class="wsh-caret" aria-hidden="true"></span>
          </button>
        </header>
        <div id="work-state-board" class="work-state-board" role="list"></div>
        <p id="work-state-empty" class="work-state-empty" hidden data-i18n="work_state.empty">No active work state.</p>
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
          <details id="home-widgets" class="home-widgets" aria-label="Dashboard widgets">
            <summary class="home-widgets-header">
              <h2 id="home-widgets-title" class="home-widgets-title" data-i18n="widgets.title">Widgets</h2>
            </summary>
            <div id="home-widgets-grid" class="home-widgets-grid"></div>
          </details>
          <p class="board-hint">Hover or focus a card for a peek. Drag a card between lanes to reorder, or focus it and press Ctrl+D to lift, arrows to move, Space to drop, Esc to cancel. Quick actions: Claim / Verify / Close.</p>
          <div id="board-team-filter" class="board-team-filter" role="status" hidden></div>
          <div id="board-controls" class="board-controls">
            <input id="board-filter" class="board-filter" type="search" autocomplete="off" aria-label="Filter tasks">
            <select id="board-sort" class="board-sort" aria-label="Sort tasks">
              <option value="priority"></option>
              <option value="updated"></option>
              <option value="title"></option>
            </select>
            <button id="board-density" type="button" class="board-density" aria-pressed="false"></button>
          </div>
          <div id="kanban" class="kanban" aria-label="Kanban"></div>
          <div id="board-peek" class="board-peek" role="tooltip" aria-hidden="true" hidden></div>
          <div id="board-dnd-status" class="board-dnd-status" role="status" aria-live="polite"></div>
        </div>
        <div id="view-search" class="view">
          <section class="search-view" aria-label="Search">
            <header class="search-view-head">
              <h2>Search</h2>
            </header>
            <input id="search-view-input" class="search-view-input" type="search" autocomplete="off"
                   placeholder="Search tasks, tasksets, messages, events" aria-label="Search entities">
            <div id="search-view-results" class="search-view-results" role="listbox" aria-label="Search results"></div>
          </section>
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
          <h2 class="view-heading">
            <span data-default-label>Tasksets</span><span data-quest-label>Quest Board</span>
          </h2>
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
        <div id="view-growth" class="view">
          <section class="growth" aria-label="Project growth">
            <header class="growth-header">
              <h2>Project Growth</h2>
              <label class="growth-toggle">
                <input id="growth-enabled-toggle" type="checkbox" checked>
                <span>Show growth</span>
              </label>
            </header>
            <p id="growth-disabled" class="growth-disabled" hidden>Growth display is turned off.</p>
            <div id="growth-body" class="growth-body">
              <div id="growth-hero" class="growth-hero" aria-label="Project level and business stage"></div>
              <div id="growth-formula" class="growth-formula" aria-label="XP formula breakdown"></div>
              <div id="growth-efficiency" class="growth-efficiency" aria-label="Efficiency stats (separate from XP)"></div>
              <div id="growth-teams" class="growth-teams" aria-label="Team XP roll-up"></div>
              <div id="growth-agents" class="growth-agents" aria-label="Per-agent XP"></div>
            </div>
          </section>
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
        <div id="view-inbox" class="view">
          <div class="inbox-grid">
            <section class="inbox-main" aria-label="Notification center">
              <header class="inbox-header">
                <h2>Inbox</h2>
                <p id="inbox-summary" class="inbox-summary" role="status" aria-live="polite"></p>
              </header>
              <div class="inbox-toolbar" role="group" aria-label="Inbox filters">
                <label class="inbox-field"><span>Kind</span>
                  <select id="inbox-filter-kind" aria-label="Filter by kind"><option value="">All</option></select>
                </label>
                <label class="inbox-field"><span>Severity</span>
                  <select id="inbox-filter-severity" aria-label="Filter by severity"><option value="">All</option></select>
                </label>
                <label class="inbox-checkbox"><input id="inbox-filter-unread" type="checkbox"> Unread only</label>
                <label class="inbox-checkbox"><input id="inbox-show-muted" type="checkbox"> Show muted</label>
                <button id="inbox-mark-all-read" class="inbox-action" type="button">Mark all read</button>
              </div>
              <p id="inbox-action-hint" class="inbox-action-hint" role="status" aria-live="polite"></p>
              <div id="inbox-list" class="inbox-list" aria-label="Notifications"></div>
            </section>
            <aside class="inbox-side" aria-label="Daily brief and subscriptions">
              <section class="daily-brief" aria-label="Daily brief">
                <header class="daily-brief-header">
                  <h3>Daily Brief</h3>
                  <span id="daily-brief-date" class="daily-brief-date"></span>
                </header>
                <div id="daily-brief-body" class="daily-brief-body"></div>
              </section>
              <section class="inbox-subscribe" aria-label="Subscription rules">
                <h3>Subscriptions</h3>
                <p class="inbox-hint">Subscribe / mute by kind, severity, or taskset. Proposal-only &mdash; a runtime executor applies preferences to the canonical config.</p>
                <form id="inbox-subscribe-form" class="config-form">
                  <select id="inbox-sub-kind" aria-label="Subscribe kind"><option value="">kind (any)</option></select>
                  <select id="inbox-sub-severity" aria-label="Subscribe severity"><option value="">severity (any)</option></select>
                  <input id="inbox-sub-taskset" placeholder="taskset id (optional)" aria-label="Subscribe taskset">
                  <button type="submit">Subscribe</button>
                </form>
                <form id="inbox-keyword-form" class="config-form">
                  <input id="inbox-keyword" placeholder="mute keyword" aria-label="Mute keyword">
                  <button type="submit">Mute keyword</button>
                </form>
                <p id="inbox-subscribe-hint" class="inbox-action-hint" role="status" aria-live="polite"></p>
              </section>
            </aside>
          </div>
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
        <div id="view-office" class="view">
          <section class="office-map" aria-label="2D office map">
            <header class="office-map-header">
              <h2>Office Map</h2>
              <p id="office-map-summary" class="office-map-summary" role="status">no agents</p>
            </header>
            <div class="office-map-stage">
              <div id="office-map-grid" class="office-map-grid" aria-label="Company floor plan"></div>
            </div>
            <ul id="office-map-legend" class="office-map-legend" aria-label="Action glyph legend"></ul>
          </section>
        </div>
        <div id="view-org" class="view">
          <section class="org-chart" aria-label="Agent organization chart">
            <header class="org-chart-header">
              <h2 data-i18n="org.title">Org Chart</h2>
              <p id="org-chart-summary" class="org-chart-summary" role="status"></p>
            </header>
            <div class="org-chart-stage">
              <svg id="org-chart-svg" class="org-chart-svg" viewBox="0 0 1200 720" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Agent organization chart: director to teams to roles" hidden></svg>
              <div id="org-chart-canvas" class="org-chart-canvas" role="group" aria-label="Organization: director, teams, and roles"></div>
            </div>
            <ul id="org-chart-legend" class="org-chart-legend" aria-label="Org chart tier and team legend"></ul>
            <div id="org-role-backdrop" class="org-role-backdrop" hidden></div>
            <aside id="org-role-detail" class="org-role-detail" role="dialog" aria-modal="true" aria-labelledby="org-role-name" hidden>
              <button id="org-role-close" class="org-role-close" type="button" aria-label="Close">&times;</button>
              <p class="org-role-kicker" data-i18n="org.detail.kicker">Agent</p>
              <h3 id="org-role-name" class="org-role-name-h"></h3>
              <div id="org-role-body" class="org-role-body"></div>
            </aside>
          </section>
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
        <div id="view-knowledge-graph" class="view">
          <section class="kg-graph" aria-label="Knowledge graph visualization">
            <header class="kg-graph-header">
              <h2>Knowledge Graph</h2>
              <p id="kg-graph-summary" class="kg-graph-summary" role="status" aria-live="polite">Loading entities&hellip;</p>
            </header>
            <div class="kg-graph-toolbar">
              <input id="kg-search" class="kg-search" type="search" placeholder="Filter by id or title&hellip;" aria-label="Filter knowledge graph entities by id or title">
              <div id="kg-filters" class="kg-filters" role="group" aria-label="Filter knowledge graph by kind"></div>
            </div>
            <div class="kg-graph-stage">
              <div id="kg-graph-state-host" class="kg-graph-state-host" aria-live="polite"></div>
              <svg id="kg-graph-svg" class="kg-graph-svg" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Knowledge graph nodes and edges"></svg>
            </div>
            <ul id="kg-graph-legend" class="kg-graph-legend" aria-label="Knowledge graph legend"></ul>
          </section>
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
        <div id="view-notifications" class="view">
          <p id="routing-status" class="routing-status" role="status" aria-live="polite"></p>
          <p class="routing-hint">External routing exports work events (completed / blocked / approval-pending) to your messenger. Secrets live in a LOCAL gitignored config &mdash; the console never sees them and never sends. This view does proposal-only subscription CRUD; an opt-in local runner performs the actual dispatch.</p>
          <ul class="routing-legend" aria-label="Severity routing windows">
            <li><span class="routing-dot routing-dot-immediate" aria-hidden="true"></span>Immediate &mdash; block / approval-pending</li>
            <li><span class="routing-dot routing-dot-aggregate" aria-hidden="true"></span>Aggregate &mdash; watch (5 / 15-min window)</li>
            <li><span class="routing-dot routing-dot-digest" aria-hidden="true"></span>Digest &mdash; pass / completed (daily)</li>
          </ul>
          <form id="subscription-form" class="config-form" aria-label="Create notification subscription rule">
            <input id="subscription-channel" name="channel" placeholder="channel name (e.g. discord-ops)" required>
            <select id="subscription-kind" name="kind" aria-label="Channel kind">
              <option value="discord">Discord webhook</option>
              <option value="telegram">Telegram bot</option>
              <option value="email">Email / SMTP</option>
            </select>
            <select id="subscription-severity" name="severity" aria-label="Severity subscription">
              <option value="all">All severities</option>
              <option value="immediate">Immediate only</option>
              <option value="aggregate">Aggregate (watch)</option>
              <option value="digest">Digest (daily)</option>
            </select>
            <select id="subscription-window" name="aggregate_minutes" aria-label="Aggregate window">
              <option value="5">5-min window</option>
              <option value="15">15-min window</option>
            </select>
            <button type="submit">Propose rule</button>
          </form>
          <p id="subscription-summary" class="config-summary" role="status" aria-live="polite"></p>
          <div id="subscription-list" class="config-grid" aria-label="Notification subscriptions"></div>
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
            <div id="health-snapshot" class="health-snapshot" role="status" hidden></div>
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
  <!-- TASK-AR-340: experience policy settings (microinteractions + gamification).
       Defaults to calm serious mode; gamification + sound are opt-in. -->
  <div id="experience-settings" class="experience-settings" role="dialog" aria-modal="true" aria-label="Experience settings" hidden>
    <div class="experience-settings-backdrop" data-experience-dismiss="1"></div>
    <div class="experience-settings-panel" role="document">
      <header class="experience-settings-head">
        <h2>Experience</h2>
        <button id="experience-settings-close" class="experience-settings-close" type="button" aria-label="Close settings">&times;</button>
      </header>
      <p class="experience-settings-hint">Default is a calm, serious mode. Animations always honor your system "reduced motion" setting. Gamification is opt-in and leaves no residue when off.</p>
      <section class="experience-settings-group" aria-label="Microinteractions">
        <h3>Microinteractions</h3>
        <label class="experience-toggle">
          <input id="setting-motion" type="checkbox" checked>
          <span class="experience-toggle-text">
            <strong>Animations</strong>
            <small>State transitions, drag physics, skeleton loading, toasts. Disabled automatically under "reduced motion".</small>
          </span>
        </label>
      </section>
      <section class="experience-settings-group" aria-label="Gamification">
        <h3>Gamification</h3>
        <label class="experience-toggle">
          <input id="setting-gamify" type="checkbox">
          <span class="experience-toggle-text">
            <strong>Gamification (opt-in)</strong>
            <small>Taskset-completion confetti, agent XP / level / streak emphasis.</small>
          </span>
        </label>
        <label class="experience-toggle">
          <input id="setting-quest-mode" type="checkbox">
          <span class="experience-toggle-text">
            <strong>Quest-board terminology</strong>
            <small>Reframe tasksets as quests and tasks as quest steps.</small>
          </span>
        </label>
        <label class="experience-toggle">
          <input id="setting-sound" type="checkbox">
          <span class="experience-toggle-text">
            <strong>Completion sound</strong>
            <small>Play a short chime on taskset completion. Off by default.</small>
          </span>
        </label>
      </section>
      <footer class="experience-settings-foot">
        <button id="experience-tour-start" class="experience-tour-start" type="button">Replay onboarding tour</button>
      </footer>
    </div>
  </div>
  <!-- TASK-AR-340: onboarding tour overlay (first-run + replayable). -->
  <div id="onboarding-tour" class="onboarding-tour" role="dialog" aria-modal="true" aria-label="Onboarding tour" hidden>
    <div class="onboarding-tour-backdrop" data-tour-dismiss="1"></div>
    <div class="onboarding-tour-card" role="document">
      <span class="onboarding-tour-step" id="onboarding-tour-step">1 / 1</span>
      <h2 id="onboarding-tour-title">Welcome</h2>
      <p id="onboarding-tour-body">Tour body</p>
      <div class="onboarding-tour-actions">
        <button id="onboarding-tour-skip" class="onboarding-tour-skip" type="button">Skip</button>
        <button id="onboarding-tour-next" class="onboarding-tour-next" type="button">Next</button>
      </div>
    </div>
  </div>
  <!-- TASK-AR-340: contextual help bubble (anchored hints, dismissible). -->
  <div id="contextual-help" class="contextual-help" role="status" aria-live="polite" hidden>
    <span id="contextual-help-text" class="contextual-help-text"></span>
    <button id="contextual-help-dismiss" class="contextual-help-dismiss" type="button" aria-label="Dismiss help">&times;</button>
  </div>
  <!-- TASK-AR-340: celebration canvas host (confetti uses token colors only). -->
  <div id="celebration-layer" class="celebration-layer" aria-hidden="true"></div>
  <script src="/vendor/dagre/3.0.0/dagre.min.js"></script>
  <script src="/vendor/d3-quadtree/3.0.1/d3-quadtree.min.js"></script>
  <script src="/vendor/d3-dispatch/3.0.1/d3-dispatch.min.js"></script>
  <script src="/vendor/d3-timer/3.0.1/d3-timer.min.js"></script>
  <script src="/vendor/d3-force/3.0.0/d3-force.min.js"></script>
  <script src="/app.js"></script>
</body>
</html>
"""

# Replace ad-hoc entity icons in the HTML template with componentIcon SVGs
# (TASK-AR-589). Only the topbar/sidebar icon spans that map clearly to a
# Lucide icon name are replaced; decorative arrows and non-icon entities are
# left as-is.  The replacement is performed once at import time so the served
# HTML is static after that point.
_ENTITY_ICON_MAP = {
    # topbar: sidebar-toggle hamburger menu button
    ">&#9776;</button>": ">" + ui_design_assets.componentIcon("menu", label="Toggle sidebar", class_name="sidebar-toggle-icon") + "</button>",
    # topbar: experience-settings gear icon
    '<span class="experience-settings-icon" aria-hidden="true">&#9881;</span>': '<span class="experience-settings-icon" aria-hidden="true">' + ui_design_assets.componentIcon("settings") + "</span>",
    # sidebar core: Home
    '<span class="sidebar-icon" aria-hidden="true">&#8962;</span><span class="sidebar-label">Home</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("home") + '</span><span class="sidebar-label">Home</span>',
    # sidebar core: Work (list)
    '<span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Work</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("list") + '</span><span class="sidebar-label">Work</span>',
    # sidebar core: Search
    '<span class="sidebar-icon" aria-hidden="true">&#9906;</span><span class="sidebar-label">Search</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("search") + '</span><span class="sidebar-label">Search</span>',
    # sidebar core: Agents (star)
    '<span class="sidebar-icon" aria-hidden="true">&#9733;</span><span class="sidebar-label">Agents</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("users") + '</span><span class="sidebar-label">Agents</span>',
    # sidebar core: Records (clock)
    '<span class="sidebar-icon" aria-hidden="true">&#9201;</span><span class="sidebar-label">Records</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("clock") + '</span><span class="sidebar-label">Records</span>',
    # sidebar: Calendar (mail entity -> calendar icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Calendar</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("calendar") + '</span><span class="sidebar-label">Calendar</span>',
    # sidebar: State Machines (gear)
    '<span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">State Machines</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("settings") + '</span><span class="sidebar-label">State Machines</span>',
    # sidebar: Writes (gear)
    '<span class="sidebar-icon" aria-hidden="true">&#9881;</span><span class="sidebar-label">Writes</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("settings") + '</span><span class="sidebar-label">Writes</span>',
    # sidebar: Evidence (check)
    '<span class="sidebar-icon" aria-hidden="true">&#9745;</span><span class="sidebar-label">Evidence</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("check-circle") + '</span><span class="sidebar-label">Evidence</span>',
    # sidebar: Flag -> flag icon (&#9873;)
    '<span class="sidebar-icon" aria-hidden="true">&#9873;</span><span class="sidebar-label">Triage</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("flag") + '</span><span class="sidebar-label">Triage</span>',
    # sidebar: Notifications (bell) -> inbox
    '<span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Notifications</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("bell") + '</span><span class="sidebar-label">Notifications</span>',
    # sidebar: Dashboard
    '<span class="sidebar-icon" aria-hidden="true">&#9683;</span><span class="sidebar-label">Dashboard</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("bar-chart") + '</span><span class="sidebar-label">Dashboard</span>',
    # sidebar: Automation (zap)
    '<span class="sidebar-icon" aria-hidden="true">&#9889;</span><span class="sidebar-label">Automation</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("zap") + '</span><span class="sidebar-label">Automation</span>',
    # sidebar: Inbox (mail)
    '<span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Inbox</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("inbox") + '</span><span class="sidebar-label">Inbox</span>',
    # sidebar: Messages (mail)
    '<span class="sidebar-icon" aria-hidden="true">&#9993;</span><span class="sidebar-label">Messages</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("mail") + '</span><span class="sidebar-label">Messages</span>',
    # sidebar: Growth (chart bar)
    '<span class="sidebar-icon" aria-hidden="true">&#9650;</span><span class="sidebar-label">Growth</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("activity") + '</span><span class="sidebar-label">Growth</span>',
    # sidebar: more-horizontal (vertical ellipsis)
    '<span class="sidebar-icon" aria-hidden="true">&#8942;</span><span class="sidebar-label">More</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("more-horizontal") + '</span><span class="sidebar-label">More</span>',
    # sidebar: Roadmap (using list icon -- &#9776; overloaded)
    '<span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Roadmap</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("chevron-right") + '</span><span class="sidebar-label">Roadmap</span>',
    # sidebar: Timeline (using arrow-right -- &#9776; overloaded)
    '<span class="sidebar-icon" aria-hidden="true">&#9776;</span><span class="sidebar-label">Timeline</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("arrow-right") + '</span><span class="sidebar-label">Timeline</span>',
    # --- TASK-AR-591: remaining ad-hoc entity icons replaced with componentIcon ---
    # sidebar core: Decisions (smiley -> calendar icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9786;</span><span class="sidebar-label">Decisions</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("calendar") + '</span><span class="sidebar-label">Decisions</span>',
    # sidebar: Tasksets (grid)
    '<span class="sidebar-icon" aria-hidden="true">&#9635;</span><span class="sidebar-label">Tasksets</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("grid") + '</span><span class="sidebar-label">Tasksets</span>',
    # sidebar: Taskset Board (layers)
    '<span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Taskset Board</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("layers") + '</span><span class="sidebar-label">Taskset Board</span>',
    # sidebar: Planner (edit icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9998;</span><span class="sidebar-label">Planner</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("edit") + '</span><span class="sidebar-label">Planner</span>',
    # sidebar: Dependencies (link icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Dependencies</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("link") + '</span><span class="sidebar-label">Dependencies</span>',
    # sidebar: Workload (cpu icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9638;</span><span class="sidebar-label">Workload</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("cpu") + '</span><span class="sidebar-label">Workload</span>',
    # sidebar: Agent List (users icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9737;</span><span class="sidebar-label">Agent List</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("users") + '</span><span class="sidebar-label">Agent List</span>',
    # sidebar: Live Map (map icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Live Map</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("map") + '</span><span class="sidebar-label">Live Map</span>',
    # sidebar: Office Map (map icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9971;</span><span class="sidebar-label">Office Map</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("map") + '</span><span class="sidebar-label">Office Map</span>',
    # sidebar: Channels (layers icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Channels</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("layers") + '</span><span class="sidebar-label">Channels</span>',
    # sidebar: Sources (clipboard icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9783;</span><span class="sidebar-label">Sources</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("clipboard") + '</span><span class="sidebar-label">Sources</span>',
    # sidebar: Knowledge Graph (link icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9901;</span><span class="sidebar-label">Knowledge Graph</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("link") + '</span><span class="sidebar-label">Knowledge Graph</span>',
    # sidebar: Properties (info icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9636;</span><span class="sidebar-label">Properties</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("info") + '</span><span class="sidebar-label">Properties</span>',
    # sidebar: Labels (flag icon)
    '<span class="sidebar-icon" aria-hidden="true">&#9750;</span><span class="sidebar-label">Labels</span>': '<span class="sidebar-icon" aria-hidden="true">' + ui_design_assets.componentIcon("flag") + '</span><span class="sidebar-label">Labels</span>',
    # sidebar: Import/Export (arrow-right icon)
    '<span class="sidebar-collapse-icon" aria-hidden="true">&#8676;</span><span class="sidebar-label">Collapse</span>': '<span class="sidebar-collapse-icon" aria-hidden="true">' + ui_design_assets.componentIcon("chevron-right") + '</span><span class="sidebar-label">Collapse</span>',
    # workspace switcher icon (layers)
    '<span class="workspace-switcher-icon" aria-hidden="true">&#9783;</span>': '<span class="workspace-switcher-icon" aria-hidden="true">' + ui_design_assets.componentIcon("layers") + '</span>',
}

_html = HTML
for _entity, _replacement in _ENTITY_ICON_MAP.items():
    _html = _html.replace(_entity, _replacement)
HTML = _html


CSS = """/*
 * Theme tokens (TASK-AR-320).
 * :root is the default Notion-style LIGHT theme. [data-theme="dark"] restores
 * the original Linear dark palette. Every component consumes var(--token) only
 * so both themes share one structure. Status colors (success/warning/danger/
 * info/primary) keep the same semantic meaning across themes and are always
 * paired with text labels (never color-only signalling).
 */
.skip-link {
  position: absolute;
  left: 8px;
  top: -48px;
  z-index: 1000;
  padding: var(--space-lg) var(--space-3xl);
  background: var(--primary);
  color: var(--canvas);
  border-radius: var(--radius-sm);
  text-decoration: none;
  transition: top 120ms ease;
}
.skip-link:focus { top: 8px; outline: 2px solid var(--canvas); }
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
  /* 2D office map (TASK-AR-364). Room surfaces reuse the panel tokens; each room
     accent maps to an existing semantic color so no per-room raw color leaks. */
  --office-floor: var(--surface-grad);
  --office-room-bg: var(--panel);
  --office-room-line: var(--line-strong);
  --office-avatar-bg: var(--panel-strong);
  /* Chibi office sprites (TASK-AR-592 v2). Warm skin + hair tones fill the
     character center (Owner: v1 felt empty); they are intentional art colors,
     not reused semantic tokens, and only appear inside the pixel sprite. */
  --office-skin: #f6caa6;
  --office-skin-shade: #e0a878;
  --office-hair: #5b4636;
  /* Growth system (TASK-AR-363). XP/level surfaces reuse existing semantic
     tokens; --growth-xp drives the level bar, --growth-stage the stage chip. */
  --growth-xp: var(--success);
  --growth-stage: var(--primary);
  --growth-efficiency: var(--teal);
  /* Data-viz palette light (TASK-AR-590). Categorical 8-hue + 5-step sequential.
     Sources: Radix Colors (MIT, radix-ui/colors) light hues for categorical;
     IBM Carbon data-viz categorical-color-4 / sequential-01 (Apache 2.0,
     carbondesignsystem.com/data-visualization/color-palettes) for seq steps.
     WCAG: all categorical tokens >3:1 contrast vs --panel (graphical threshold).
     Graph node/edge categorical colors (TASK-AR-588) consume these tokens.
     Sparkline: --dv-sparkline maps to --accent per theme for auto-theming.
     TASK-AR-592: dv-cat-3 light adjusted for WCAG AA compliance
     (was 2.28:1, now 3.66:1 vs white panel; non-text graphical threshold).
     TASK-AR-590 (redo): dv-cat-2/5/6 light darkened to clear the WCAG 1.4.11
     non-text 3:1 threshold vs the light --panel (were 2.86/2.94/2.82:1; now
     3.49/4.40/4.20:1) so every categorical hue is verifiably >=3:1. */
  --dv-cat-1: #3e63dd;
  --dv-cat-2: #0d9488;
  --dv-cat-3: #b87000;
  --dv-cat-4: #e54d2e;
  --dv-cat-5: #218358;
  --dv-cat-6: #cc4e00;
  --dv-cat-7: #6e56cf;
  --dv-cat-8: #d6409f;
  --dv-seq-1: #d0e2ff;
  --dv-seq-2: #82b4ff;
  --dv-seq-3: #4589ff;
  --dv-seq-4: #0f62fe;
  --dv-seq-5: #002d9c;
  --dv-sparkline: var(--accent, var(--primary));
  --dv-sparkline-area: rgba(46, 111, 219, 0.13);
  --dv-sparkline-w: 64px;
  --dv-sparkline-h: 24px;
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
  /* 2D office map (TASK-AR-364) */
  --office-floor: var(--surface-grad);
  --office-room-bg: var(--panel);
  --office-room-line: var(--line-strong);
  --office-avatar-bg: var(--panel-strong);
  /* Chibi office sprites (TASK-AR-592 v2): slightly deeper skin/hair for dark theme. */
  --office-skin: #e7b489;
  --office-skin-shade: #c9925f;
  --office-hair: #4a3a2c;
  /* Growth system (TASK-AR-363) */
  --growth-xp: var(--success);
  --growth-stage: var(--primary-hover);
  --growth-efficiency: var(--teal);
  /* Data-viz palette dark (TASK-AR-590). Categorical: IBM Carbon data-viz
     categorical-color-4 dark (Apache 2.0). Sequential: Carbon seq-01 dark.  */
  --dv-cat-1: #8a3ffc;
  --dv-cat-2: #33b1ff;
  --dv-cat-3: #007d79;
  --dv-cat-4: #ff7eb6;
  --dv-cat-5: #fa4d56;
  --dv-cat-6: #fff1f1;
  --dv-cat-7: #6fdc8c;
  --dv-cat-8: #4589ff;
  --dv-seq-1: #e8f0ff;
  --dv-seq-2: #a6c8ff;
  --dv-seq-3: #4589ff;
  --dv-seq-4: #0f62fe;
  --dv-seq-5: #001d6c;
  --dv-sparkline: var(--accent, var(--primary));
  --dv-sparkline-area: rgba(94, 106, 210, 0.18);
}
* { box-sizing: border-box; }
html { background: var(--canvas); }
body {
  margin: 0;
  min-height: 100vh;
  font-family: var(--font-sans);
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
  gap: var(--space-md);
  padding: var(--space-2xl) var(--space-xl);
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
.sidebar[data-collapsed="true"] .sidebar-more-content {
  display: none;
}
.sidebar-pinned {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--primary-soft);
  padding: var(--space-xl);
  margin-bottom: var(--space-md);
}
.sidebar-active-label {
  display: block;
  color: var(--subtle);
  font-size: var(--font-size-ui-10);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.sidebar-active-name {
  display: block;
  margin: var(--space-sm) 0 var(--space-md);
  color: var(--ink);
  font-size: var(--font-size-ui-13);
  overflow-wrap: anywhere;
}
.sidebar-active-progress {
  margin-bottom: var(--space-md);
}
.sidebar-active-meta {
  color: var(--muted);
  font-size: var(--font-size-ui-11);
}
.sidebar-active-empty {
  color: var(--subtle);
  font-size: var(--font-size-ui-11);
}
.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  flex: 1 1 auto;
}
.sidebar-core {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-bottom: var(--space-md);
}
.sidebar-more {
  border-top: 1px solid var(--line);
  padding-top: var(--space-md);
}
.sidebar-more-summary {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  width: 100%;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  cursor: pointer;
  font-size: var(--font-size-ui-13);
  font-weight: 700;
  list-style: none;
  padding: var(--space-lg) var(--space-xl);
}
.sidebar-more-summary::-webkit-details-marker {
  display: none;
}
.sidebar-more-summary:hover,
.sidebar-more[open] > .sidebar-more-summary {
  color: var(--ink);
  background: var(--raise-strong);
}
.sidebar-more-summary:focus-visible {
  outline: 2px solid var(--primary-hover);
  outline-offset: 2px;
  box-shadow: var(--focus);
}
.sidebar-more-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-top: var(--space-md);
}
.sidebar-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding-bottom: var(--space-lg);
}
.sidebar-group-title {
  color: var(--subtle);
  font-size: var(--font-size-ui-10);
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: var(--space-lg) var(--space-xl) var(--space-xs);
}
.sidebar-link {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  width: 100%;
  border: 1px solid transparent;
  border-radius: var(--radius);
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-size: var(--font-size-ui-13);
  font-weight: 600;
  text-align: left;
  padding: var(--space-lg) var(--space-xl);
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
  height: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: var(--font-size-ui-15);
  line-height: 1;
}
.icon,
.sidebar-toggle-icon {
  width: var(--icon-size);
  height: var(--icon-size);
  color: currentColor;
  stroke: currentColor;
  flex: 0 0 auto;
  vertical-align: -0.125em;
}
.sidebar-icon .icon,
.experience-settings-icon .icon {
  display: block;
}
.sidebar[data-collapsed="true"] .sidebar-link {
  justify-content: center;
}
.sidebar[data-collapsed="true"] .sidebar-more-summary {
  justify-content: center;
}
.sidebar-collapse {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  width: 100%;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-weight: 600;
  padding: var(--space-lg) var(--space-xl);
  margin-top: auto;
}
.sidebar-collapse:hover {
  transform: none;
  color: var(--ink);
}
.sidebar-toggle {
  display: none;
  padding: var(--space-lg-half) var(--space-xl-half);
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
  gap: var(--space-6xl);
  padding: var(--space-5xl) var(--space-7xl);
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
  gap: var(--space-2xl);
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
  stroke: var(--on-accent);
  stroke-width: 2;
  stroke-linecap: round;
}
h1 {
  font-size: var(--font-size-ui-28);
  line-height: 1.05;
  letter-spacing: 0;
}
#status-line {
  margin-top: var(--space-sm-half);
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
/* TASK-AR-623: freshness badge turns amber only when the snapshot nears the
   server TTL backstop; a quiet, recent console stays muted (calm by default). */
#status-line.is-stale {
  color: var(--warning);
  font-weight: 600;
}
.cockpit-empty-asof {
  color: var(--muted);
  font-variant-numeric: tabular-nums;
}
/* TASK-AR-631: decision screenfit — verdict strip, summary strip, flow tiles.
   Quiet by default: neutral panel surfaces, semantic state color only on the
   verdict badge and an over-limit WIP tile. */
.home-verdict {
  display: flex; align-items: center; gap: var(--space-lg);
  margin: 0 0 0.85rem;
}
.verdict-badge {
  font-weight: 700; font-size: 0.86rem; padding: 0.18rem 0.65rem;
  border-radius: var(--radius-pill); border: 1px solid var(--line-strong);
  color: var(--ink); background: var(--panel-strong);
}
.verdict-badge[data-verdict="healthy"] { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
.verdict-badge[data-verdict="watch"] { color: var(--warning); background: var(--warning-soft); border-color: var(--warning-line); }
.verdict-badge[data-verdict="at_risk"] { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.verdict-line { color: var(--ink); font-size: 0.9rem; }
.home-strip {
  margin: 0.85rem 0 0.6rem; color: var(--muted); font-size: 0.86rem;
  font-variant-numeric: tabular-nums;
}
.flow-tiles {
  display: grid; grid-template-columns: repeat(3, minmax(150px, 1fr));
  gap: var(--space-lg); margin: 0 0 1rem;
}
.flow-tiles:empty { display: none; }
.flow-tile {
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
  padding: 0.65rem 0.85rem; display: flex; flex-direction: column; gap: 0.2rem;
  box-shadow: var(--shadow);
}
.flow-tile .ft-label {
  color: var(--muted); font-size: 0.72rem; text-transform: uppercase;
  letter-spacing: 0.04em;
}
.flow-tile .ft-value {
  font-size: 1.4rem; font-weight: 700; color: var(--ink);
  font-variant-numeric: tabular-nums; display: flex; align-items: baseline; gap: 0.4rem;
}
.flow-tile .ft-value .ft-unit { font-size: 0.78rem; color: var(--muted); font-weight: 500; }
.flow-tile.ft-warn .ft-value { color: var(--warning); }
.flow-tile .ft-spark { min-height: 24px; }
.inbox-card-more {
  justify-content: center; align-items: center; color: var(--muted);
  font-size: 0.85rem; border-style: dashed;
}
@media (max-width: 760px) {
  .flow-tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-md); }
  .flow-tile .ft-value { font-size: 1.05rem; }
  .flow-tile .ft-spark { display: none; }
}
.toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-xl);
  flex-wrap: wrap;
}
button {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  padding: var(--space-lg-half) var(--space-2xl);
  min-height: 36px;
  font: inherit;
  font-size: var(--font-size-ui-13);
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
  gap: var(--space-md-half);
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
  font-size: var(--font-size-ui-12);
  font-weight: 700;
}
/* TASK-AR-341: workspace switcher + language toggle (topbar) + home widgets.
 * Every color flows through var(--token); no raw hex/rgba in these rules. */
.workspace-switcher { position: relative; display: inline-flex; }
.workspace-switcher-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md-half);
  background: var(--raise);
  border: 1px solid var(--line-strong);
  color: var(--ink);
  box-shadow: none;
}
.workspace-switcher-toggle:hover { border-color: var(--primary); }
.workspace-switcher-icon { font-size: var(--font-size-ui-13); }
.workspace-switcher-label {
  font-size: var(--font-size-ui-12);
  font-weight: 700;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.workspace-switcher-menu {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  z-index: 40;
  min-width: 280px;
  max-width: 380px;
  max-height: 60vh;
  overflow-y: auto;
  padding: var(--space-lg);
  background: var(--surface-raised);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}
.workspace-switcher-menu[hidden] { display: none; }
.workspace-switcher-hint {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  padding: var(--space-xs) var(--space-sm) var(--space-sm);
}
.workspace-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  padding: var(--space-lg) var(--space-xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--raise);
}
.workspace-item.is-current { border-color: var(--primary); background: var(--tile); }
.workspace-item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}
.workspace-item-name { font-weight: 700; font-size: var(--font-size-ui-13); color: var(--ink); }
.workspace-item-current-badge {
  font-size: var(--font-size-ui-10);
  font-weight: 700;
  color: var(--on-accent);
  background: var(--primary);
  border-radius: var(--radius-pill);
  padding: var(--space-hairline) var(--space-lg);
}
.workspace-item-path {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  word-break: break-all;
}
.workspace-item-preview { font-size: var(--font-size-ui-11); color: var(--muted); }
.workspace-item-cmd {
  font-size: var(--font-size-ui-11);
  font-family: var(--font-mono);
  background: var(--tile);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-sm) var(--space-md);
  color: var(--ink);
  word-break: break-all;
}
.workspace-item-switch {
  align-self: flex-start;
  font-size: var(--font-size-ui-11);
  padding: var(--space-sm) var(--space-xl);
}
.lang-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
  font-size: var(--font-size-ui-12);
  font-weight: 700;
  color: var(--ink);
}
.lang-toggle-select {
  font: inherit;
  font-size: var(--font-size-ui-12);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
}
.home-widgets { margin-bottom: var(--space-4xl); }
/* Decision-first IA P1: widgets are opt-in (collapsed) so the cockpit stays the
   hero. The header is the <summary> click target. */
.home-widgets-header {
  margin-bottom: var(--space-lg);
  cursor: pointer;
  list-style: none;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.home-widgets-header::-webkit-details-marker { display: none; }
.home-widgets-header::before {
  content: "\\25B8";
  color: var(--muted);
  font-size: var(--font-size-ui-13);
  transition: transform 0.15s ease;
}
.home-widgets[open] > .home-widgets-header { margin-bottom: var(--space-lg); }
.home-widgets[open] > .home-widgets-header::before { transform: rotate(90deg); }
.home-widgets-title {
  font-size: var(--font-size-ui-13);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted);
  margin: 0;
}
.home-widgets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-2xl);
}
.home-widget {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-2xl) var(--space-3xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--tile);
}
.home-widget-title {
  font-size: var(--font-size-ui-12);
  font-weight: 700;
  color: var(--ink);
}
.home-widget-metric-value {
  font-size: var(--font-size-ui-26);
  font-weight: 800;
  color: var(--primary);
  line-height: 1.1;
}
.home-widget-caption, .home-widget-note { font-size: var(--font-size-ui-12); color: var(--muted); }
.home-widget-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-sm); }
.home-widget-list-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-12);
  color: var(--ink);
}
.home-widget-list-row .home-widget-list-value { color: var(--muted); font-weight: 700; }
.home-widget-shortcut {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-12);
  color: var(--ink);
  padding: var(--space-xs-half) 0;
}
.home-widget-shortcut kbd {
  font-family: var(--font-mono);
  font-size: var(--font-size-ui-11);
  background: var(--raise);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-hairline) var(--space-md);
  color: var(--ink);
}
.home-widget-empty { font-size: var(--font-size-ui-12); color: var(--muted); }
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
  padding: var(--space-lg-half) var(--space-xl);
  font: inherit;
  font-size: var(--font-size-ui-13);
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
  gap: var(--space-4xl);
  align-items: start;
  padding: var(--space-5xl) var(--space-7xl) var(--space-8xl);
  margin-left: var(--sidebar-width);
  transition: margin-left 160ms ease;
}
.layout > * {
  min-width: 0;
}
.shell[data-sidebar-collapsed="true"] .layout {
  margin-left: var(--sidebar-rail);
}
.dashboard {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: var(--space-xl);
}
.metric {
  min-height: 82px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--metric-grad);
  padding: var(--space-3xl);
  box-shadow: inset 0 1px 0 var(--hairline-top);
}
.metric strong {
  display: block;
  margin-top: var(--space-lg);
  font-size: var(--font-size-ui-30);
  line-height: 1;
  letter-spacing: 0;
}
.metric span {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-2xl);
  padding: var(--space-3xl);
}
.shell[data-work-surface-open="false"] .work-surface {
  display: none;
}
/* TASK-AR-624: the create-task / runtime-command forms belong to the board and
   work views. On every other view they were unrelated noise pinned above the
   content, so scope them out unless board/work is active. */
.shell:not([data-active-view="board"]):not([data-active-view="work"]) .create-form,
.shell:not([data-active-view="board"]):not([data-active-view="work"]) .runtime-form {
  display: none;
}
.create-form,
.runtime-form,
.filter-row,
.edit-form,
.edit-row,
.button-row {
  display: grid;
  gap: var(--space-lg);
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
  gap: var(--space-md);
  padding-top: var(--space-xs);
  border-bottom: 1px solid var(--line);
}
.tab {
  background: transparent;
  border-color: transparent;
  box-shadow: none;
  color: var(--muted);
  padding: var(--space-lg) var(--space-xl);
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
/* SPEC-board-taskview-v1: board controls bar + lane "more" + density (tokens only). */
.board-controls {
  display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-md);
  margin-bottom: var(--space-lg);
}
.board-filter {
  flex: 1 1 200px; min-width: 160px;
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--surface-raised); color: var(--ink);
  padding: var(--space-sm) var(--space-md); font: inherit; font-size: var(--font-size-ui-13);
}
.board-filter:focus-visible { outline: 2px solid var(--primary); outline-offset: 1px; box-shadow: var(--focus); }
.board-sort, .board-density {
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--panel-strong); color: var(--ink);
  padding: var(--space-sm) var(--space-md); font: inherit; font-size: var(--font-size-ui-13); cursor: pointer;
}
.board-density[aria-pressed="true"] { border-color: var(--primary); background: var(--primary-soft); }
.lane-more {
  display: block; width: 100%; margin-top: var(--space-sm);
  border: 1px dashed var(--line-strong); border-radius: var(--radius-sm);
  background: transparent; color: var(--muted);
  padding: var(--space-sm); font: inherit; font-size: var(--font-size-ui-12); cursor: pointer;
}
.lane-more:hover { border-color: var(--primary-line); color: var(--primary); background: var(--primary-soft); }
.kanban.density-compact .lane { gap: var(--space-xs); }
.kanban {
  display: grid;
  grid-template-columns: repeat(3, minmax(220px, 1fr));
  gap: var(--space-xl);
}
.lane {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--raise-strong);
  padding: var(--space-xl);
}
.lane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  font-weight: 800;
  text-transform: uppercase;
  padding-bottom: var(--space-lg);
  letter-spacing: 0;
}
.lane-title {
  display: grid;
  gap: var(--space-xs);
  color: var(--ink);
}
.lane-title small {
  color: var(--subtle);
  font-size: var(--font-size-ui-10);
  text-transform: uppercase;
}
.lane-count {
  min-width: 28px;
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-pill);
  padding: var(--space-xs-half) var(--space-lg);
  background: var(--primary-soft-strong);
  color: var(--ink);
  text-align: center;
}
.lane-body,
.list-panel,
.taskset-strip,
.assurance-grid {
  display: grid;
  gap: var(--space-lg);
}
.lane-body {
  min-height: 48px;
}
.board-hint {
  color: var(--muted);
  font-size: var(--font-size-ui-11);
  line-height: 1.4;
  margin-bottom: var(--space-lg);
}
.board-team-filter {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  margin-bottom: var(--space-lg);
  padding: var(--space-md) var(--space-2xl);
  border: 1px solid var(--primary-line);
  background: var(--primary-soft);
  border-radius: var(--radius-pill);
  font-size: var(--font-size-ui-13);
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
  border-radius: var(--radius-pill);
  background: var(--primary-hover);
  margin: var(--space-xs) 0;
}
.task-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-top: var(--space-xs);
}
.task-card-actions button {
  font-size: var(--font-size-ui-11);
  padding: var(--space-xs-half) var(--space-lg-half);
  border-radius: var(--radius-sm);
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
  padding: var(--space-2xl);
  color: var(--ink);
  font-size: var(--font-size-ui-12);
  line-height: 1.45;
  pointer-events: none;
}
.board-peek h3 {
  font-size: var(--font-size-ui-13);
  margin-bottom: var(--space-sm);
}
.board-peek code {
  color: var(--primary-hover);
  font-family: var(--font-mono);
  font-size: var(--font-size-ui-11);
}
.board-peek dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--space-xs) var(--space-xl);
  margin-top: var(--space-md);
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
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
  padding: var(--space-xl);
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
  padding: var(--space-md) var(--space-2xl);
  cursor: pointer;
}
.taskset-template-label {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.taskset-template-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}
.taskset-template-btn {
  font-size: var(--font-size-ui-12);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--raise);
  color: var(--ink);
  padding: var(--space-sm-half) var(--space-xl);
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
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
  padding: var(--space-lg) var(--space-xl);
  border: 1px solid var(--primary-line);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius);
  background: var(--primary-soft);
}
.taskset-bulk-count {
  font-weight: 600;
  font-size: var(--font-size-ui-12);
  color: var(--ink);
}
.taskset-bulk-bar select,
.taskset-bulk-bar input {
  font-size: var(--font-size-ui-12);
}
.taskset-bulk-bar button {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--primary);
  color: var(--on-accent);
  padding: var(--space-sm-half) var(--space-xl);
  cursor: pointer;
}
.taskset-bulk-bar button.ghost {
  background: var(--raise);
  color: var(--muted);
  border-color: var(--border);
}
.taskset-task-select {
  margin-right: var(--space-md);
}
.taskset-card-tasks {
  display: grid;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  border-top: 1px solid var(--line);
  padding-top: var(--space-md);
}
.taskset-task-row {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-lg);
  z-index: 60;
  pointer-events: none;
}
.undo-toast {
  display: flex;
  align-items: center;
  gap: var(--space-2xl);
  pointer-events: auto;
  background: var(--panel-strong);
  color: var(--ink);
  border: 1px solid var(--border);
  border-left: 3px solid var(--success);
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  padding: var(--space-xl) var(--space-3xl);
  font-size: var(--font-size-ui-13);
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
  padding: var(--space-sm) var(--space-xl);
  cursor: pointer;
  font-size: var(--font-size-ui-12);
}
.taskset-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(150px, 0.28fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}
.taskset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: var(--space-xl);
}
.taskset-completion {
  border: 1px solid var(--success-line);
  border-left: 3px solid var(--success);
  border-radius: var(--radius);
  background: var(--success-soft);
  color: var(--ink);
  padding: var(--space-2xl);
  display: grid;
  gap: var(--space-lg);
  margin-bottom: var(--space-2xl);
}
.taskset-completion-head {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}
.taskset-completion-badge {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--success);
}
.taskset-completion-message {
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
.taskset-completion-next {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--tile);
  padding: var(--space-lg) var(--space-xl);
}
.taskset-completion-next-label {
  font-size: var(--font-size-ui-11);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--subtle);
}
.taskset-completion-next-meta {
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.taskset-completion-next-cmd {
  font-size: var(--font-size-ui-12);
  color: var(--ink);
  background: var(--raise);
  border-radius: var(--radius-sm-half);
  padding: var(--space-xs) var(--space-md);
}
.evidence-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-xl);
}
.evidence-grid section {
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: var(--space-xl);
}
.evidence-grid h2 {
  font-size: var(--font-size-ui-14);
  margin-bottom: var(--space-lg);
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
  padding: var(--space-xl);
  display: grid;
  gap: var(--space-md-half);
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
  gap: var(--space-lg);
}
.task-id {
  color: var(--primary-hover);
  font-family: var(--font-mono);
  font-size: var(--font-size-ui-11);
}
.task-card-title {
  color: var(--ink);
  font-size: var(--font-size-ui-13);
  line-height: 1.25;
}
.task-card-summary {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  line-height: 1.35;
}
.task-card .task-card-inflight {
  color: var(--amber);
  font-size: var(--font-size-ui-11);
  line-height: 1.3;
  overflow-wrap: anywhere;
}
.task-card-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-md);
}
.agent-card-meta,
.taskset-card-meta,
.command-card-meta,
.audit-card-meta,
.surface-card-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-md);
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
  border-radius: var(--radius-sm);
  background: var(--tile);
  padding: var(--space-md);
}
.meta-label {
  display: block;
  color: var(--subtle);
  font-size: var(--font-size-ui-10);
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
  margin-top: var(--space-sm);
  color: var(--ink);
  font-size: var(--font-size-ui-11);
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.task-card-evidence strong {
  color: var(--teal);
}
.task-card-taskset strong {
  color: var(--primary-hover);
}
/* Agent avatar (TASK-AR-587, experimental) */
.agent-avatar {
  display: block;
  flex-shrink: 0;
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.agent-card-header,
.taskset-card-header,
.command-card-header,
.audit-card-header,
.surface-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-lg);
}
.taskset-title {
  display: grid;
  gap: var(--space-xs-half);
  min-width: 0;
}
.taskset-title b {
  font-size: var(--font-size-ui-14);
}
.taskset-title span {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
}
.alias-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
}
.alias-row code {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius-pill);
  padding: var(--space-sm) var(--space-md-half);
  background: var(--primary-soft);
  color: var(--primary);
  font-size: var(--font-size-ui-11);
}
.taskset-summary,
.taskset-command {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  line-height: 1.4;
}
.taskset-command {
  overflow-wrap: anywhere;
}
.taskset-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-md);
}
.taskset-action {
  min-height: 32px;
  padding: var(--space-md-half) var(--space-lg-half);
  font-size: var(--font-size-ui-12);
}
.audit-card p {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  line-height: 1.4;
}
/* ----- Live map: presence + node/edge graph (TASK-AR-326) ----- */
.live-map {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
  margin-bottom: var(--space-4xl);
  padding: var(--space-3xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
}
.live-map-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2xl);
}
.live-map-header h2 { margin: 0; }
.live-map-presence {
  margin: 0;
  font-size: var(--font-size-ui-12);
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
/* SPEC-relationship-edge-labels-v1: mid-edge "why" labels for block/review. */
.live-map-edge-label { fill: var(--ink); font-size: var(--font-size-ui-10); font-weight: 600; pointer-events: none; }
.live-map-edge-label.kind-block { fill: var(--danger); }
.live-map-edge-label.kind-review { fill: var(--warning); }
.live-map-edge-label-bg { fill: var(--canvas); opacity: 0.85; }
.live-map-edge.magnitude-low { stroke-width: 1.5; }
.live-map-edge.magnitude-medium { stroke-width: 2.25; }
.live-map-edge.magnitude-high { stroke-width: 3; }
.live-map-edge.health-pass { stroke: var(--success-line); opacity: 0.9; }
.live-map-edge.health-watch { stroke: var(--warning-line); opacity: 0.85; }
.live-map-edge.health-block { stroke: var(--danger); opacity: 1; }
.live-map-edge.health-info { stroke: var(--primary-line); opacity: 0.85; }
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
  /* TASK-AR-592: transition is non-essential visual enhancement; gated below. */
  transition: fill var(--motion-fast, 0.14s) ease, stroke var(--motion-fast, 0.14s) ease;
}
/* TASK-AR-592: suppress non-essential live-map transitions under reduced-motion. */
@media (prefers-reduced-motion: reduce) {
  .live-map-node circle { transition: none; }
  .live-map-edge.is-pulsing { filter: none; }
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
  font-size: var(--font-size-ui-11);
  text-anchor: middle;
}
/* TASK-AR-588: node label and GitHub-Actions-style status icon for live-map. */
.live-map-node-label { fill: var(--muted); font-size: var(--font-size-ui-10); text-anchor: middle; }
.live-map-status-icon { fill: var(--ink); font-size: var(--font-size-ui-8); text-anchor: middle; }
.live-map-empty {
  padding: var(--space-viewport-gap) var(--space-4xl);
  text-align: center;
  color: var(--subtle);
}
.live-map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xl);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.live-map-legend li {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
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
/* --- 2D Office Map (TASK-AR-364) --- */
.office-map {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
}
.office-map-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2xl);
  flex-wrap: wrap;
}
.office-map-header h2 { margin: 0; }
.office-map-summary {
  margin: 0;
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.office-map-stage {
  border: 1px solid var(--office-room-line);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  background: var(--office-floor);
}
.office-map-grid {
  position: relative;
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  grid-template-rows: repeat(8, minmax(34px, 1fr));
  gap: var(--space-md);
  width: 100%;
  aspect-ratio: 3 / 2;
}
.office-room {
  position: relative;
  border: 1px solid var(--office-room-line);
  border-top: 3px solid var(--office-room-line);
  border-radius: var(--radius-lg);
  background: var(--office-room-bg);
  padding: var(--space-md) var(--space-lg);
  overflow: hidden;
}
.office-room.token-violet { border-top-color: var(--violet); }
.office-room.token-blue { border-top-color: var(--blue); }
.office-room.token-amber { border-top-color: var(--amber); }
.office-room.token-success { border-top-color: var(--success); }
.office-room.token-primary { border-top-color: var(--primary); }
.office-room-name {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.02em;
}
.office-room-count {
  font-size: var(--font-size-ui-10);
  color: var(--subtle);
}
.office-agent {
  position: absolute;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-hairline);
  width: 46px;
  text-align: center;
}
.office-agent-glyph {
  font-size: var(--font-size-ui-14);
  line-height: 1;
}
.office-agent-sprite {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-ui-10);
  font-weight: 700;
  color: var(--ink);
  background: var(--office-avatar-bg);
  border: 2px solid var(--office-room-line);
  /* Chibi sprite idle bob (TASK-AR-592 v2): a gentle, self-hosted CSS-only
     animation. Disabled under prefers-reduced-motion (see media query below). */
  animation: office-idle-bob 3.2s ease-in-out infinite;
}
.office-agent-sprite .chibi-sprite,
.office-agent-sprite .v3-sprite {
  width: 30px;
  height: 30px;
  display: block;
  image-rendering: pixelated;
}
/* Presence ring is a SECONDARY cue; the word badge below is the primary,
   non-color-only status signal (a11y / AR-588). */
.office-agent.presence-working .office-agent-sprite { border-color: var(--blue); }
.office-agent.presence-reviewing .office-agent-sprite { border-color: var(--amber); }
.office-agent.presence-in_meeting .office-agent-sprite { border-color: var(--violet); }
.office-agent.presence-online .office-agent-sprite { border-color: var(--success); }
.office-agent.presence-offline .office-agent-sprite { border-color: var(--office-room-line); opacity: 0.7; animation: none; }
/* Stagger the idle bob by presence so a roomful of agents doesn't bob in
   lockstep (subtle liveliness, still calm). */
.office-agent.presence-working .office-agent-sprite { animation-delay: 0s; }
.office-agent.presence-reviewing .office-agent-sprite { animation-delay: 0.5s; }
.office-agent.presence-in_meeting .office-agent-sprite { animation-delay: 1s; }
.office-agent.presence-online .office-agent-sprite { animation-delay: 1.5s; }
@keyframes office-idle-bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
@media (prefers-reduced-motion: reduce) {
  .office-agent-sprite { animation: none; }
}
.office-agent-status {
  font-size: var(--font-size-ui-9);
  font-weight: 600;
  color: var(--muted);
  letter-spacing: 0.02em;
  max-width: 46px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.office-agent-name {
  font-size: var(--font-size-ui-9);
  color: var(--muted);
  max-width: 46px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.office-map-empty {
  grid-column: 1 / -1;
  grid-row: 1 / -1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--subtle);
  font-size: var(--font-size-ui-13);
}
.office-map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3xl);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.office-map-legend li {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
}
.office-map-legend .legend-glyph { font-size: var(--font-size-ui-14); }
.activity-feed {
  position: fixed;
  right: 18px;
  bottom: 18px;
  z-index: 60;
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  max-width: 320px;
  pointer-events: none;
}
.activity-toast {
  pointer-events: auto;
  padding: var(--space-xl) var(--space-2xl);
  border: 1px solid var(--line);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius);
  background: var(--panel);
  box-shadow: var(--shadow-pop);
  font-size: var(--font-size-ui-12);
  color: var(--ink);
  opacity: 1;
  transition: opacity 0.4s ease, transform 0.4s ease;
}
.activity-toast.is-leaving { opacity: 0; transform: translateY(6px); }
.activity-toast.kind-message { border-left-color: var(--blue); }
.activity-toast.kind-assignment { border-left-color: var(--success); }
.activity-toast.kind-review { border-left-color: var(--amber); }
.activity-toast.kind-block { border-left-color: var(--danger); }
.activity-toast b { display: block; font-size: var(--font-size-ui-11); color: var(--muted); }
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
  gap: var(--space-xl);
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
  font-size: var(--font-size-ui-12);
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
  font-size: var(--font-size-ui-12);
  line-height: 1.35;
}
.task-card .task-id {
  color: var(--primary-hover);
  font-size: var(--font-size-ui-11);
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
  font-size: var(--font-size-ui-10);
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
  font-size: var(--font-size-ui-11);
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
  gap: var(--space-md);
  border-radius: var(--radius-pill);
  padding: var(--space-sm-half) var(--space-lg);
  border: 1px solid var(--teal-line);
  background: var(--teal-soft);
  color: var(--teal);
  font-size: var(--font-size-ui-12);
}
.pill.high { color: var(--red); border-color: var(--danger-line); background: var(--danger-soft); }
.pill.medium { color: var(--amber); border-color: var(--warning-line); background: var(--warning-soft); }
.pill.low { color: var(--teal); }
.agent-progress,
.meta-grid {
  display: grid;
  gap: var(--space-lg);
}
.agent-progress-meta,
.meta-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.agent-progress-meta {
  display: grid;
  gap: var(--space-lg);
  color: var(--muted);
  font-size: var(--font-size-ui-12);
}
.progress-track {
  height: 7px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--progress-track);
}
.progress-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  background: var(--progress-fill);
}
.work-toolbar {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) minmax(150px, 0.4fr) auto auto;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}
.work-staleness {
  color: var(--subtle);
  font-size: var(--font-size-ui-11);
  margin-bottom: var(--space-lg);
  overflow-wrap: anywhere;
}
.work-facets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}
.facet-group {
  min-width: 0;
  margin: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-md) var(--space-lg);
}
.facet-group legend {
  color: var(--subtle);
  font-size: var(--font-size-ui-10);
  font-weight: 800;
  text-transform: uppercase;
  padding: 0 var(--space-sm);
}
.facet-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  max-width: 460px;
}
.facet-option {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm-half);
  border: 1px solid var(--line);
  border-radius: var(--radius-pill);
  padding: var(--space-xs-half) var(--space-lg-half);
  color: var(--muted);
  font-size: var(--font-size-ui-11);
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
  gap: var(--space-xl);
  align-items: start;
}
.work-tree {
  display: grid;
  gap: var(--space-sm);
  min-width: 0;
}
.work-node {
  display: grid;
  gap: var(--space-sm);
  min-width: 0;
}
.work-node-children {
  display: grid;
  gap: var(--space-sm);
  margin-left: var(--space-5xl);
  min-width: 0;
}
.work-node-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-lg);
  width: 100%;
  min-width: 0;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--raise);
  color: var(--ink);
  padding: var(--space-lg) var(--space-xl);
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
  padding: var(--space-xs) var(--space-md);
  border-color: transparent;
  background: transparent;
  box-shadow: none;
  color: var(--muted);
  font-size: var(--font-size-ui-11);
}
.work-node-number {
  color: var(--primary-hover);
  font-family: var(--font-mono);
  font-size: var(--font-size-ui-11);
  white-space: nowrap;
}
.work-node-id {
  color: var(--ink);
  font-size: var(--font-size-ui-12);
  font-weight: 700;
  overflow-wrap: anywhere;
}
.work-node-title {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  line-height: 1.3;
  min-width: 0;
  flex: 1 1 180px;
  overflow-wrap: anywhere;
}
.rollup-badge {
  border: 1px solid var(--teal-line);
  border-radius: var(--radius-pill);
  background: var(--teal-soft);
  color: var(--teal);
  font-size: var(--font-size-ui-11);
  padding: var(--space-xs-half) var(--space-lg);
  white-space: nowrap;
}
.evidence-badge {
  border: 1px solid var(--primary-line);
  border-radius: var(--radius-pill);
  background: var(--primary-soft);
  color: var(--primary);
  font-size: var(--font-size-ui-11);
  padding: var(--space-xs-half) var(--space-lg);
  white-space: nowrap;
}
.work-node-detail {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: var(--space-xl);
  display: grid;
  gap: var(--space-lg);
  min-width: 0;
}
.work-node-detail h3 {
  font-size: var(--font-size-ui-14);
  overflow-wrap: anywhere;
}
.work-node-detail p {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
  line-height: 1.4;
}
.work-detail-meta {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-md);
}
.work-detail-meta > span {
  min-width: 0;
  border: 1px solid var(--tile-line);
  border-radius: var(--radius-sm);
  background: var(--tile);
  padding: var(--space-md);
}
.work-detail-meta strong {
  display: block;
  margin-top: var(--space-sm);
  color: var(--ink);
  font-size: var(--font-size-ui-11);
  line-height: 1.2;
  overflow-wrap: anywhere;
}
.evidence-ref {
  display: block;
  color: var(--subtle);
  font-size: var(--font-size-ui-11);
  overflow-wrap: anywhere;
}
.meeting-grid {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(0, 1.6fr);
  gap: var(--space-2xl);
  align-items: start;
}
.meeting-roster,
.meeting-room {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: var(--space-2xl);
  min-width: 0;
}
.meeting-roster h2,
.meeting-room h2 {
  font-size: var(--font-size-ui-14);
  margin-bottom: var(--space-md);
}
.meeting-hint {
  color: var(--muted);
  font-size: var(--font-size-ui-11);
  line-height: 1.4;
  margin-bottom: var(--space-lg);
}
.meeting-card-list,
.meeting-participant-list {
  display: grid;
  gap: var(--space-md);
}
.meeting-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--tile);
  padding: var(--space-lg);
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
  font-size: var(--font-size-ui-12);
  overflow-wrap: anywhere;
}
.meeting-card-meta {
  color: var(--muted);
  font-size: var(--font-size-ui-10);
  white-space: nowrap;
}
.meeting-dropzone {
  border: 2px dashed var(--line-strong);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: var(--space-2xl);
  min-height: 96px;
  margin-bottom: var(--space-xl);
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
  font-size: var(--font-size-ui-12);
}
.meeting-dropzone.has-participants .meeting-dropzone-empty {
  display: none;
}
.meeting-participant {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  border: 1px solid var(--accent);
  border-radius: var(--radius-md);
  background: var(--info-soft);
  padding: var(--space-lg);
}
.meeting-participant button {
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--subtle);
  cursor: pointer;
  font-size: var(--font-size-ui-12);
  padding: var(--space-xs) var(--space-lg);
}
.meeting-config {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-lg);
  align-items: end;
}
.meeting-field {
  display: grid;
  gap: var(--space-sm);
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  min-width: 0;
}
.meeting-field input,
.meeting-field select {
  min-width: 0;
}
.meeting-validation {
  margin-top: var(--space-lg);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-3xl);
  align-items: start;
}
.channels-sidebar {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  padding: var(--space-xl);
}
.channels-heading {
  font-size: var(--font-size-ui-12);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--subtle);
  margin-bottom: var(--space-lg);
}
.channels-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.channel-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  width: 100%;
  border: 0;
  background: transparent;
  color: var(--ink);
  text-align: left;
  padding: var(--space-md-half) var(--space-lg-half);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: var(--font-size-ui-13);
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
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  background: var(--raise);
  border-radius: var(--radius-pill);
  padding: var(--space-hairline) var(--space-md-half);
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
  gap: var(--space-xl);
  padding: var(--space-2xl) var(--space-3xl);
  border-bottom: 1px solid var(--line);
}
.channels-active-name {
  font-size: var(--font-size-ui-16);
}
.channels-active-meta {
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.channels-threads {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2xl) var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-3xl);
}
.channel-thread {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--inset-soft);
  padding: var(--space-xl) var(--space-2xl);
}
.channel-thread-head {
  display: flex;
  justify-content: space-between;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}
.channel-thread-title {
  font-weight: 600;
  font-size: var(--font-size-ui-13);
}
.channel-thread-task {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.channel-message {
  display: flex;
  gap: var(--space-lg-half);
  padding: var(--space-md) 0;
}
.channel-message + .channel-message {
  border-top: 1px solid var(--line);
}
.channel-avatar {
  flex: 0 0 auto;
  width: 30px;
  height: 30px;
  border-radius: var(--radius-pill);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-ui-11);
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
  gap: var(--space-lg);
}
.channel-sender {
  font-weight: 600;
  font-size: var(--font-size-ui-13);
  color: var(--role-color, var(--ink));
}
.channel-ts {
  font-size: var(--font-size-ui-11);
  color: var(--subtle);
}
.channel-message-text {
  font-size: var(--font-size-ui-13);
  color: var(--ink);
  line-height: 1.4;
  margin-top: var(--space-xs);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
.channel-message-actions { display: flex; gap: var(--space-md); margin-top: var(--space-sm); }
.channel-msg-action {
  font-size: var(--font-size-ui-11);
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-pill);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--muted);
  cursor: pointer;
}
.channel-msg-action:hover { border-color: var(--primary-line); color: var(--primary); }
.channels-empty {
  color: var(--muted);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-5xl);
  text-align: center;
}
.channels-input {
  border-top: 1px solid var(--line);
  padding: var(--space-xl) var(--space-3xl) var(--space-2xl);
  background: var(--panel);
}
.channels-input-label {
  display: block;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  margin-bottom: var(--space-md);
}
.channels-input-label code {
  background: var(--raise);
  border-radius: var(--radius-sm-half);
  padding: 0 var(--space-sm);
}
.channels-input-row {
  display: flex;
  gap: var(--space-lg);
}
.channels-input-row input {
  border: 1px solid var(--line-strong);
  border-radius: var(--radius);
  background: var(--surface-raised);
  color: var(--ink);
  padding: var(--space-lg) var(--space-xl);
  font-size: var(--font-size-ui-13);
}
#channels-input-target {
  flex: 0 0 150px;
}
#channels-input-box {
  flex: 1;
}
.channels-input-hint {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  min-height: 14px;
  margin-top: var(--space-md);
}
.channels-input-hint.is-error {
  color: var(--danger);
}
.channels-input-hint.is-ok {
  color: var(--success);
}
.detail-panel {
  padding: var(--space-3xl);
  align-self: start;
  position: sticky;
  top: 88px;
}
.detail-panel h2 {
  font-size: var(--font-size-ui-18);
  line-height: 1.2;
  letter-spacing: 0;
  overflow-wrap: anywhere;
}
.detail-panel p {
  margin-top: var(--space-lg);
  color: var(--muted);
  line-height: 1.45;
}
.detail-empty {
  color: var(--muted);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-5xl);
}
.meta-grid {
  margin: var(--space-2xl) 0;
}
.meta-grid div {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-lg);
  background: var(--inset-soft);
}
.meta-grid span {
  display: block;
  color: var(--muted);
  font-size: var(--font-size-ui-11);
}
.meta-grid strong {
  display: block;
  margin-top: var(--space-sm);
  font-size: var(--font-size-ui-12);
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
  padding: var(--space-xl);
}
.empty {
  color: var(--muted);
  font-style: italic;
  padding: var(--space-lg);
}
.hidden { display: none !important; }
/* TASK-AR-332: file attachments (drop zone, thumbnails, lightbox, preview) */
.attachments {
  margin-top: var(--space-3xl);
  border-top: 1px solid var(--line);
  padding-top: var(--space-2xl);
}
.attachments-title {
  font-size: var(--font-size-ui-12);
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: var(--space-lg);
}
.attach-dropzone {
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  text-align: center;
  color: var(--muted);
  font-size: var(--font-size-ui-12);
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
  margin-top: var(--space-sm);
  font-size: var(--font-size-ui-11);
  color: var(--subtle);
}
.attach-error {
  margin-top: var(--space-lg);
  color: var(--danger);
  font-size: var(--font-size-ui-12);
}
.attach-list {
  list-style: none;
  margin: var(--space-xl) 0 0;
  padding: 0;
  display: grid;
  gap: var(--space-lg);
}
.attach-item {
  display: flex;
  gap: var(--space-xl);
  align-items: center;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-lg);
  background: var(--tile);
}
.attach-thumb {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  object-fit: cover;
  border: 1px solid var(--line);
  background: var(--panel);
  cursor: zoom-in;
  flex: 0 0 auto;
}
.attach-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--line);
  background: var(--panel);
  color: var(--muted);
  font-size: var(--font-size-ui-11);
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
  font-size: var(--font-size-ui-13);
  overflow-wrap: anywhere;
  color: var(--ink);
}
.attach-meta {
  display: block;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  margin-top: var(--space-xs);
}
.attach-actions {
  display: flex;
  gap: var(--space-md);
  flex: 0 0 auto;
}
.attach-actions a,
.attach-actions button {
  font-size: var(--font-size-ui-11);
  padding: var(--space-sm) var(--space-lg);
  border-radius: var(--radius-sm);
  border: 1px solid var(--line-strong);
  background: var(--surface-raised);
  color: var(--primary);
  cursor: pointer;
  text-decoration: none;
}
.attach-preview {
  margin-top: var(--space-lg);
  max-width: 100%;
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--pre-bg);
  color: var(--pre-ink);
  padding: var(--space-xl);
  font-size: var(--font-size-ui-12);
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
  padding: var(--space-7xl);
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
  font-size: var(--font-size-ui-22);
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
  gap: var(--space-xl);
  align-items: center;
  margin-bottom: var(--space-2xl);
}
.tsboard-swimlane-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
.tsboard-staleness {
  color: var(--subtle);
  font-size: var(--font-size-ui-12);
  margin-bottom: var(--space-2xl);
}
.tsboard-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-3xl);
}
.tsboard-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}
.tsboard-card.bucket-completed { border-left: 3px solid var(--success); }
.tsboard-card.bucket-in_progress { border-left: 3px solid var(--blue); }
.tsboard-card.bucket-planned { border-left: 3px solid var(--subtle); }
.tsboard-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-xl);
}
.tsboard-title { display: flex; flex-direction: column; gap: var(--space-xs); }
.tsboard-title span { color: var(--muted); font-size: var(--font-size-ui-13); }
.tsboard-toggle {
  background: var(--surface-raised);
  border: 1px solid var(--line);
  color: var(--ink);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-lg);
  cursor: pointer;
}
.tsboard-card-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-13);
}
.tsboard-distribution { display: flex; flex-wrap: wrap; gap: var(--space-md); }
.dist-chip {
  border-radius: var(--radius-pill);
  padding: var(--space-xs) var(--space-lg);
  font-size: var(--font-size-ui-11);
  border: 1px solid var(--line-strong);
}
.dist-completed { color: var(--success); }
.dist-in_progress { color: var(--blue); }
.dist-planned { color: var(--muted); }
.agent-stack { display: flex; gap: var(--space-sm); flex-wrap: wrap; }
.agent-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--surface-raised);
  border: 1px solid var(--line-strong);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-ui-10);
}
.agent-stack-empty { color: var(--subtle); font-size: var(--font-size-ui-12); }
.tsboard-activity { list-style: none; margin: 0; padding: 0; font-size: var(--font-size-ui-12); }
.tsboard-activity li { color: var(--muted); }
.tsboard-add-row { display: flex; gap: var(--space-md); }
.tsboard-add-title { flex: 1; }
.tsboard-add-task {
  background: var(--primary);
  border: none;
  color: var(--ink);
  border-radius: var(--radius-sm);
  padding: var(--space-md) var(--space-xl);
  cursor: pointer;
}
.tsboard-children { display: flex; flex-direction: column; gap: var(--space-sm); }
.tsboard-child {
  display: grid;
  grid-template-columns: auto 90px 1fr auto auto auto;
  gap: var(--space-lg);
  align-items: center;
  padding: var(--space-md);
  border-top: 1px solid var(--line);
  cursor: pointer;
  font-size: var(--font-size-ui-12);
}
.tsboard-child:hover { background: var(--surface-raised); }
.tsboard-child-id { font-family: var(--font-mono); color: var(--muted); }
.phase-chip {
  border-radius: var(--radius-pill);
  padding: var(--space-hairline) var(--space-md-half);
  font-size: var(--font-size-ui-10);
  text-transform: uppercase;
}
.phase-plan { background: var(--raise-strong); color: var(--muted); }
.phase-work { background: var(--info-soft); color: var(--blue); }
.phase-review { background: var(--warning-soft); color: var(--amber); }
.phase-done { background: var(--success-soft); color: var(--success); }
.tsboard-swimlanes { display: flex; flex-direction: column; gap: var(--space-4xl); }
.tsboard-swimlane {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-2xl);
  background: var(--panel);
}
.tsboard-swimlane-header { display: flex; gap: var(--space-lg); align-items: baseline; margin-bottom: var(--space-lg); }
.tsboard-swimlane-header span { color: var(--muted); font-size: var(--font-size-ui-13); }
.tsboard-swimlane-cols {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-lg);
}
.tsboard-swim-col { background: var(--surface-raised); border-radius: var(--radius-sm); padding: var(--space-lg); }
.tsboard-swim-col header { font-size: var(--font-size-ui-12); color: var(--muted); margin-bottom: var(--space-md); }
.tsboard-swim-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-md);
  background: var(--panel);
  border-radius: var(--radius-sm-half);
  margin-bottom: var(--space-md);
  cursor: pointer;
  font-size: var(--font-size-ui-12);
}
.tsboard-swim-card code { color: var(--muted); }

.team-toolbar {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
  align-items: center;
}
.team-online-toggle { display: flex; gap: var(--space-md); align-items: center; color: var(--muted); font-size: var(--font-size-ui-13); }
.team-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin: 0 0 var(--space-2xl); }
.team-org { display: flex; flex-direction: column; gap: var(--space-5xl); }
.team-group {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  background: var(--panel);
}
.team-group-header { display: flex; gap: var(--space-xl); align-items: baseline; margin-bottom: var(--space-2xl); }
.team-group-header b { font-size: var(--font-size-ui-15); }
.team-group-header span { color: var(--muted); font-size: var(--font-size-ui-13); }
.team-role-badges { display: flex; flex-wrap: wrap; gap: var(--space-md); margin-bottom: var(--space-2xl); }
.team-role-badge {
  border-radius: var(--radius-pill);
  padding: var(--space-xs) var(--space-lg-half);
  font-size: var(--font-size-ui-11);
  border: 1px solid var(--line-strong);
  color: var(--muted);
  background: var(--panel);
  cursor: pointer;
}
.team-role-badge:hover { color: var(--nav-active-text); border-color: var(--primary-line); background: var(--primary-soft); }
.team-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-3xl);
}
.agent-character-card {
  background: var(--panel-strong);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}
.agent-character-card.presence-working { border-left: 3px solid var(--blue); }
.agent-character-card.presence-reviewing { border-left: 3px solid var(--amber); }
.agent-character-card.presence-in_meeting { border-left: 3px solid var(--violet); }
.agent-character-card.presence-online { border-left: 3px solid var(--success); }
.agent-character-card.presence-offline { border-left: 3px solid var(--subtle); }
.agent-character-header { display: flex; gap: var(--space-2xl); align-items: center; }
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
  font-size: var(--font-size-ui-14);
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
.agent-character-identity { display: flex; flex-direction: column; gap: var(--space-xs); min-width: 0; }
.agent-character-identity b { overflow-wrap: anywhere; }
.agent-character-identity span { color: var(--muted); font-size: var(--font-size-ui-12); }
.agent-character-level {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.agent-character-level strong { color: var(--ink); }
.agent-character-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-12);
}
.agent-character-task { font-size: var(--font-size-ui-12); color: var(--muted); }
.agent-character-task code { color: var(--ink); }
.agent-character-activity { list-style: none; margin: 0; padding: 0; font-size: var(--font-size-ui-12); color: var(--muted); }

/* ===== Growth system (TASK-AR-363) =====
 * Project level / business-stage / XP surfaces. All colors are semantic tokens
 * (--growth-*, status tokens, --progress-fill); no raw hex/rgba is emitted, so
 * the tokenization gate stays green. */
.growth-header { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-2xl); flex-wrap: wrap; }
.growth-toggle { display: inline-flex; align-items: center; gap: var(--space-md); color: var(--muted); font-size: var(--font-size-ui-13); cursor: pointer; }
.growth-disabled { color: var(--muted); font-size: var(--font-size-ui-13); }
.growth-body { display: flex; flex-direction: column; gap: var(--space-4xl); }
.growth-hero {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-3xl);
}
.growth-hero-card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-4xl);
  background: var(--panel-strong);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
.growth-hero-card .growth-hero-label { color: var(--muted); font-size: var(--font-size-ui-12); text-transform: uppercase; letter-spacing: 0.04em; }
.growth-level-value { font-size: var(--font-size-ui-28); font-weight: 700; color: var(--ink); }
.growth-stage-chip {
  align-self: flex-start;
  border-radius: var(--radius-pill);
  padding: var(--space-sm) var(--space-2xl);
  font-size: var(--font-size-ui-13);
  font-weight: 600;
  color: var(--on-accent);
  background: var(--growth-stage);
}
.growth-ladder { list-style: none; display: flex; flex-wrap: wrap; gap: var(--space-md); margin: var(--space-md) 0 0; padding: 0; font-size: var(--font-size-ui-11); }
.growth-ladder li { color: var(--muted); border: 1px solid var(--line); border-radius: var(--radius-pill); padding: var(--space-hairline) var(--space-lg); }
.growth-ladder li.is-current { color: var(--on-accent); background: var(--growth-stage); border-color: var(--growth-stage); }
.growth-xp-bar { background: var(--growth-xp); height: 100%; border-radius: inherit; }
.growth-formula, .growth-efficiency, .growth-teams, .growth-agents {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  background: var(--panel);
}
.growth-section-title { font-size: var(--font-size-ui-13); font-weight: 600; margin: 0 0 var(--space-xl); color: var(--ink); }
.growth-formula-rows { display: flex; flex-direction: column; gap: var(--space-md); font-size: var(--font-size-ui-13); }
.growth-formula-row { display: flex; justify-content: space-between; gap: var(--space-xl); color: var(--muted); }
.growth-formula-row strong { color: var(--ink); }
.growth-formula-total { border-top: 1px solid var(--line); margin-top: var(--space-lg); padding-top: var(--space-lg); font-weight: 600; }
.growth-note { color: var(--muted); font-size: var(--font-size-ui-12); margin: var(--space-lg) 0 0; }
.growth-stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: var(--space-xl); }
.growth-stat { border: 1px solid var(--line); border-radius: var(--radius-md); padding: var(--space-xl); background: var(--tile); }
.growth-stat .growth-stat-label { color: var(--muted); font-size: var(--font-size-ui-11); }
.growth-stat .growth-stat-value { font-size: var(--font-size-ui-18); font-weight: 600; color: var(--growth-efficiency); }
.growth-row { display: flex; justify-content: space-between; align-items: center; gap: var(--space-xl); padding: var(--space-md) 0; border-bottom: 1px solid var(--line); font-size: var(--font-size-ui-13); }
.growth-row:last-child { border-bottom: 0; }
.growth-row .growth-row-meta { color: var(--muted); font-size: var(--font-size-ui-12); }

/* ===== Workload heatmap (TASK-AR-337) =====
 * Cell color is ALWAYS a semantic token (--heat-*); per-cell load is expressed
 * only as opacity via the inline --cell-intensity custom property, so no raw
 * rgba/hex is ever emitted (tokenization gate stays green). */
.workload-header { display: flex; align-items: baseline; gap: var(--space-2xl); }
.workload-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin: 0; }
.workload-toolbar { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2xl); margin: var(--space-2xl) 0; flex-wrap: wrap; }
.workload-scope { display: inline-flex; border: 1px solid var(--line-strong); border-radius: var(--radius-pill); overflow: hidden; }
.workload-scope-btn { background: var(--panel); color: var(--muted); border: 0; padding: var(--space-md) var(--space-3xl); font-size: var(--font-size-ui-13); cursor: pointer; }
.workload-scope-btn.is-active { background: var(--primary-soft); color: var(--nav-active-text); font-weight: 600; }
.workload-legend { list-style: none; display: flex; gap: var(--space-2xl); margin: 0; padding: 0; font-size: var(--font-size-ui-12); color: var(--muted); }
.workload-legend li { display: inline-flex; align-items: center; gap: var(--space-md); }
.workload-legend .heat-swatch { width: 14px; height: 14px; border-radius: var(--radius-xs); border: 1px solid var(--line); }
.heat-swatch.band-idle { background: var(--heat-idle); }
.heat-swatch.band-normal { background: var(--heat-normal); }
.heat-swatch.band-busy { background: var(--heat-busy); }
.heat-swatch.band-overload { background: var(--heat-overload); }
.workload-grid { display: grid; gap: var(--space-sm); overflow-x: auto; }
.workload-row { display: grid; grid-template-columns: var(--heat-label-col, 200px) 1fr; gap: var(--space-sm); align-items: stretch; }
.workload-row.is-head .workload-label { color: var(--muted); font-size: var(--font-size-ui-11); text-transform: uppercase; letter-spacing: 0.04em; }
.workload-label { display: flex; flex-direction: column; justify-content: center; padding: var(--space-md) var(--space-xl); font-size: var(--font-size-ui-13); overflow-wrap: anywhere; }
.workload-label small { color: var(--muted); font-size: var(--font-size-ui-11); }
.workload-cells { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(56px, 1fr); gap: var(--space-sm); }
.workload-cell {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-ui-13);
  font-weight: 600;
  color: var(--ink);
  cursor: pointer;
  background: var(--panel);
}
.workload-cell.is-head { background: transparent; border: 0; color: var(--muted); font-size: var(--font-size-ui-11); font-weight: 500; cursor: default; }
/* The fill layer is a single token color; opacity (--cell-intensity) is the
 * only per-cell variable, so the rendered color is always var(--heat-base). */
.workload-cell .heat-fill {
  position: absolute;
  inset: 0;
  border-radius: var(--radius-sm);
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
.workload-empty { color: var(--muted); padding: var(--space-6xl); }

/* ===== Custom properties / labels / automation / triage (TASK-AR-331) ===== */
/* Label colors flow through a FIXED token palette. The JS only ever sets
 * data-color="<token>"; these rules resolve each token via var(--token) so no
 * raw/user CSS is ever injected (tokenization gate stays green). */
.label-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-xs) var(--space-xl);
  border-radius: var(--radius-pill);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-lg);
  align-items: center;
  margin-bottom: var(--space-3xl);
}
.config-form input,
.config-form select {
  padding: var(--space-lg) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.config-form button {
  padding: var(--space-lg) var(--space-3xl);
  border-radius: var(--radius);
  border: 1px solid var(--primary);
  background: var(--primary);
  color: var(--on-accent);
  font: inherit;
  cursor: pointer;
}
.config-form button:hover { background: var(--primary-hover); }
.config-form-arrow { color: var(--muted); font-weight: 700; }
.config-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin-bottom: var(--space-2xl); }
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-2xl);
}
.config-card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: var(--space-2xl) var(--space-3xl);
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}
.config-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
}
.config-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md) var(--space-3xl);
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.config-card-meta strong { color: var(--ink); }
.config-card-actions { display: flex; gap: var(--space-lg); flex-wrap: wrap; }
.config-action {
  padding: var(--space-sm) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: var(--font-size-ui-12);
  cursor: pointer;
}
.config-action:hover { background: var(--raise-strong); }
.rule-state {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-pill);
  border: 1px solid var(--line);
}
.rule-state.is-active { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
.rule-state.is-inactive { color: var(--muted); background: var(--raise); }
.rule-state.is-invalid { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.rule-flow {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-13);
  flex-wrap: wrap;
}
.rule-token {
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius);
  background: var(--primary-soft);
  color: var(--primary-hover);
  font-weight: 600;
}
.rule-flow-arrow { color: var(--muted); }
/* External notification routing (TASK-AR-365). All colors are theme tokens. */
.routing-status { color: var(--muted); font-size: var(--font-size-ui-13); margin-bottom: var(--space-md); }
.routing-status strong { color: var(--ink); }
.routing-hint { color: var(--muted); font-size: var(--font-size-ui-12); margin: 0 0 var(--space-xl); max-width: 70ch; }
.routing-legend { display: flex; flex-wrap: wrap; gap: var(--space-lg) var(--space-4xl); list-style: none; padding: 0; margin: 0 0 var(--space-2xl); font-size: var(--font-size-ui-12); color: var(--muted); }
.routing-legend li { display: flex; align-items: center; gap: var(--space-md); }
.routing-dot { width: 10px; height: 10px; border-radius: var(--radius-pill); display: inline-block; background: var(--muted); }
.routing-dot-immediate { background: var(--danger); }
.routing-dot-aggregate { background: var(--amber); }
.routing-dot-digest { background: var(--success); }
.routing-token { font-size: var(--font-size-ui-11); font-weight: 600; padding: var(--space-xs) var(--space-lg); border-radius: var(--radius-pill); border: 1px solid var(--line); color: var(--muted); background: var(--raise); }
.routing-token-immediate { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.routing-token-aggregate { color: var(--warning); background: var(--warning-soft); border-color: var(--warning-line); }
.routing-token-digest { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
/* Calendar / scheduling (TASK-AR-335). All colors are theme tokens. */
.calendar-header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-2xl); flex-wrap: wrap; margin-bottom: var(--space-xl); }
.calendar-header h2 { margin: 0; font-size: var(--font-size-ui-16); color: var(--ink); }
.calendar-nav { display: flex; align-items: center; gap: var(--space-lg); flex-wrap: wrap; }
.calendar-period { font-weight: 600; color: var(--ink); min-width: 140px; text-align: center; }
.calendar-nav-btn, .calendar-mode {
  padding: var(--space-sm) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: var(--font-size-ui-12);
  cursor: pointer;
}
.calendar-nav-btn:hover, .calendar-mode:hover { background: var(--raise-strong); }
.calendar-mode.is-active { background: var(--primary-soft); color: var(--primary-hover); border-color: var(--primary-line); }
.calendar-view-toggle { display: inline-flex; gap: var(--space-sm); }
.calendar-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin-bottom: var(--space-xl); }
.calendar-summary strong { color: var(--ink); }
.calendar-reminders { display: flex; flex-direction: column; gap: var(--space-md); margin-bottom: var(--space-2xl); }
.calendar-reminder {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-13);
  padding: var(--space-md) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--warning-line);
  background: var(--warning-soft);
  color: var(--warning);
}
.calendar-reminder.is-overdue { border-color: var(--danger-line); background: var(--danger-soft); color: var(--danger); }
.calendar-reminder strong { color: var(--ink); }
.calendar-reminder-badge {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-pill);
  border: 1px solid currentColor;
}
.calendar-legend { display: flex; flex-wrap: wrap; gap: var(--space-lg) var(--space-4xl); list-style: none; padding: 0; margin: 0 0 var(--space-2xl); font-size: var(--font-size-ui-12); color: var(--muted); }
.calendar-legend li { display: flex; align-items: center; gap: var(--space-md); }
.calendar-dot { width: 10px; height: 10px; border-radius: var(--radius-pill); display: inline-block; background: var(--muted); }
.calendar-dot-milestone { background: var(--violet); }
.calendar-dot-meeting { background: var(--primary); }
.calendar-dot-completion { background: var(--success); }
.calendar-dot-deadline { background: var(--warning); }
.calendar-dot-scheduled { background: var(--teal); }
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-sm);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: var(--space-md);
}
.calendar-weekday { font-size: var(--font-size-ui-11); font-weight: 600; color: var(--muted); text-align: center; padding: var(--space-sm) 0; text-transform: uppercase; }
.calendar-cell {
  min-height: 84px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--tile);
  padding: var(--space-sm) var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs-half);
  overflow: hidden;
}
.calendar-cell.is-outside { background: var(--inset-soft); color: var(--subtle); }
.calendar-cell.is-today { border-color: var(--primary-line); box-shadow: var(--focus); }
.calendar-cell-date { font-size: var(--font-size-ui-12); font-weight: 600; color: var(--ink); }
.calendar-cell.is-outside .calendar-cell-date { color: var(--subtle); }
.calendar-event {
  font-size: var(--font-size-ui-11);
  padding: var(--space-hairline) var(--space-md);
  border-radius: var(--radius-pill);
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
.calendar-schedule-panel { margin-top: var(--space-5xl); }
.calendar-schedule-panel h3 { margin: 0 0 var(--space-sm); font-size: var(--font-size-ui-14); color: var(--ink); }
.calendar-hint { color: var(--muted); font-size: var(--font-size-ui-12); margin: 0 0 var(--space-2xl); }
.calendar-cron-badge { font-family: var(--font-mono); font-size: var(--font-size-ui-11); color: var(--teal); }
/* ===== TASK-AR-338: notification center + daily brief ===== */
.sidebar-badge {
  margin-left: auto;
  min-width: 18px;
  text-align: center;
  font-size: var(--font-size-ui-11);
  font-weight: 700;
  padding: var(--space-hairline) var(--space-md);
  border-radius: var(--radius-pill);
  background: var(--danger);
  color: var(--tile);
}
.inbox-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(260px, 1fr); gap: var(--space-4xl); }
@media (max-width: 960px) { .inbox-grid { grid-template-columns: 1fr; } }
.inbox-header { display: flex; align-items: baseline; gap: var(--space-2xl); flex-wrap: wrap; margin-bottom: var(--space-lg); }
.inbox-header h2 { margin: 0; }
.inbox-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin: 0; }
.inbox-summary strong { color: var(--ink); }
.inbox-toolbar { display: flex; gap: var(--space-xl); flex-wrap: wrap; align-items: center; margin-bottom: var(--space-lg); }
.inbox-field { display: flex; flex-direction: column; gap: var(--space-xs); font-size: var(--font-size-ui-11); color: var(--muted); }
.inbox-field select,
.inbox-subscribe input,
.inbox-subscribe select {
  padding: var(--space-md-half) var(--space-lg-half);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.inbox-checkbox { display: flex; align-items: center; gap: var(--space-sm); font-size: var(--font-size-ui-12); color: var(--muted); }
.inbox-action {
  padding: var(--space-md-half) var(--space-2xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  cursor: pointer;
}
.inbox-action:hover { border-color: var(--primary-line); }
.inbox-action-hint { font-size: var(--font-size-ui-12); color: var(--muted); margin: 0 0 var(--space-lg); min-height: 14px; }
.inbox-action-hint.is-ok { color: var(--success); }
.inbox-action-hint.is-error { color: var(--danger); }
.inbox-list { display: flex; flex-direction: column; gap: var(--space-lg); }
.inbox-item {
  display: flex;
  gap: var(--space-xl);
  align-items: flex-start;
  padding: var(--space-xl) var(--space-2xl);
  border: 1px solid var(--line);
  border-left-width: 3px;
  border-radius: var(--radius);
  background: var(--tile);
}
.inbox-item.is-unread { background: var(--primary-soft); }
.inbox-item.is-muted { opacity: 0.6; }
.inbox-item.is-highlighted { box-shadow: var(--focus); }
.inbox-item[data-severity="overdue"],
.inbox-item[data-severity="blocked"],
.inbox-item[data-severity="error"] { border-left-color: var(--danger); }
.inbox-item[data-severity="approval"],
.inbox-item[data-severity="due_soon"] { border-left-color: var(--warning); }
.inbox-item[data-severity="mention"] { border-left-color: var(--primary); }
.inbox-item[data-severity="info"] { border-left-color: var(--info); }
.inbox-item-main { flex: 1; min-width: 0; }
.inbox-item-title { font-weight: 600; color: var(--ink); font-size: var(--font-size-ui-13); }
.inbox-item-body { color: var(--muted); font-size: var(--font-size-ui-12); margin-top: var(--space-xs); word-break: break-word; }
.inbox-item-meta { display: flex; gap: var(--space-lg); flex-wrap: wrap; margin-top: var(--space-md); font-size: var(--font-size-ui-11); color: var(--subtle); }
.inbox-badge {
  font-size: var(--font-size-ui-10);
  font-weight: 700;
  text-transform: uppercase;
  padding: var(--space-xs) var(--space-md-half);
  border-radius: var(--radius-pill);
  border: 1px solid currentColor;
}
.inbox-badge[data-severity="overdue"],
.inbox-badge[data-severity="blocked"],
.inbox-badge[data-severity="error"] { color: var(--danger); background: var(--danger-soft); }
.inbox-badge[data-severity="approval"],
.inbox-badge[data-severity="due_soon"] { color: var(--warning); background: var(--warning-soft); }
.inbox-badge[data-severity="mention"] { color: var(--primary); background: var(--primary-soft); }
.inbox-badge[data-severity="info"] { color: var(--info); background: var(--info-soft); }
.inbox-item-actions { display: flex; flex-direction: column; gap: var(--space-sm); }
.inbox-item-actions button {
  font-size: var(--font-size-ui-11);
  padding: var(--space-xs-half) var(--space-lg);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  cursor: pointer;
  white-space: nowrap;
}
.inbox-item-actions button:hover { border-color: var(--primary-line); }
.inbox-side { display: flex; flex-direction: column; gap: var(--space-4xl); }
.daily-brief,
.inbox-subscribe {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: var(--space-3xl) var(--space-4xl);
}
.daily-brief-header { display: flex; align-items: baseline; justify-content: space-between; }
.daily-brief-header h3 { margin: 0; font-size: var(--font-size-ui-14); color: var(--ink); }
.daily-brief-date { font-size: var(--font-size-ui-12); color: var(--muted); }
.daily-brief-section { margin-top: var(--space-xl); }
.daily-brief-section-title { font-size: var(--font-size-ui-11); font-weight: 700; text-transform: uppercase; color: var(--subtle); margin-bottom: var(--space-sm); }
.daily-brief-section.is-completed .daily-brief-section-title { color: var(--success); }
.daily-brief-section.is-blocked .daily-brief-section-title { color: var(--danger); }
.daily-brief-section.is-decisions .daily-brief-section-title { color: var(--violet); }
.daily-brief-section.is-next .daily-brief-section-title { color: var(--primary); }
.daily-brief-item {
  display: block;
  font-size: var(--font-size-ui-12);
  color: var(--ink);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--line);
  cursor: pointer;
}
.daily-brief-item:last-child { border-bottom: none; }
.daily-brief-item:hover { color: var(--primary); }
.daily-brief-item code { font-size: var(--font-size-ui-11); color: var(--muted); }
.daily-brief-empty { font-size: var(--font-size-ui-12); color: var(--subtle); }
.inbox-subscribe h3 { margin: 0 0 var(--space-sm); font-size: var(--font-size-ui-14); color: var(--ink); }
.inbox-hint { color: var(--muted); font-size: var(--font-size-ui-12); margin: 0 0 var(--space-xl); }
.triage-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin-bottom: var(--space-xl); }
.triage-summary strong { color: var(--ink); }
.triage-toolbar { display: flex; gap: var(--space-lg); margin-bottom: var(--space-2xl); flex-wrap: wrap; }
.triage-toolbar input,
.triage-toolbar select {
  padding: var(--space-lg) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.triage-reason {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-pill);
  border: 1px solid var(--warning-line);
  color: var(--warning);
  background: var(--warning-soft);
}
.triage-reason[data-reason="unclassified"] { color: var(--info); background: var(--info-soft); border-color: var(--primary-line); }
.triage-reason[data-reason="long_blocked"] { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.config-prop-values {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md) var(--space-3xl);
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.portability-section {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
  padding: var(--space-3xl) var(--space-4xl);
  margin-bottom: var(--space-4xl);
}
.portability-section h2 { margin: 0 0 var(--space-md); font-size: var(--font-size-ui-15); color: var(--ink); }
.portability-hint { color: var(--muted); font-size: var(--font-size-ui-13); margin: 0 0 var(--space-2xl); }
.portability-actions { display: flex; gap: var(--space-lg); flex-wrap: wrap; }
.portability-btn {
  padding: var(--space-lg) var(--space-3xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--raise);
  color: var(--ink);
  font: inherit;
  font-size: var(--font-size-ui-13);
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
.portability-import { display: flex; flex-direction: column; gap: var(--space-xl); }
.portability-field { display: flex; flex-direction: column; gap: var(--space-sm); max-width: 220px; }
.portability-field span { font-size: var(--font-size-ui-12); color: var(--muted); }
.portability-import select,
.portability-import textarea {
  padding: var(--space-lg) var(--space-xl);
  border-radius: var(--radius);
  border: 1px solid var(--line-strong);
  background: var(--paper);
  color: var(--ink);
  font: inherit;
}
.portability-import textarea { font-family: var(--font-mono); font-size: var(--font-size-ui-12); }
.portability-summary { color: var(--muted); font-size: var(--font-size-ui-13); margin: var(--space-2xl) 0 var(--space-lg); }
.portability-summary strong { color: var(--ink); }
.portability-preview { display: flex; flex-direction: column; gap: var(--space-md); }
.portability-row {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  padding: var(--space-lg) var(--space-xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--paper);
  font-size: var(--font-size-ui-13);
}
.portability-row .portability-row-title { flex: 1; color: var(--ink); }
.portability-row .portability-row-id { color: var(--muted); font-size: var(--font-size-ui-12); }
.portability-badge {
  font-size: var(--font-size-ui-11);
  font-weight: 600;
  padding: var(--space-xs) var(--space-lg);
  border-radius: var(--radius-pill);
  border: 1px solid var(--line);
}
.portability-badge.is-new { color: var(--success); background: var(--success-soft); border-color: var(--success-line); }
.portability-badge.is-duplicate { color: var(--warning); background: var(--warning-soft); border-color: var(--warning-line); }
.portability-badge.is-invalid { color: var(--danger); background: var(--danger-soft); border-color: var(--danger-line); }
.portability-row-reason { color: var(--muted); font-size: var(--font-size-ui-12); }

@media (max-width: 760px) {
  .topbar {
    align-items: flex-start;
    flex-direction: column;
    flex-wrap: wrap;
    gap: var(--space-lg);
    padding: var(--space-xl) var(--space-2xl);
  }
  .brand { gap: var(--space-lg); }
  .brand-mark { width: 32px; height: 32px; }
  #status-line { display: none; }
  .topbar .topbar-search { flex: 0 0 auto; width: 100%; max-width: none; margin: 0; }
  .toolbar {
    justify-content: flex-start;
    width: 100%;
    gap: var(--space-md);
    flex-wrap: nowrap;
    overflow-x: auto;
    padding-bottom: var(--space-xs);
  }
  .toolbar > * { flex: 0 0 auto; }
  h1 { font-size: var(--font-size-ui-19); }
  .layout {
    padding: var(--space-3xl);
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
  .sidebar[data-collapsed="true"] .sidebar-more-content {
    display: flex;
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
  .growth-hero,
  .growth-stat-grid,
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
  .dashboard {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .metric {
    min-height: 64px;
    padding: var(--space-xl);
  }
  .metric strong {
    margin-top: var(--space-md);
    font-size: var(--font-size-ui-24);
  }
  /* TASK-AR-592: responsive pass - new visual components at mobile widths.
   * All sizing through tokens; no raw px literals outside token definitions. */
  /* Agent avatar (TASK-AR-587): constrain SVG avatar to --space-5xl on mobile. */
  .agent-avatar {
    width: var(--space-5xl);
    height: var(--space-5xl);
  }
  /* Agent stack: wrap so avatars don't overflow narrow containers. */
  .agent-stack {
    flex-wrap: wrap;
    gap: var(--space-xs);
  }
  /* Sparkline (TASK-AR-590): override sparkline width token for mobile.
   * The SVG uses var(--dv-sparkline-w) so narrowing that narrows all sparklines. */
  :root {
    --dv-sparkline-w: var(--visual-sparkline-mobile-w);
    --dv-sparkline-h: var(--space-5xl);
  }
  .workload-sparkline {
    flex-wrap: wrap;
    gap: var(--space-sm);
  }
  /* State illustrations (TASK-AR-590): shrink art and tighten padding. */
  .empty-illustration {
    padding: var(--space-4xl) var(--space-md);
    gap: var(--space-md);
  }
  .empty-illustration-art {
    width: var(--space-7xl);
    height: var(--space-7xl);
  }
  /* Graph SVGs (TASK-AR-588/590/591): allow horizontal scroll on mobile rather
   * than clipping. height constraint avoids full-page vertical scroll. */
  .dep-graph-stage,
  .kg-graph-stage,
  .live-map-stage {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .dep-graph-svg,
  .kg-graph-svg,
  .live-map-graph {
    min-width: var(--visual-graph-mobile-min-width);
    height: var(--visual-graph-mobile-height);
  }
  .state-machine-svg {
    min-width: var(--visual-graph-mobile-min-width);
    height: var(--visual-state-machine-mobile-height);
  }
  /* dep-graph legend: single column on mobile */
  .dep-graph-legend,
  .kg-graph-legend,
  .dep-graph-legend li,
  .kg-graph-legend li {
    flex-direction: column;
    gap: var(--space-sm);
  }
  /* Knowledge graph toolbar: stack filter chips vertically */
  .kg-graph-toolbar {
    flex-direction: column;
    gap: var(--space-md);
  }
  /* Icon rows: wrap on mobile */
  .workload-label {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  /* roadmap timeline: collapse wide link grid to single column */
  .roadmap-tl-link {
    grid-template-columns: 1fr;
    gap: var(--space-sm);
  }
}
/* TASK-AR-592: very narrow mobile breakpoint (<=480px).
 * Token: --space-breakpoint-xs is not yet defined; using the breakpoint
 * inline here as it's the only consumer and defining a token now would
 * add a not-yet-designed scale step. Breakpoint value 480px is a raw
 * literal in the token-definition role (this @media selector). */
@media (max-width: 480px) {
  /* Avatar: minimum readable size, aligned with --space-lg (8px cell -> 24px total). */
  .agent-avatar {
    width: var(--space-7xl);
    height: var(--space-7xl);
  }
  /* Sparkline: collapse to near-invisible at very narrow; hide non-essential. */
  :root {
    --dv-sparkline-w: var(--space-5xl);
    --dv-sparkline-h: var(--space-4xl);
  }
  /* State art: smaller still, readable on narrow screens. */
  .empty-illustration-art {
    width: var(--space-6xl);
    height: var(--space-6xl);
  }
  /* Dashboard: single column */
  .dashboard {
    grid-template-columns: 1fr;
  }
}
.roadmap-timeline-summary {
  color: var(--muted);
  font-size: var(--font-size-ui-13);
  margin: 0 0 var(--space-2xl);
}
.roadmap-timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--space-3xl);
  padding-left: var(--space-6-5xl);
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
  border-radius: var(--radius-hairline);
}
.roadmap-tl-vision .roadmap-tl-marker {
  background: var(--primary-hover);
}
.roadmap-tl-statement {
  color: var(--muted);
  font-size: var(--font-size-ui-13);
  margin: var(--space-sm) 0 var(--space-lg);
}
.roadmap-tl-links {
  list-style: none;
  margin: var(--space-lg) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.roadmap-tl-link {
  display: grid;
  grid-template-columns: 120px 70px 1fr 90px;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-2xl);
  padding: var(--space-3xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
}
.timeline-header,
.dep-graph-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2xl);
}
.timeline-header h2,
.dep-graph-header h2 { margin: 0; }
.timeline-summary,
.dep-graph-summary {
  margin: 0;
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.dep-cycle-warning {
  margin: 0;
  padding: var(--space-lg) var(--space-2xl);
  border: 1px solid var(--danger-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--danger);
  font-size: var(--font-size-ui-12);
  font-weight: 600;
}
.timeline-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
  overflow-x: auto;
}
.timeline-lane {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: var(--space-xl);
  align-items: center;
}
.timeline-lane-label {
  font-size: var(--font-size-ui-12);
  font-weight: 600;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.timeline-track {
  position: relative;
  display: flex;
  gap: var(--space-md);
  min-height: 30px;
  padding: var(--space-xs-half);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--tile);
}
.timeline-bar {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-xl);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-pill);
  background: var(--raise);
  color: var(--ink);
  font-size: var(--font-size-ui-11);
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
  font-size: var(--font-size-ui-10);
  color: var(--muted);
}
.timeline-arrows {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin-top: var(--space-md);
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.timeline-arrow {
  display: inline-flex;
  gap: var(--space-md);
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
.dep-edge.magnitude-low { stroke-width: 1.5; }
.dep-edge.magnitude-medium { stroke-width: 2.25; }
.dep-edge.magnitude-high { stroke-width: 3; }
.dep-edge.health-pass { stroke: var(--success-line); }
.dep-edge.health-watch { stroke: var(--warning-line); opacity: 0.85; }
.dep-edge.health-block { stroke: var(--danger); opacity: 1; }
.dep-edge.health-info { stroke: var(--primary-line); }
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
/* TASK-AR-591: --dv-cat-* palette drives dependency-graph node colors.
 * Categorical tokens (Radix Colors MIT / Carbon Apache 2.0) ensure WCAG-adequate
 * contrast vs --panel in both light and dark themes.                          */
.dep-node.kind-task circle { fill: var(--dv-cat-1, var(--panel-strong)); stroke: var(--dv-cat-1, var(--primary-line)); opacity: 0.82; }
.dep-node.kind-parent circle { fill: var(--dv-cat-2, var(--primary-soft-strong)); stroke: var(--dv-cat-2, var(--primary-line)); opacity: 0.75; }
.dep-node.kind-missing circle { fill: var(--dv-cat-3, var(--warning-soft)); stroke: var(--dv-cat-3, var(--warning-line)); opacity: 0.75; }
.dep-node.is-cycle circle { stroke: var(--danger); stroke-width: 2.5; }
.dep-node text {
  fill: var(--muted);
  font-size: var(--font-size-ui-10);
  text-anchor: middle;
}
/* TASK-AR-588: GitHub-Actions-style status icon badge on dependency nodes. */
.dep-node-status-icon { fill: var(--ink); font-size: var(--font-size-ui-8); text-anchor: middle; }
.dep-node-status-badge,
.state-machine-node-status-badge,
.live-map-node-status-badge {
  fill: var(--canvas);
  stroke: var(--line-strong);
  stroke-width: 1;
}
.dep-node-status-badge.signal-pass,
.state-machine-node-status-badge.signal-pass,
.live-map-node-status-badge.signal-pass { stroke: var(--success-line); }
.dep-node-status-badge.signal-watch,
.state-machine-node-status-badge.signal-watch,
.live-map-node-status-badge.signal-watch { stroke: var(--warning-line); }
.dep-node-status-badge.signal-block,
.state-machine-node-status-badge.signal-block,
.live-map-node-status-badge.signal-block { stroke: var(--danger); }
.dep-node-status-badge.signal-info,
.state-machine-node-status-badge.signal-info,
.live-map-node-status-badge.signal-info { stroke: var(--primary-line); }
.dep-graph-empty { fill: var(--subtle); font-size: var(--font-size-ui-14); }
.dep-graph-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2xl);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.dep-graph-legend .legend-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: var(--space-sm-half);
  border-radius: var(--radius-xs);
  vertical-align: middle;
}
.dep-graph-legend .legend-dependency { background: var(--blue); }
.dep-graph-legend .legend-parent { background: var(--subtle); }
.dep-graph-legend .legend-cycle { background: var(--danger); }

/* ===== Org chart view (console org-chart): director -> teams -> roles ===== */
.org-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
  padding: var(--space-3xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface-grad);
}
.org-chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-2xl);
}
.org-chart-header h2 { margin: 0; }
.org-chart-summary {
  margin: 0;
  font-size: var(--font-size-ui-12);
  color: var(--muted);
}
.org-chart-stage {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--canvas-grad);
  overflow: auto;
}
.org-chart-stage { overflow: visible; }
.org-chart-svg {
  display: block;
  width: 100%;
  height: 560px;
}
/* SPEC-org-chart-cards: glanceable, spacious team-card grid (wraps to fit width). */
.org-chart-canvas { display: flex; flex-direction: column; align-items: center; gap: var(--space-sm); padding: var(--space-md) 0; }
.org-owner-card {
  display: inline-flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl); border-radius: var(--radius-pill);
  border: 1px solid var(--primary); background: var(--primary); color: var(--on-accent);
  font-size: var(--font-size-ui-15); font-weight: 700;
}
.org-owner-glyph { font-size: var(--font-size-ui-16); }
.org-owner-sub { font-weight: 600; font-size: var(--font-size-ui-12); opacity: 0.85; }
.org-hierarchy-link { width: 0; height: var(--space-lg); border-left: 2px solid var(--line-strong); }
.org-director-card {
  align-self: center; display: inline-flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-md) var(--space-xl); border-radius: var(--radius-md);
  border: 1px solid var(--violet-line, var(--line-strong)); background: var(--violet-soft, var(--panel-strong));
  color: var(--ink); font-size: var(--font-size-ui-15); font-weight: 700;
}
.org-director-glyph { color: var(--violet, var(--primary)); }
.org-director-tier { color: var(--muted); font-size: var(--font-size-ui-12); font-weight: 600; }
.org-teams-grid {
  width: 100%; margin-top: var(--space-md);
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--space-xl); align-items: start;
}
.org-team-card {
  display: flex; flex-direction: column; gap: var(--space-md);
  border: 1px solid var(--line); border-top: 3px solid var(--line-strong);
  border-radius: var(--radius-md); background: var(--surface-raised);
  padding: var(--space-lg); cursor: pointer;
}
.org-team-card:hover { border-color: var(--primary-line); }
.org-team-card:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
.org-team-card.tone-primary { border-top-color: var(--primary); }
.org-team-card.tone-violet { border-top-color: var(--violet, var(--primary)); }
.org-team-card.tone-success { border-top-color: var(--success); }
.org-team-card.tone-danger { border-top-color: var(--danger); }
.org-team-card.tone-warning { border-top-color: var(--warning); }
.org-team-card.tone-teal { border-top-color: var(--teal, var(--primary)); }
.org-team-card.tone-amber { border-top-color: var(--amber, var(--warning)); }
.org-team-card.tone-muted { border-top-color: var(--muted); }
.org-team-card-head { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-sm); }
.org-team-card-name { color: var(--ink); font-size: var(--font-size-ui-14); font-weight: 700; }
.org-team-card-meta { color: var(--muted); font-size: var(--font-size-ui-11); }
.org-team-card-load { color: var(--muted); font-size: var(--font-size-ui-11); font-weight: 600; }
.org-team-card-load.load-band-busy { color: var(--warning); }
.org-team-card-load.load-band-overload { color: var(--danger); }
.org-team-card-load.has-blocked { color: var(--danger); }
.org-team-roles { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: var(--space-sm); }
.org-role-chip {
  display: flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md); border: 1px solid var(--line);
  border-radius: var(--radius-sm); background: var(--panel); cursor: pointer;
  font-size: var(--font-size-ui-12);
}
.org-role-chip:hover { border-color: var(--primary-line); background: var(--primary-soft); }
.org-role-chip:focus-visible { outline: 2px solid var(--primary); outline-offset: 1px; }
.org-role-glyph { color: var(--muted); font-weight: 700; }
.org-role-name { color: var(--ink); flex: 1 1 auto; }
.org-role-tier { color: var(--muted); font-size: var(--font-size-ui-10); }
/* SPEC-org-role-detail: click-a-role description drawer. */
.org-role-backdrop { position: fixed; inset: 0; z-index: 48; background: var(--scrim); }
.org-role-detail {
  position: fixed; top: 0; right: 0; bottom: 0; z-index: 49; width: 380px; max-width: 92vw;
  background: var(--panel); border-left: 1px solid var(--line-strong);
  box-shadow: var(--shadow-pop, var(--shadow)); padding: var(--space-2xl);
  overflow-y: auto; display: flex; flex-direction: column; gap: var(--space-md);
}
.org-role-backdrop[hidden], .org-role-detail[hidden] { display: none; }
.org-role-close {
  position: absolute; top: var(--space-md); right: var(--space-md); width: 32px; height: 32px;
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--panel-strong); color: var(--ink); cursor: pointer; font-size: var(--font-size-ui-16); line-height: 1;
}
.org-role-close:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus); }
.org-role-kicker { margin: 0; color: var(--muted); font-size: var(--font-size-ui-11); font-weight: 700; text-transform: uppercase; }
.org-role-name-h { margin: 0; color: var(--ink); font-size: var(--font-size-ui-18); }
.org-role-meta { display: flex; flex-wrap: wrap; gap: var(--space-sm); }
.org-role-tag {
  font-size: var(--font-size-ui-12); color: var(--ink);
  background: var(--surface-raised); border: 1px solid var(--line); border-radius: var(--radius-pill);
  padding: var(--space-xs) var(--space-md);
}
.org-role-tag-k { color: var(--muted); }
.org-role-sec { display: flex; flex-direction: column; gap: var(--space-xs); margin-top: var(--space-sm); }
.org-role-sec h4 { margin: 0; color: var(--muted); font-size: var(--font-size-ui-11); font-weight: 700; text-transform: uppercase; }
.org-role-sec p { margin: 0; color: var(--ink); font-size: var(--font-size-ui-13); line-height: 1.5; }
.org-role-drill {
  margin-top: var(--space-lg); align-self: flex-start;
  border: 1px solid var(--primary); border-radius: var(--radius-sm);
  background: var(--primary); color: var(--on-accent);
  padding: var(--space-sm) var(--space-lg); font: inherit; font-size: var(--font-size-ui-13); font-weight: 600; cursor: pointer;
}
.org-role-drill:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus); }
.org-chart-empty { fill: var(--subtle); font-size: var(--font-size-ui-14); }
.org-chart-edge {
  stroke: var(--line-strong);
  stroke-width: 1.5;
  fill: none;
  opacity: 0.7;
}
.org-chart-card {
  stroke-width: 1.5;
  opacity: 0.95;
}
.org-chart-node.kind-role,
.org-chart-node.kind-team { cursor: pointer; }
.org-chart-node.is-animated { transition: opacity var(--motion-fast) ease; }
.org-chart-node:focus-visible { outline: 2px solid var(--primary-hover); outline-offset: 2px; }
.org-chart-node:hover .org-chart-card { opacity: 1; stroke-width: 2; }
.org-chart-role-name {
  fill: var(--ink);
  font-size: var(--font-size-ui-12);
  font-weight: 600;
}
.org-chart-tier-badge {
  fill: var(--muted);
  font-size: var(--font-size-ui-10);
}
.org-chart-group-name {
  fill: var(--ink);
  font-size: var(--font-size-ui-13);
  font-weight: 700;
}
.org-chart-group-name.kind-director { font-size: var(--font-size-ui-14); }
.org-chart-group-sub {
  fill: var(--muted);
  font-size: var(--font-size-ui-10);
}
/* SPEC-org-chart-load-v1: per-team load line (color band + always a text label). */
.org-team-load { fill: var(--muted); font-size: var(--font-size-ui-10); font-weight: 600; }
.org-team-load.load-band-normal { fill: var(--success); }
.org-team-load.load-band-busy { fill: var(--warning); }
.org-team-load.load-band-overload { fill: var(--danger); }
.org-team-load.has-blocked { fill: var(--danger); }
.org-chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2xl);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.org-chart-legend .legend-glyph {
  display: inline-block;
  margin-right: var(--space-sm-half);
  font-weight: 700;
  color: var(--ink);
}
@media (prefers-reduced-motion: reduce) {
  .org-chart-node.is-animated { transition: none; }
}

/* ===== Knowledge graph view (#5) ===== */
.kg-graph-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-lg);
  margin: var(--space-lg) 0;
}
.kg-search {
  flex: 1 1 200px;
  min-width: 160px;
  padding: var(--space-md) var(--space-xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  color: var(--ink);
  font-size: var(--font-size-ui-12);
}
.kg-filters { display: flex; flex-wrap: wrap; gap: var(--space-md); }
.kg-filter-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--space-sm-half);
  padding: var(--space-xs-half) var(--space-lg-half);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-pill);
  background: var(--panel);
  color: var(--muted);
  font-size: var(--font-size-ui-11);
  cursor: pointer;
}
.kg-filter-chip[aria-pressed="true"] { background: var(--panel-strong); color: var(--ink); }
.kg-filter-chip[aria-pressed="false"] { opacity: 0.45; text-decoration: line-through; }
.kg-filter-chip .kg-chip-dot {
  display: inline-block; width: 9px; height: 9px; border-radius: 50%;
  border: 1px solid var(--line-strong);
}
.kg-graph-stage {
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--canvas-grad);
  overflow: hidden;
}
/* TASK-AR-591: state host for componentEmptyState/ErrorState/LoadingState overlays. */
.kg-graph-state-host:not(:empty) { padding: var(--space-4xl) var(--space-4xl); }
.kg-graph-svg { display: block; width: 100%; height: 460px; }
.kg-edge { stroke: var(--line-strong); stroke-width: 1.2; fill: none; opacity: 0.45; }
.kg-edge.type-partOf { stroke: var(--primary-line); opacity: 0.7; }
.kg-edge.type-dependsOn, .kg-edge.type-blocks { stroke: var(--danger); opacity: 0.7; }
.kg-edge.type-references { stroke: var(--blue); }
.kg-edge.type-executes { stroke: var(--subtle); stroke-dasharray: 4 3; }
/* TASK-AR-590: knowledge-graph categorical node colors consume data-viz tokens
 * (--dv-cat-N, Radix Colors MIT / Carbon Apache 2.0) for WCAG-adequate hues.
 * Node kinds: task=cat1(blue), taskset=cat2(teal), initiative=cat3(amber),
 *   review/meeting/research=cat7(violet), claim=cat4(red), commit/pr=panel. */
.kg-node circle { stroke: var(--line-strong); stroke-width: 1.4; fill: var(--panel-strong); cursor: pointer; }
.kg-node.kind-task circle { fill: var(--dv-cat-1, var(--primary-soft-strong)); stroke: var(--dv-cat-1, var(--primary-line)); opacity: 0.85; }
.kg-node.kind-taskset circle { fill: var(--dv-cat-2, var(--blue)); stroke: var(--dv-cat-2, var(--blue)); opacity: 0.85; }
.kg-node.kind-initiative circle { fill: var(--dv-cat-3, var(--warning-soft)); stroke: var(--dv-cat-3, var(--warning-line)); opacity: 0.75; }
.kg-node.kind-review circle, .kg-node.kind-meeting circle, .kg-node.kind-research circle,
.kg-node.kind-retro circle, .kg-node.kind-council circle, .kg-node.kind-seminar circle,
.kg-node.kind-compound circle, .kg-node.kind-verification circle, .kg-node.kind-call circle { fill: var(--dv-cat-7, var(--panel)); opacity: 0.6; }
.kg-node.kind-claim circle { fill: var(--dv-cat-4, var(--subtle)); opacity: 0.6; }
.kg-node.kind-commit circle, .kg-node.kind-pr circle { fill: var(--canvas); }
.kg-node.is-focus circle { stroke: var(--danger); stroke-width: 2.6; }
/* TASK-AR-592: keyboard focus ring on interactive graph nodes. SVG groups do not
 * support CSS outline so we use a box-shadow fallback; the primary focus ring is
 * shown via the outer SVG container's outline when the group has :focus-visible. */
.kg-node:focus-visible { outline: 2px solid var(--primary-hover); outline-offset: 2px; }
.kg-node text { fill: var(--muted); font-size: var(--font-size-ui-9); text-anchor: middle; pointer-events: none; }
.kg-graph-empty { fill: var(--subtle); font-size: var(--font-size-ui-14); }
.kg-graph-legend {
  display: flex; flex-wrap: wrap; gap: var(--space-2xl); margin: var(--space-lg) 0 0; padding: 0;
  list-style: none; font-size: var(--font-size-ui-11); color: var(--muted);
}
.kg-graph-legend .legend-swatch {
  display: inline-block; width: 12px; height: 12px; margin-right: var(--space-sm-half);
  border-radius: 50%; vertical-align: middle; border: 1px solid var(--line-strong);
}

/* ===== State machine interactive viewer (TASK-AR-336) ===== */
.state-machine-viewer {
  display: flex;
  flex-direction: column;
  gap: var(--space-2xl);
}
.state-machine-hint {
  font-size: var(--font-size-ui-12);
  color: var(--muted);
  margin: var(--space-sm) 0 0;
}
.state-machine-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2xl);
  align-items: flex-end;
  margin-top: var(--space-lg);
}
.state-machine-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.state-machine-field-label {
  font-size: var(--font-size-ui-10);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.state-machine-field select {
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  color: var(--ink);
  padding: var(--space-sm-half) var(--space-lg);
  font-size: var(--font-size-ui-12);
  min-width: 180px;
}
.state-machine-summary {
  font-size: var(--font-size-ui-12);
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
.state-machine-edge.magnitude-low { stroke-width: 1.5; }
.state-machine-edge.magnitude-medium { stroke-width: 2.25; }
.state-machine-edge.magnitude-high { stroke-width: 3; }
.state-machine-edge.health-pass { stroke: var(--success-line); opacity: 0.9; }
.state-machine-edge.health-watch { stroke: var(--warning-line); opacity: 0.8; }
.state-machine-edge.health-block { stroke: var(--danger); opacity: 1; }
.state-machine-edge.health-info { stroke: var(--primary-line); opacity: 0.8; }
.state-machine-edge.is-wildcard { stroke-dasharray: 5 4; opacity: 0.4; }
.state-machine-edge.is-traversed {
  stroke: var(--sm-path);
  stroke-width: 3;
  opacity: 1;
}
.state-machine-edge-label {
  fill: var(--subtle);
  font-size: var(--font-size-ui-9);
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
  font-size: var(--font-size-ui-10);
  text-anchor: middle;
}
.state-machine-node-score { fill: var(--muted); font-size: var(--font-size-ui-8); text-anchor: middle; }
/* TASK-AR-588: GitHub-Actions-style status icon badge on state-machine nodes. */
.state-machine-status-icon { fill: var(--ink); font-size: var(--font-size-ui-8); text-anchor: middle; }
.state-machine-node-status-icon { fill: var(--ink); font-size: var(--font-size-ui-8); text-anchor: middle; }
.live-map-node-status-icon { fill: var(--ink); font-size: var(--font-size-ui-8); text-anchor: middle; }
.state-machine-empty { fill: var(--subtle); font-size: var(--font-size-ui-14); }
.state-machine-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2xl);
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
.state-machine-legend .legend-swatch {
  display: inline-block;
  width: 12px;
  height: 12px;
  margin-right: var(--space-sm-half);
  border-radius: var(--radius-xs);
  vertical-align: middle;
}
.state-machine-legend .legend-pass { background: var(--success); }
.state-machine-legend .legend-watch { background: var(--warning); }
.state-machine-legend .legend-block { background: var(--danger); }
.state-machine-legend .legend-current { background: var(--sm-current); }
.state-machine-legend .legend-path { background: var(--sm-path); }

/* ===== Common list pattern toolbar / density / groups (TASK-AR-322) ===== */
.list-toolbar-mount {
  margin-bottom: var(--space-xl);
}
.list-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-lg);
  padding: var(--space-xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
}
.list-toolbar-field {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}
.list-toolbar-label {
  font-size: var(--font-size-ui-10);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
}
.list-toolbar input,
.list-toolbar select {
  background: var(--panel-strong);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-sm);
  color: var(--ink);
  padding: var(--space-sm-half) var(--space-lg);
  font-size: var(--font-size-ui-12);
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
  gap: var(--space-xs);
}
.list-density-btn {
  border: 1px solid var(--line-strong);
  background: var(--panel-strong);
  color: var(--muted);
  border-radius: var(--radius-sm);
  padding: var(--space-sm) var(--space-lg);
  font-size: var(--font-size-ui-11);
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
  border-radius: var(--radius-sm);
  padding: var(--space-md) var(--space-xl);
  font-size: var(--font-size-ui-12);
  cursor: pointer;
}
.list-group-block {
  margin-bottom: var(--space-2xl);
}
.list-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--font-size-ui-11);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  padding: var(--space-sm) var(--space-xs);
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--space-md);
}
.list-group-count {
  background: var(--primary-soft);
  border: 1px solid var(--line-strong);
  border-radius: var(--radius-pill);
  padding: var(--space-hairline) var(--space-lg);
  color: var(--ink);
}
.list-panel.density-compact .agent-card,
.list-panel.density-compact .list-row,
.list-panel.density-compact .audit-card {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--font-size-ui-11);
  line-height: 1.25;
}
.list-panel.density-compact .agent-card-meta span,
.list-panel.density-compact .audit-card-meta span {
  font-size: var(--font-size-ui-10);
}
.list-panel.density-cozy .agent-card,
.list-panel.density-cozy .list-row,
.list-panel.density-cozy .audit-card {
  padding: var(--space-xl) var(--space-2xl);
}
.list-panel.density-detail .agent-card,
.list-panel.density-detail .list-row,
.list-panel.density-detail .audit-card {
  padding: var(--space-4xl) var(--space-5xl);
  font-size: var(--font-size-ui-13);
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
  padding: var(--space-3xl) var(--space-4xl);
  font-size: var(--font-size-ui-15);
}
.command-palette-input:focus {
  outline: none;
}
.command-palette-results {
  max-height: 50vh;
  overflow-y: auto;
}
.command-palette-item {
  padding: var(--space-xl) var(--space-4xl);
  font-size: var(--font-size-ui-13);
  cursor: pointer;
  color: var(--ink);
}
.command-palette-item.is-active,
.command-palette-item:hover {
  background: var(--primary-soft-strong);
}
.command-palette-empty {
  padding: var(--space-3xl) var(--space-4xl);
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
/* Global search box in the topbar + results dropdown (TASK-AR-334). */
.topbar-search {
  position: relative;
  flex: 1 1 320px;
  max-width: 480px;
  margin: 0 var(--space-4xl);
}
.global-search-input {
  width: 100%;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  color: var(--ink);
  border-radius: var(--radius);
  padding: var(--space-lg) var(--space-2xl);
  font-size: var(--font-size-ui-13);
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
  padding: var(--space-xl) var(--space-3xl);
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
  gap: var(--space-lg);
}
.search-result-type {
  flex: none;
  font-size: var(--font-size-ui-11);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: var(--space-hairline) var(--space-md);
}
.search-result-title {
  font-size: var(--font-size-ui-13);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.search-result-meta {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
  margin-top: var(--space-xs);
}
.search-result-links {
  font-size: var(--font-size-ui-11);
  color: var(--primary);
  margin-top: var(--space-xs);
}
.search-result-group {
  padding: var(--space-md) var(--space-3xl);
  font-size: var(--font-size-ui-11);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  background: var(--panel);
  border-bottom: 1px solid var(--line);
}
.search-empty {
  padding: var(--space-3xl);
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
.search-view {
  max-width: 760px;
}
.search-view-head {
  margin-bottom: var(--space-2xl);
}
.search-view-input {
  width: 100%;
  border: 1px solid var(--line-strong);
  background: var(--panel);
  color: var(--ink);
  border-radius: var(--radius);
  padding: var(--space-xl) var(--space-2xl);
  font-size: var(--font-size-ui-14);
}
.search-view-input:focus {
  outline: 2px solid var(--primary);
  outline-offset: 1px;
}
.search-view-results {
  margin-top: var(--space-xl);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--panel);
  overflow: hidden;
}
.search-view-results:empty {
  display: none;
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
  padding: var(--space-3xl) var(--space-4xl);
  font-size: var(--font-size-ui-15);
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
  padding: var(--space-sm) var(--space-xs) var(--space-4xl);
}
.opsdash-header {
  display: flex;
  align-items: baseline;
  gap: var(--space-2xl);
  flex-wrap: wrap;
  margin-bottom: var(--space-2xl);
}
.opsdash-summary {
  color: var(--muted);
  font-size: var(--font-size-ui-13);
}
/* SPEC-health-snapshot-v1: insight-first health strip (tokens only). */
.health-snapshot {
  margin: 0 0 var(--space-2xl);
  display: flex; flex-direction: column; gap: var(--space-lg);
}
.health-verdict {
  display: inline-flex; align-items: center; gap: var(--space-sm);
  font-size: var(--font-size-ui-15); color: var(--ink);
}
.health-verdict-dot {
  width: var(--space-md); height: var(--space-md);
  border-radius: var(--radius-pill); background: var(--muted);
}
.health-verdict.tone-success .health-verdict-dot { background: var(--success); }
.health-verdict.tone-warning .health-verdict-dot { background: var(--warning); }
.health-verdict.tone-danger .health-verdict-dot { background: var(--danger); }
.health-tiles {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-md);
}
.health-tile {
  display: flex; align-items: center; justify-content: space-between; gap: var(--space-md);
  border: 1px solid var(--line); border-radius: var(--radius-sm);
  background: var(--surface-raised); padding: var(--space-md) var(--space-lg);
}
.health-tile.tone-success { background: var(--success-soft); border-color: var(--success-line); }
.health-tile.tone-warning { background: var(--warning-soft); border-color: var(--warning-line); }
.health-tile.tone-danger { background: var(--danger-soft); border-color: var(--danger-line); }
.health-tile-text { font-size: var(--font-size-ui-13); color: var(--ink); }
.health-tile-spark { flex: 0 0 auto; }
.opsdash-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--space-3xl);
}
.opsdash-card {
  background: var(--tile);
  border: 1px solid var(--tile-line);
  border-radius: var(--radius);
  padding: var(--space-3xl);
  box-shadow: var(--shadow);
}
.opsdash-card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
}
.opsdash-card-head h3 {
  margin: 0;
  font-size: var(--font-size-ui-14);
  color: var(--ink);
}
.opsdash-card-meta {
  color: var(--muted);
  font-size: var(--font-size-ui-12);
}
.opsdash-src {
  display: inline-block;
  margin-top: var(--space-lg);
  color: var(--primary);
  font-size: var(--font-size-ui-12);
  text-decoration: none;
}
.opsdash-empty {
  color: var(--muted);
  font-size: var(--font-size-ui-13);
  padding: var(--space-xl) 0;
}
/* Token/cost bars: estimate track + actual fill over token colors. */
.opsdash-bar-row {
  margin-bottom: var(--space-xl);
}
.opsdash-bar-label {
  display: flex;
  justify-content: space-between;
  gap: var(--space-lg);
  font-size: var(--font-size-ui-12);
  color: var(--ink);
  margin-bottom: var(--space-sm);
}
.opsdash-bar-label small {
  color: var(--muted);
}
.opsdash-bar-track {
  position: relative;
  height: 12px;
  border-radius: var(--radius-sm);
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
  gap: var(--space-4xl);
  flex-wrap: wrap;
  margin-bottom: var(--space-2xl);
  padding-bottom: var(--space-xl);
  border-bottom: 1px solid var(--line);
}
.opsdash-stat {
  display: flex;
  flex-direction: column;
}
.opsdash-stat b {
  font-size: var(--font-size-ui-18);
  color: var(--ink);
}
.opsdash-stat span {
  font-size: var(--font-size-ui-11);
  color: var(--muted);
}
/* Eval trend: inline SVG line + axis labels, stroke via token. */
.opsdash-sparkline-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
  color: var(--muted);
  font-size: var(--font-size-ui-12);
}
.opsdash-sparkline-strip .sparkline {
  flex-shrink: 0;
}
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
  font-size: var(--font-size-ui-9);
}
.opsdash-grid-line {
  stroke: var(--line);
  stroke-width: 1;
}
/* Gate board: pass/watch/block pills mapped to semantic tokens. */
.opsdash-gate-counts {
  display: flex;
  gap: var(--space-lg);
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
}
.opsdash-gate-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 56px;
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius);
  border: 1px solid var(--line);
}
.opsdash-gate-count b {
  font-size: var(--font-size-ui-18);
}
.opsdash-gate-count span {
  font-size: var(--font-size-ui-10);
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
  gap: var(--space-lg);
  padding: var(--space-md) 0;
  border-bottom: 1px solid var(--line);
  font-size: var(--font-size-ui-12);
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
  font-size: var(--font-size-ui-11);
}
/* Burndown + velocity: token-styled progress + SVG bar chart. */
.opsdash-burndown-bars {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
  margin-bottom: var(--space-3xl);
}
.opsdash-velocity-head {
  font-size: var(--font-size-ui-12);
  color: var(--muted);
  margin-bottom: var(--space-md);
}
.opsdash-velocity-bars {
  display: flex;
  align-items: flex-end;
  gap: var(--space-md);
  height: 80px;
}
.opsdash-vbar {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: var(--space-xs);
}
.opsdash-vbar-fill {
  width: 100%;
  background: var(--success);
  border-radius: var(--radius-xs) var(--radius-xs) 0 0;
  min-height: 2px;
}
.opsdash-vbar-label {
  font-size: var(--font-size-ui-9);
  color: var(--muted);
}
.opsdash-vbar-count {
  font-size: var(--font-size-ui-10);
  color: var(--ink);
}

/* =====================================================================
 * TASK-AR-340: Microinteractions + gamification policy layer.
 * Calm serious mode is the DEFAULT. All animation classes are gated by
 * the root data-motion attribute AND prefers-reduced-motion; all
 * gamification visuals are gated by data-gamify. Confetti / celebration
 * colors come from existing semantic tokens (no raw hex).
 * ===================================================================== */
:root {
  /* Confetti / celebration palette is derived purely from semantic tokens
     so it tracks the theme and passes the no-raw-hex gate. */
  --confetti-1: var(--primary);
  --confetti-2: var(--success);
  --confetti-3: var(--warning);
  --confetti-4: var(--violet);
  --confetti-5: var(--blue);
  --skeleton-base: var(--panel-strong);
  --skeleton-sheen: var(--raise-strong);
  --motion-fast: 140ms;
  --motion-base: 240ms;
  --motion-slow: 420ms;
}

@keyframes ar-fade-in-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes ar-pop-in {
  0% { opacity: 0; transform: scale(0.94); }
  60% { opacity: 1; transform: scale(1.02); }
  100% { opacity: 1; transform: scale(1); }
}
@keyframes ar-skeleton-shimmer {
  0% { background-position: -160px 0; }
  100% { background-position: 160px 0; }
}
@keyframes ar-confetti-fall {
  0% { opacity: 1; transform: translate3d(0, -12px, 0) rotate(0deg); }
  100% { opacity: 0; transform: translate3d(var(--confetti-dx, 0), 78vh, 0) rotate(540deg); }
}
@keyframes ar-xp-bump {
  0% { transform: scale(1); }
  40% { transform: scale(1.12); }
  100% { transform: scale(1); }
}

/* --- Microinteractions: state transitions + optimistic updates --- */
.ar-anim-enter {
  animation: ar-fade-in-up var(--motion-base) ease both;
}
.ar-anim-pop {
  animation: ar-pop-in var(--motion-base) cubic-bezier(0.2, 0.8, 0.3, 1.1) both;
}
.is-optimistic {
  opacity: 0.62;
  transition: opacity var(--motion-fast) ease;
}
.is-state-changed {
  animation: ar-pop-in var(--motion-base) ease both;
}

/* --- Drag physics (lift + tilt while dragging board cards) --- */
.ar-dragging {
  transition: transform var(--motion-fast) ease, box-shadow var(--motion-fast) ease;
  transform: scale(1.03) rotate(-1deg);
  box-shadow: var(--shadow-pop);
  cursor: grabbing;
}

/* --- Skeleton loading placeholders --- */
.ar-skeleton {
  position: relative;
  overflow: hidden;
  border-radius: var(--radius);
  background: var(--skeleton-base);
  min-height: 14px;
}
.ar-skeleton::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, var(--skeleton-sheen), transparent);
  background-size: 160px 100%;
  background-repeat: no-repeat;
  animation: ar-skeleton-shimmer 1.1s ease-in-out infinite;
}

/* View heading (carries quest-mode label swap). */
.view-heading {
  font-size: var(--font-size-ui-16);
  margin-bottom: var(--space-2xl);
  color: var(--ink);
}

/* --- Illustrated empty state (token-driven SVG) --- */
.empty-illustration {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-lg);
  text-align: center;
  font-style: normal;
  padding: var(--space-7xl) var(--space-2xl);
  color: var(--muted);
}
.empty-illustration-art {
  width: 56px;
  height: 56px;
  fill: var(--raise-strong);
  stroke: var(--line-strong);
  stroke-width: 2;
  opacity: 0.9;
}
.empty-illustration-art path { stroke: var(--line-strong); fill: none; }
.empty-illustration-title { color: var(--ink); font-weight: 600; }
.empty-illustration-hint { color: var(--muted); font-size: var(--font-size-ui-12); }
/* TASK-AR-590: state illustration variants (error=danger token, loading=accent) */
.empty-illustration--loading .empty-illustration-art { stroke: none; fill: none; }
@keyframes ar-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.empty-illustration-art--spin {
  animation: ar-spin 1s linear infinite;
  transform-origin: 50% 50%;
}
@media (prefers-reduced-motion: reduce) {
  .empty-illustration-art--spin { animation: none; }
}
/* TASK-AR-590: sparkline component (inspired by fnando/sparkline MIT).        */
/* Stroke/fill consume --dv-sparkline / --dv-sparkline-area token pairs.       */
.sparkline {
  display: inline-block;
  vertical-align: middle;
  overflow: visible;
}
.sparkline--empty { display: inline-block; width: var(--dv-sparkline-w, 64px); height: var(--dv-sparkline-h, 24px); }
/* Workload agent-row sparkline slot */
.workload-sparkline { display: flex; align-items: center; gap: var(--space-md); }
.workload-sparkline .sparkline { flex-shrink: 0; }

/* TASK-AR-592 final responsive override for visual-system components.
 * This appears after graph/sparkline base rules so mobile values are not
 * overwritten by later component CSS. */
@media (max-width: 720px) {
  :root {
    --dv-sparkline-w: var(--visual-sparkline-mobile-w);
    --dv-sparkline-h: var(--space-5xl);
  }
  .dep-graph-stage,
  .kg-graph-stage,
  .live-map-stage {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .dep-graph-svg,
  .kg-graph-svg,
  .live-map-graph {
    min-width: var(--visual-graph-mobile-min-width);
    height: var(--visual-graph-mobile-height);
  }
  .state-machine-svg {
    min-width: var(--visual-graph-mobile-min-width);
    height: var(--visual-state-machine-mobile-height);
  }
  .dep-graph-svg {
    min-width: 100%;
  }
}
@media (max-width: 480px) {
  :root {
    --dv-sparkline-w: var(--space-5xl);
    --dv-sparkline-h: var(--space-4xl);
  }
}

/* --- Experience settings control + dialog --- */
.experience-settings-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-md);
}
.experience-settings-icon { font-size: var(--font-size-ui-14); line-height: 1; }
.experience-settings {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
}
.experience-settings[hidden] { display: none; }
.experience-settings-backdrop {
  position: absolute;
  inset: 0;
  background: var(--scrim);
}
.experience-settings-panel {
  position: relative;
  width: min(380px, 92vw);
  margin: var(--space-floating-offset) var(--space-4xl) var(--space-4xl);
  max-height: calc(100vh - 96px);
  overflow-y: auto;
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  padding: var(--space-4xl);
  animation: ar-fade-in-up var(--motion-base) ease both;
}
.experience-settings-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.experience-settings-head h2 { font-size: var(--font-size-ui-16); }
.experience-settings-close {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: var(--font-size-ui-22);
  line-height: 1;
  cursor: pointer;
}
.experience-settings-hint { color: var(--muted); font-size: var(--font-size-ui-12); margin: var(--space-lg) 0 var(--space-3xl); }
.experience-settings-group { margin-bottom: var(--space-4xl); }
.experience-settings-group h3 {
  font-size: var(--font-size-ui-11);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--subtle);
  margin-bottom: var(--space-lg);
}
.experience-toggle {
  display: flex;
  gap: var(--space-xl);
  align-items: flex-start;
  padding: var(--space-lg);
  border-radius: var(--radius);
  cursor: pointer;
}
.experience-toggle:hover { background: var(--raise); }
.experience-toggle input { margin-top: var(--space-xs-half); }
.experience-toggle-text { display: flex; flex-direction: column; gap: var(--space-xs); }
.experience-toggle-text strong { font-size: var(--font-size-ui-13); color: var(--ink); }
.experience-toggle-text small { font-size: var(--font-size-ui-11); color: var(--muted); }
.experience-settings-foot { border-top: 1px solid var(--line); padding-top: var(--space-2xl); }
.experience-tour-start {
  background: var(--primary-soft);
  border: 1px solid var(--primary-line);
  color: var(--primary-hover);
  border-radius: var(--radius);
  padding: var(--space-md) var(--space-2xl);
  cursor: pointer;
}

/* --- Onboarding tour overlay --- */
.onboarding-tour {
  position: fixed;
  inset: 0;
  z-index: 45;
  display: flex;
  align-items: center;
  justify-content: center;
}
.onboarding-tour[hidden] { display: none; }
.onboarding-tour-backdrop { position: absolute; inset: 0; background: var(--scrim); }
.onboarding-tour-card {
  position: relative;
  width: min(420px, 92vw);
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-pop);
  padding: var(--space-6xl);
  animation: ar-pop-in var(--motion-base) ease both;
}
.onboarding-tour-step { font-size: var(--font-size-ui-11); color: var(--subtle); letter-spacing: 0.06em; }
.onboarding-tour-card h2 { font-size: var(--font-size-ui-18); margin: var(--space-md) 0 var(--space-lg); }
.onboarding-tour-card p { color: var(--muted); font-size: var(--font-size-ui-13); }
.onboarding-tour-actions { display: flex; justify-content: space-between; margin-top: var(--space-4xl); }
.onboarding-tour-skip {
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
}
.onboarding-tour-next {
  background: var(--primary);
  color: var(--on-accent);
  border: none;
  border-radius: var(--radius);
  padding: var(--space-lg) var(--space-4xl);
  cursor: pointer;
}

/* --- Contextual help bubble --- */
.contextual-help {
  position: fixed;
  right: 16px;
  bottom: 16px;
  z-index: 38;
  max-width: 300px;
  display: flex;
  gap: var(--space-lg);
  align-items: flex-start;
  background: var(--surface-raised);
  border: 1px solid var(--primary-line);
  border-left: 3px solid var(--primary);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: var(--space-xl) var(--space-2xl);
  animation: ar-fade-in-up var(--motion-base) ease both;
}
.contextual-help[hidden] { display: none; }
.contextual-help-text { font-size: var(--font-size-ui-12); color: var(--ink); }
.contextual-help-dismiss {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: var(--font-size-ui-16);
  line-height: 1;
  cursor: pointer;
}

/* --- Gamification: celebration / confetti (opt-in via data-gamify) --- */
.celebration-layer {
  position: fixed;
  inset: 0;
  z-index: 60;
  pointer-events: none;
  overflow: hidden;
}
.celebration-layer:empty { display: none; }
.confetti-piece {
  position: absolute;
  top: 0;
  width: 9px;
  height: 14px;
  border-radius: var(--radius-hairline);
  opacity: 0;
  will-change: transform, opacity;
}
.confetti-piece.tone-1 { background: var(--confetti-1); }
.confetti-piece.tone-2 { background: var(--confetti-2); }
.confetti-piece.tone-3 { background: var(--confetti-3); }
.confetti-piece.tone-4 { background: var(--confetti-4); }
.confetti-piece.tone-5 { background: var(--confetti-5); }

/* Confetti only animates when gamification + motion are BOTH on. */
:root[data-gamify="on"][data-motion="on"] .confetti-piece {
  animation: ar-confetti-fall var(--motion-slow) ease-in forwards;
}

/* Gamification emphasis on the agent XP bar (opt-in). */
:root[data-gamify="on"] .agent-character-level { font-weight: 600; }
:root[data-gamify="on"][data-motion="on"] .agent-character-level.is-leveled {
  animation: ar-xp-bump var(--motion-base) ease both;
}
.agent-character-streak {
  display: none;
  font-size: var(--font-size-ui-11);
  color: var(--warning);
}
:root[data-gamify="on"] .agent-character-streak { display: inline; }

/* Quest-board terminology mode swaps a few labels via [data-quest-*]. */
:root:not([data-quest-mode="on"]) [data-quest-label] { display: none; }
:root[data-quest-mode="on"] [data-default-label] { display: none; }

/* =====================================================================
 * ACCESSIBILITY (acceptance-critical): every animation is disabled when
 * the global motion toggle is OFF, OR when the OS requests reduced motion.
 * These rules MUST sit AFTER the animation definitions to win the cascade.
 * ===================================================================== */
:root[data-motion="off"] .ar-anim-enter,
:root[data-motion="off"] .ar-anim-pop,
:root[data-motion="off"] .is-state-changed,
:root[data-motion="off"] .ar-dragging,
:root[data-motion="off"] .ar-skeleton::after,
:root[data-motion="off"] .confetti-piece,
:root[data-motion="off"] .agent-character-level.is-leveled,
:root[data-motion="off"] .experience-settings-panel,
:root[data-motion="off"] .onboarding-tour-card,
:root[data-motion="off"] .contextual-help {
  animation: none !important;
  transition: none !important;
}
:root[data-motion="off"] .ar-dragging { transform: none; }

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
    scroll-behavior: auto !important;
  }
  .confetti-piece,
  .ar-skeleton::after {
    animation: none !important;
  }
}

/* --- Decision-first cockpit: attention inbox (TASK-AR-564) ----------------- */
/* The home hero -- "what needs you now". Six derived groups (scripts/
   attention_inbox.py via /api/inbox): counts + compact summaries stay on the
   home; full item detail opens in the focus-managed drawer (TASK-AR-566).
   Colors are tokens only (no raw literals -- see theme token tests). */
.cockpit { margin: 0 0 1.25rem; }
.cockpit-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 0.5rem; margin-bottom: 0.75rem;
}
.cockpit-title { margin: 0; font-size: 1.2rem; font-weight: 700; color: var(--ink); }
.cockpit-total { font-size: 0.85rem; color: var(--muted); }
.cockpit-grid {
  display: grid; gap: 0.85rem;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  max-height: 320px;
  overflow-y: auto;
  padding-right: var(--space-xs);
}
.cockpit-empty {
  margin: 0; padding: 1.5rem; text-align: center; color: var(--muted);
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
}
.inbox-card {
  display: flex; flex-direction: column; gap: 0.5rem; padding: 0.85rem 1rem;
  background: var(--panel); border: 1px solid var(--line);
  border-left: 4px solid var(--line-strong); border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.inbox-card.tone-high { border-left-color: var(--danger); }
.inbox-card.tone-mid { border-left-color: var(--warning); }
.inbox-card.tone-low { border-left-color: var(--muted); }
.inbox-card-head { display: flex; align-items: center; gap: 0.45rem; }
.inbox-ico { font-size: 1.05em; line-height: 1; }
.inbox-label { font-weight: 600; color: var(--ink); }
.inbox-count {
  margin-left: auto; min-width: 1.7em; padding: 0.05rem 0.45rem; text-align: center;
  font-size: 0.8rem; font-weight: 700; color: var(--ink);
  background: var(--panel-strong); border-radius: var(--radius-pill);
}
.inbox-summary-line {
  margin: 0; color: var(--muted); font-size: 0.86rem;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.inbox-summary-action { color: var(--primary); font-weight: 700; }
.inbox-card-action {
  align-self: flex-start; min-height: 34px; border: 1px solid var(--line-strong);
  border-radius: var(--radius); background: var(--panel-strong); color: var(--ink);
  cursor: pointer; font-size: 0.82rem; font-weight: 700; padding: 0.35rem 0.65rem;
}
.inbox-card-action:hover { border-color: var(--primary-line); background: var(--primary-soft); }
.inbox-card-action:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus);
}
.inbox-detail-backdrop {
  position: fixed; inset: 0; z-index: 48; background: var(--scrim);
}
.inbox-detail-drawer {
  position: fixed; top: 0; right: 0; bottom: 0; z-index: 49;
  width: min(460px, 100vw); padding: 1rem;
  background: var(--panel); border-left: 1px solid var(--line);
  box-shadow: var(--shadow); overflow-y: auto;
}
.inbox-detail-backdrop[hidden],
.inbox-detail-drawer[hidden] { display: none; }
.inbox-detail-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 1rem; margin-bottom: 0.75rem;
}
.inbox-detail-kicker {
  margin: 0 0 0.2rem; color: var(--muted); font-size: 0.75rem;
  font-weight: 700; text-transform: uppercase;
}
.inbox-detail-head h2 { margin: 0; font-size: 1.1rem; color: var(--ink); }
.inbox-detail-close {
  display: inline-flex; align-items: center; justify-content: center;
  width: 34px; height: 34px; border: 1px solid var(--line-strong);
  border-radius: var(--radius); background: var(--panel-strong); color: var(--ink);
  cursor: pointer; font-size: 1.3rem; line-height: 1;
}
.inbox-detail-close:hover { border-color: var(--primary-line); background: var(--primary-soft); }
.inbox-detail-close:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus);
}
.inbox-detail-summary { margin: 0 0 0.75rem; color: var(--muted); font-size: 0.85rem; }
.inbox-detail-list { display: flex; flex-direction: column; gap: 0.6rem; }
.inbox-detail-item {
  border: 1px solid var(--line); border-radius: var(--radius);
  background: var(--surface-raised); padding: 0.7rem;
}
.inbox-detail-item-title { margin: 0; color: var(--ink); font-size: 0.92rem; font-weight: 700; }
.inbox-detail-item-meta {
  display: flex; flex-wrap: wrap; gap: 0.35rem 0.55rem;
  margin-top: 0.45rem; color: var(--muted); font-size: 0.78rem;
}
.inbox-detail-item-action { color: var(--primary); font-weight: 700; }
/* SPEC-decision-inbox-v1: plain-language lead + proposal-only respond bar. */
.inbox-detail-item-lead { margin: 0.35rem 0 0; color: var(--ink); font-size: 0.85rem; line-height: 1.45; }
.inbox-detail-item.is-decided { border-color: var(--success-line); background: var(--success-soft); }
.inbox-decide { margin-top: 0.6rem; padding-top: 0.55rem; border-top: 1px solid var(--line); }
.inbox-decide-prompt {
  display: block; margin-bottom: 0.4rem; color: var(--muted);
  font-size: 0.75rem; font-weight: 700;
}
.inbox-decide-actions { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.inbox-decide-btn {
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--panel-strong); color: var(--ink);
  padding: 0.32rem 0.7rem; font-size: 0.8rem; font-weight: 600; cursor: pointer;
  transition: border-color 120ms ease, background 120ms ease;
}
.inbox-decide-btn:hover { border-color: var(--primary-line); background: var(--primary-soft); }
.inbox-decide-btn:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus);
}
.inbox-decide-btn.is-primary { border-color: var(--primary); background: var(--primary); color: var(--on-accent); }
.inbox-decide-btn.is-ghost { background: transparent; }
.inbox-decide-reason { margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem; }
.inbox-decide-reason-input {
  width: 100%; resize: vertical; box-sizing: border-box;
  border: 1px solid var(--line-strong); border-radius: var(--radius-sm);
  background: var(--surface-raised); color: var(--ink);
  padding: 0.45rem 0.55rem; font: inherit; font-size: 0.82rem;
}
.inbox-decide-reason-input:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 1px; box-shadow: var(--focus);
}
.inbox-decide-reason-actions { display: flex; gap: 0.4rem; }
.inbox-decide-error { margin: 0.35rem 0 0; color: var(--danger); font-size: 0.78rem; }
.inbox-decide-recorded {
  margin: 0.5rem 0 0; color: var(--success); font-size: 0.82rem; font-weight: 700;
  animation: inboxDecideIn 160ms ease-out;
}
.inbox-decide-undo {
  margin: 0.3rem 0 0; padding: 0; border: none; background: none;
  color: var(--primary); font-size: 0.78rem; font-weight: 600;
  text-decoration: underline; cursor: pointer;
}
.inbox-decide-undo:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  .inbox-decide-recorded { animation: none; }
  .inbox-decide-btn { transition: none; }
}
@keyframes inboxDecideIn { from { opacity: 0; } to { opacity: 1; } }
.work-state-hero {
  margin: 0 0 1.25rem; padding: 1rem;
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius);
  box-shadow: var(--shadow);
}
.work-state-head {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 1rem; margin-bottom: 0.8rem;
}
.work-state-kicker {
  margin: 0 0 0.2rem; color: var(--muted); font-size: 0.75rem;
  font-weight: 700; text-transform: uppercase;
}
.work-state-head h2 { margin: 0; color: var(--ink); font-size: 1.1rem; }
.work-state-total { color: var(--muted); font-size: 0.84rem; white-space: nowrap; margin-left: auto; }
/* TASK-AR-624: collapse toggle demotes the work-state hero (cockpit stays the
   top-of-screen focus). Defaults expanded, so initial geometry is unchanged. */
.work-state-collapse {
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.6rem; height: 1.6rem; padding: 0; flex: none;
  background: transparent; border: 1px solid var(--line); border-radius: var(--radius);
  color: var(--muted); cursor: pointer;
}
.work-state-collapse:hover { color: var(--ink); border-color: var(--line-strong); }
.work-state-collapse:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }
.wsh-caret {
  width: 0.5rem; height: 0.5rem; border-right: 2px solid currentColor;
  border-bottom: 2px solid currentColor; transform: rotate(45deg) translate(-1px, -1px);
  transition: transform 0.15s ease;
}
.work-state-hero.is-collapsed .wsh-caret { transform: rotate(-45deg) translate(-1px, 1px); }
.work-state-hero.is-collapsed .work-state-board,
.work-state-hero.is-collapsed .work-state-empty { display: none; }
@media (prefers-reduced-motion: reduce) { .wsh-caret { transition: none; } }
.work-state-board {
  display: grid; gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  max-height: 320px;
  overflow-y: auto;
  padding-right: var(--space-xs);
}
.work-state-empty {
  margin: 0; padding: 1rem; color: var(--muted); text-align: center;
  background: var(--surface-raised); border: 1px solid var(--line); border-radius: var(--radius);
}
.work-state-card {
  display: flex; flex-direction: column; gap: 0.65rem; min-width: 0;
  padding: 0.85rem; background: var(--surface-raised);
  border: 1px solid var(--line); border-left: 4px solid var(--primary-line);
  border-radius: var(--radius);
}
.work-state-card.is-hot { border-left-color: var(--danger); }
.work-state-card.is-waiting { border-left-color: var(--warning); }
.work-state-path {
  margin: 0; color: var(--muted); font-size: 0.72rem; font-weight: 700;
  text-transform: uppercase; overflow-wrap: anywhere;
}
.work-state-card-title {
  margin: 0; color: var(--ink); font-size: 0.95rem; line-height: 1.3;
  overflow-wrap: anywhere;
}
.work-state-counts {
  display: grid; gap: 0.4rem;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.work-state-count {
  min-width: 0; padding: 0.45rem; background: var(--panel);
  border: 1px solid var(--line); border-radius: var(--radius);
}
.work-state-count strong {
  display: block; color: var(--ink); font-size: 1rem; line-height: 1.1;
}
.work-state-count span {
  display: block; margin-top: 0.12rem; color: var(--muted); font-size: 0.7rem;
}
.work-state-drill {
  border-top: 1px solid var(--line); padding-top: 0.55rem;
}
.work-state-drill summary {
  cursor: pointer; color: var(--primary); font-size: 0.8rem; font-weight: 700;
}
.work-state-drill summary:focus-visible {
  outline: 2px solid var(--primary); outline-offset: 2px; box-shadow: var(--focus);
}
.work-state-units {
  display: flex; flex-direction: column; gap: 0.35rem; margin-top: 0.55rem;
}
.work-state-unit {
  display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
  min-width: 0; color: var(--ink); font-size: 0.78rem;
}
.work-state-unit span:first-child {
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.work-state-bucket {
  flex: 0 0 auto; padding: 0.08rem 0.4rem; color: var(--muted);
  background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius-pill);
  font-size: 0.68rem;
}
@media (max-width: 640px) {
  .cockpit { margin-bottom: 0.75rem; }
  .cockpit-grid,
  .work-state-board {
    max-height: 320px;
    overflow-y: auto;
    padding-right: var(--space-xs);
  }
  .cockpit-grid { gap: 0.5rem; }
  .cockpit-grid { grid-template-columns: 1fr; }
  .inbox-card { gap: 0.35rem; padding: 0.65rem 0.75rem; }
  .inbox-card-action { min-height: 30px; padding: 0.25rem 0.55rem; }
  .inbox-detail-drawer { width: 100vw; }
  .work-state-hero { margin-bottom: 0.75rem; padding: 0.75rem; }
  .work-state-head { gap: 0.45rem; margin-bottom: 0.55rem; }
  .work-state-head { flex-direction: column; }
  .work-state-total { white-space: normal; }
  .work-state-board { grid-template-columns: 1fr; gap: 0.5rem; }
  .work-state-card { gap: 0.45rem; padding: 0.65rem; }
  .work-state-counts { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .work-state-drill { display: none; }
}
"""

CSS = CSS + ui_design_assets.UI_TOKEN_SCALE_CSS

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

// --- Experience policy: microinteractions + gamification (TASK-AR-340) -----
// Calm serious mode is the default. Motion always honors prefers-reduced-motion.
// Gamification + completion sound are opt-in and persist via localStorage.
// All state lives on the document root as data-motion / data-gamify /
// data-quest-mode attributes; CSS keys off them so there is no residue when off.
const MOTION_KEY = "agent-runtime-motion";
const GAMIFY_KEY = "agent-runtime-gamify";
const QUEST_KEY = "agent-runtime-quest-mode";
const SOUND_KEY = "agent-runtime-completion-sound";
const TOUR_KEY = "agent-runtime-tour-seen";

function readPref(key) {
  try { return window.localStorage.getItem(key); } catch (error) { return null; }
}
function writePref(key, value) {
  try { window.localStorage.setItem(key, value); } catch (error) { /* storage blocked */ }
}
function prefersReducedMotion() {
  return Boolean(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
}
function motionEnabled() {
  return document.documentElement.getAttribute("data-motion") === "on";
}
function gamifyEnabled() {
  return document.documentElement.getAttribute("data-gamify") === "on";
}
function soundEnabled() {
  return readPref(SOUND_KEY) === "on";
}

function resolveMotion() {
  // Explicit user choice wins; otherwise default ON but yield to reduced-motion.
  const raw = readPref(MOTION_KEY);
  if (raw === "off") return false;
  if (raw === "on") return true;
  return !prefersReducedMotion();
}

function applyExperiencePolicy() {
  const root = document.documentElement;
  root.setAttribute("data-motion", resolveMotion() ? "on" : "off");
  root.setAttribute("data-gamify", readPref(GAMIFY_KEY) === "on" ? "on" : "off");
  root.setAttribute("data-quest-mode", readPref(QUEST_KEY) === "on" ? "on" : "off");
  syncExperienceControls();
}

function syncExperienceControls() {
  const motion = $("setting-motion");
  const gamify = $("setting-gamify");
  const quest = $("setting-quest-mode");
  const sound = $("setting-sound");
  if (motion) motion.checked = motionEnabled();
  if (gamify) gamify.checked = gamifyEnabled();
  if (quest) quest.checked = document.documentElement.getAttribute("data-quest-mode") === "on";
  if (sound) sound.checked = soundEnabled();
}

function openExperienceSettings() {
  const dialog = $("experience-settings");
  const toggle = $("experience-settings-toggle");
  if (!dialog) return;
  syncExperienceControls();
  dialog.hidden = false;
  if (toggle) toggle.setAttribute("aria-expanded", "true");
}
function closeExperienceSettings() {
  const dialog = $("experience-settings");
  const toggle = $("experience-settings-toggle");
  if (!dialog) return;
  dialog.hidden = true;
  if (toggle) toggle.setAttribute("aria-expanded", "false");
}

function initExperienceSettings() {
  applyExperiencePolicy();
  $("experience-settings-toggle")?.addEventListener("click", () => {
    const dialog = $("experience-settings");
    if (dialog && dialog.hidden) openExperienceSettings();
    else closeExperienceSettings();
  });
  $("experience-settings-close")?.addEventListener("click", closeExperienceSettings);
  document.querySelectorAll("[data-experience-dismiss]").forEach((node) =>
    node.addEventListener("click", closeExperienceSettings));
  $("setting-motion")?.addEventListener("change", (event) => {
    writePref(MOTION_KEY, event.target.checked ? "on" : "off");
    applyExperiencePolicy();
  });
  $("setting-gamify")?.addEventListener("change", (event) => {
    writePref(GAMIFY_KEY, event.target.checked ? "on" : "off");
    applyExperiencePolicy();
    // Re-render so JS-driven labels/streaks reflect the new policy. Guard on
    // runtimeState: a toggle can fire before the first state load resolves.
    if (runtimeState) renderAll();
  });
  $("setting-quest-mode")?.addEventListener("change", (event) => {
    writePref(QUEST_KEY, event.target.checked ? "on" : "off");
    applyExperiencePolicy();
    if (runtimeState) renderAll();
  });
  $("setting-sound")?.addEventListener("change", (event) => {
    writePref(SOUND_KEY, event.target.checked ? "on" : "off");
  });
  $("experience-tour-start")?.addEventListener("click", () => {
    closeExperienceSettings();
    startOnboardingTour(true);
  });
  // React live to OS reduced-motion changes (only when no explicit choice).
  if (window.matchMedia) {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => { if (!readPref(MOTION_KEY)) applyExperiencePolicy(); };
    if (media.addEventListener) media.addEventListener("change", onChange);
    else if (media.addListener) media.addListener(onChange);
  }
}

// Quest-board terminology helper: returns the quest term only when the mode is
// on, else the plain default. Used for dynamic JS-rendered labels.
function questTerm(plain, quest) {
  return document.documentElement.getAttribute("data-quest-mode") === "on" ? quest : plain;
}

// Confetti celebration. Pieces are colored ONLY via token-driven CSS classes
// (tone-1..5); JS never injects raw colors. Runs only when gamification AND
// motion are both on. Pieces self-remove so nothing lingers when off.
function celebrate(intensity) {
  if (!gamifyEnabled() || !motionEnabled()) return;
  const layer = $("celebration-layer");
  if (!layer) return;
  const count = Math.max(12, Math.min(80, Number(intensity) || 36));
  for (let i = 0; i < count; i += 1) {
    const piece = document.createElement("span");
    piece.className = `confetti-piece tone-${(i % 5) + 1}`;
    piece.style.left = `${Math.round(Math.random() * 100)}%`;
    piece.style.setProperty("--confetti-dx", `${Math.round((Math.random() - 0.5) * 240)}px`);
    piece.style.animationDelay = `${Math.round(Math.random() * 180)}ms`;
    layer.appendChild(piece);
    setTimeout(() => { if (piece.parentNode) piece.parentNode.removeChild(piece); }, 1400);
  }
}

// Completion chime (WebAudio). Default OFF; only plays when explicitly enabled.
function playCompletionSound() {
  if (!soundEnabled()) return;
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return;
    const ctx = new Ctx();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(660, ctx.currentTime);
    osc.frequency.setValueAtTime(880, ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.0001, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.18, ctx.currentTime + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.3);
    osc.connect(gain).connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.32);
  } catch (error) { /* audio unavailable */ }
}

// Onboarding tour. Shown once on first run (unless reduced visuals); replayable
// from the settings panel. Pure DOM, ASCII-only copy.
const ONBOARDING_STEPS = [
  { title: "Welcome to Agent Runtime", body: "This console is read-first: it shows live runtime state and proposes changes. Let us take a quick tour." },
  { title: "Navigate with the sidebar", body: "Use the left sidebar to switch between work, agents, comms, records, and ops views. Press Ctrl+P to quick-open." },
  { title: "Tune your experience", body: "Open Experience in the top bar to toggle animations, opt into gamification, or replay this tour. Calm serious mode is the default." },
];
let onboardingIndex = 0;

function renderOnboardingStep() {
  const step = ONBOARDING_STEPS[onboardingIndex];
  if (!step) return;
  setText("onboarding-tour-step", `${onboardingIndex + 1} / ${ONBOARDING_STEPS.length}`);
  setText("onboarding-tour-title", step.title);
  setText("onboarding-tour-body", step.body);
  const next = $("onboarding-tour-next");
  if (next) next.textContent = onboardingIndex === ONBOARDING_STEPS.length - 1 ? "Done" : "Next";
}
function startOnboardingTour(force) {
  const dialog = $("onboarding-tour");
  if (!dialog) return;
  if (!force && readPref(TOUR_KEY) === "1") return;
  onboardingIndex = 0;
  renderOnboardingStep();
  dialog.hidden = false;
}
function endOnboardingTour() {
  const dialog = $("onboarding-tour");
  if (dialog) dialog.hidden = true;
  writePref(TOUR_KEY, "1");
}
function initOnboardingTour() {
  $("onboarding-tour-next")?.addEventListener("click", () => {
    if (onboardingIndex >= ONBOARDING_STEPS.length - 1) { endOnboardingTour(); return; }
    onboardingIndex += 1;
    renderOnboardingStep();
  });
  $("onboarding-tour-skip")?.addEventListener("click", endOnboardingTour);
  document.querySelectorAll("[data-tour-dismiss]").forEach((node) =>
    node.addEventListener("click", endOnboardingTour));
  startOnboardingTour(false);
}

// Contextual help bubble: a small dismissible hint anchored bottom-right.
function showContextualHelp(text) {
  const host = $("contextual-help");
  if (!host) return;
  setText("contextual-help-text", text);
  host.hidden = false;
}
function initContextualHelp() {
  $("contextual-help-dismiss")?.addEventListener("click", () => {
    const host = $("contextual-help");
    if (host) host.hidden = true;
  });
}

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
// B-03: dedupe successive SSE snapshots. The /api/stream endpoint is single-shot,
// so EventSource reconnects and may re-deliver the SAME state; if it is identical
// we skip the (heavy) re-render + downstream reconciliation so a reconnect can't
// pile redundant work on top of the interval poll.
let lastStreamPayload = null;
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

function setHtml(id, value) {
  const node = $(id);
  if (node) node.innerHTML = value;
}

// ----- TASK-AR-341: i18n (KR/EN) string lookup + language toggle -----
// String VALUES are served from Python (runtimeState.i18n / /api/i18n) so this
// app.js stays ASCII-only; t() looks them up with KR/EN fallback. Default KR.
const LANGUAGE_STORAGE_KEY = "agent-runtime-language";
const DEFAULT_LANGUAGE = "ko";
const SUPPORTED_LANGUAGES = ["ko", "en"];
let currentLanguage = DEFAULT_LANGUAGE;
let i18nStrings = {};
let cockpitData = null;
let workStateData = null;

function storedLanguage() {
  try {
    const value = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return SUPPORTED_LANGUAGES.indexOf(value) >= 0 ? value : null;
  } catch (error) {
    return null;
  }
}

// t(key): resolve a string for the active language; falls back to KR, then EN,
// then the raw key. The return value is plain text (callers escape when they
// inject it into innerHTML).
function t(key) {
  const entry = i18nStrings[key];
  if (!entry) return key;
  return entry[currentLanguage] || entry[DEFAULT_LANGUAGE] || entry.en || key;
}

// Apply translations to every [data-i18n] node via textContent (never innerHTML)
// so KR/EN values can never inject markup.
function applyTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.getAttribute("data-i18n");
    if (key && i18nStrings[key]) node.textContent = t(key);
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    const key = node.getAttribute("data-i18n-aria-label");
    if (key && i18nStrings[key]) node.setAttribute("aria-label", t(key));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    const key = node.getAttribute("data-i18n-title");
    if (key && i18nStrings[key]) node.setAttribute("title", t(key));
  });
  const wsLabel = $("workspace-switcher-label");
  if (wsLabel && i18nStrings["workspace.title"]) wsLabel.textContent = t("workspace.title");
  const langLabel = $("lang-toggle-label");
  if (langLabel && i18nStrings["common.language"]) langLabel.textContent = t("common.language");
  const widgetsTitle = $("home-widgets-title");
  if (widgetsTitle && i18nStrings["widgets.title"]) widgetsTitle.textContent = t("widgets.title");
  // Nav tab labels by data-view (the core tabs carry no data-i18n attr). Owner:
  // tab names were stuck in English under KR. Only set when a translation exists.
  document.querySelectorAll(".sidebar-link[data-view]").forEach((link) => {
    const key = "nav." + link.getAttribute("data-view");
    const label = link.querySelector(".sidebar-label");
    if (label && i18nStrings[key]) label.textContent = t(key);
  });
  const moreLabel = document.querySelector(".sidebar-more-summary .sidebar-label");
  if (moreLabel && i18nStrings["nav.more"]) moreLabel.textContent = t("nav.more");
}

// TASK-AR-624: collapse toggle for the work-state hero. Defaults expanded so the
// initial layout is unchanged; the Owner can collapse it to keep the cockpit as
// the top-of-screen focus. State persists in localStorage.
function initWorkStateCollapse() {
  const hero = $("work-state-hero");
  const btn = $("work-state-collapse");
  if (!hero || !btn) return;
  const KEY = "ar624:workStateCollapsed";
  // TASK-AR-631: the hero is second-tier -- collapsed by default so the verdict
  // strip, decision queue, summary strip and flow tiles own the fold. An
  // explicit expand (stored "0") persists across sessions.
  let collapsed = true;
  try { collapsed = window.localStorage.getItem(KEY) !== "0"; } catch (error) {}
  const apply = () => {
    hero.classList.toggle("is-collapsed", collapsed);
    btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
  };
  apply();
  btn.addEventListener("click", () => {
    collapsed = !collapsed;
    try { window.localStorage.setItem(KEY, collapsed ? "1" : "0"); } catch (error) {}
    apply();
  });
}

function setLanguage(lang, persist) {
  currentLanguage = SUPPORTED_LANGUAGES.indexOf(lang) >= 0 ? lang : DEFAULT_LANGUAGE;
  document.documentElement.setAttribute("lang", currentLanguage);
  const select = $("lang-toggle");
  if (select) select.value = currentLanguage;
  if (persist) {
    try { window.localStorage.setItem(LANGUAGE_STORAGE_KEY, currentLanguage); } catch (error) {}
  }
  applyTranslations();
  // Re-render the surfaces that draw translated strings inline.
  renderWorkspaces();
  renderWidgets();
  if (cockpitData) renderCockpit(cockpitData);
  if (workStateData) renderWorkState(workStateData);
}

function initLanguage() {
  currentLanguage = storedLanguage() || DEFAULT_LANGUAGE;
  const select = $("lang-toggle");
  if (select) {
    select.value = currentLanguage;
    select.addEventListener("change", () => setLanguage(select.value, true));
  }
  document.documentElement.setAttribute("lang", currentLanguage);
}

async function loadI18n() {
  try {
    const response = await fetch("/api/i18n", { cache: "no-store" });
    if (!response.ok) return;
    const payload = await response.json();
    const data = (payload && payload.items) || payload;
    if (data && data.strings) {
      i18nStrings = data.strings;
      if (!storedLanguage() && data.default_language) {
        currentLanguage = SUPPORTED_LANGUAGES.indexOf(data.default_language) >= 0 ? data.default_language : DEFAULT_LANGUAGE;
      }
    }
    setLanguage(currentLanguage, false);
  } catch (error) {
    /* i18n table unavailable: data-i18n nodes keep their literal English text */
  }
}

// ----- TASK-AR-341: workspace switcher (read-only list + safe relaunch) -----
// Switching workspaces is a NAVIGATION action. The menu lists registered host
// projects with a recent-state preview and a copy-able relaunch command. It
// NEVER execs an arbitrary path; the only "switch" is reloading the console for
// the current root (a safe self-navigation) or copying the command for another.
function renderWorkspaces() {
  const menu = $("workspace-switcher-menu");
  if (!menu) return;
  const data = (runtimeState && runtimeState.workspaces) || { items: [] };
  const items = data.items || [];
  const current = items.find((item) => item.current);
  const label = $("workspace-switcher-label");
  if (label) label.textContent = current ? (current.name || current.path) : t("workspace.title");
  if (!items.length) {
    menu.innerHTML = `<div class="workspace-switcher-hint">${escapeHtml(t("workspace.title"))}</div>`;
    return;
  }
  const hint = `<div class="workspace-switcher-hint">${escapeHtml(t("workspace.relaunch_hint"))}</div>`;
  const rows = items.map((item) => {
    const recent = item.recent_state || {};
    const previewParts = [];
    if (recent.open_tasks != null) previewParts.push(`${escapeHtml(recent.open_tasks)} tasks`);
    if (recent.last_activity) previewParts.push(escapeHtml(recent.last_activity));
    if (recent.status_title) previewParts.push(escapeHtml(recent.status_title));
    const preview = previewParts.length
      ? `<div class="workspace-item-preview">${previewParts.join(" &middot; ")}</div>`
      : `<div class="workspace-item-preview">${escapeHtml(recent.available ? "no recent activity" : "unavailable")}</div>`;
    const badge = item.current
      ? `<span class="workspace-item-current-badge">${escapeHtml(t("workspace.current"))}</span>`
      : `<button type="button" class="workspace-item-switch" data-workspace-switch="${escapeHtml(item.path)}" data-workspace-current="${item.current ? "1" : "0"}">${escapeHtml(t("workspace.switch"))}</button>`;
    return `<div class="workspace-item${item.current ? " is-current" : ""}" role="menuitem">
      <div class="workspace-item-head"><span class="workspace-item-name">${escapeHtml(item.name || item.path)}</span>${badge}</div>
      <div class="workspace-item-path">${escapeHtml(item.path)}</div>
      ${preview}
      <code class="workspace-item-cmd">${escapeHtml(item.relaunch_command || "")}</code>
    </div>`;
  }).join("");
  menu.innerHTML = hint + rows;
}

function toggleWorkspaceMenu(force) {
  const menu = $("workspace-switcher-menu");
  const toggle = $("workspace-switcher-toggle");
  if (!menu || !toggle) return;
  const willOpen = typeof force === "boolean" ? force : menu.hidden;
  menu.hidden = !willOpen;
  toggle.setAttribute("aria-expanded", willOpen ? "true" : "false");
}

// Safe switch: for the current workspace this is a self-reload (no exec); for a
// different registered host we copy the relaunch command and inform the user.
// The console never spawns or execs an arbitrary root.
function switchWorkspace(path) {
  const data = (runtimeState && runtimeState.workspaces) || { items: [] };
  const target = (data.items || []).find((item) => item.path === path);
  if (!target) return;
  if (target.current) {
    window.location.reload();
    return;
  }
  const command = target.relaunch_command || "";
  if (command && navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(command).catch(() => {});
  }
  toggleWorkspaceMenu(false);
  setText("status-line", command ? `Relaunch command copied: ${command}` : "Workspace relaunch ready");
}

// ----- TASK-AR-341: declarative Home dashboard widgets -----
// Widget definitions are DATA (loaded server-side from JSON/YAML). Every field
// is rendered through escapeHtml; no widget content is ever eval'd or injected
// as raw HTML/JS.
function renderWidgetCard(widget) {
  const title = `<div class="home-widget-title">${escapeHtml(widget.title || "Widget")}</div>`;
  let body = "";
  if (widget.kind === "metric") {
    body = `<div class="home-widget-metric-value">${escapeHtml(widget.value != null ? widget.value : "")}</div>`
      + (widget.caption ? `<div class="home-widget-caption">${escapeHtml(widget.caption)}</div>` : "");
  } else if (widget.kind === "list") {
    const rows = (widget.items || []).map((item) =>
      `<li class="home-widget-list-row"><span>${escapeHtml(item.label || "")}</span><span class="home-widget-list-value">${escapeHtml(item.value != null ? item.value : "")}</span></li>`
    ).join("");
    body = `<ul class="home-widget-list">${rows}</ul>`;
  } else if (widget.kind === "shortcut") {
    const rows = (widget.items || []).map((item) =>
      `<div class="home-widget-shortcut"><span>${escapeHtml(item.label || "")}</span><kbd>${escapeHtml(item.shortcut || "")}</kbd></div>`
    ).join("");
    body = rows || `<div class="home-widget-empty">${escapeHtml(t("widgets.empty"))}</div>`;
  } else {
    body = `<div class="home-widget-note">${escapeHtml(widget.body || "")}</div>`;
  }
  return `<article class="home-widget" data-widget-id="${escapeHtml(widget.id || "")}" data-widget-kind="${escapeHtml(widget.kind || "note")}">${title}${body}</article>`;
}

function renderWidgets() {
  const grid = $("home-widgets-grid");
  if (!grid) return;
  const data = (runtimeState && runtimeState.widgets) || { items: [] };
  const widgets = data.items || [];
  grid.innerHTML = widgets.length
    ? widgets.map(renderWidgetCard).join("")
    : `<div class="home-widget-empty">${escapeHtml(t("widgets.empty"))}</div>`;
}

// --- Decision-first cockpit: attention inbox (TASK-AR-564) -----------------
// Render /api/inbox (six derived groups) as the home hero - "what needs you
// now". Counts + top-3 per group; dynamic text uses textContent (no innerHTML
// interpolation). A derived read: non-fatal if unavailable.
const INBOX_GROUPS = {
  approval_pending:  { labelKey: "inbox.group.approval_pending", icon: "\\u270B", tone: "high" },
  blocked:           { labelKey: "inbox.group.blocked", icon: "\\u26D4", tone: "high" },
  runtime_anomalies: { labelKey: "inbox.group.runtime_anomalies", icon: "\\u26A1", tone: "high" },
  gate_failures:     { labelKey: "inbox.group.gate_failures", icon: "\\u2717", tone: "mid" },
  gate_watch:        { labelKey: "inbox.group.gate_watch", icon: "\\u25CE", tone: "low" },
  cost_anomalies:    { labelKey: "inbox.group.cost_anomalies", icon: "$", tone: "mid" },
  stale:             { labelKey: "inbox.group.stale", icon: "\\u231B", tone: "low" },
  unowned:           { labelKey: "inbox.group.unowned", icon: "\\u25CB", tone: "low" },
};
// Decision-first IA P1 (RFC-2026-06-23): the cockpit renders inbox group cards in
// the Owner-chosen urgency order gate > blocked > stale > risk > unowned. Each
// derived group maps onto a tier; cards sort by (tier, then group definition).
const INBOX_TIER_ORDER = ["gate", "blocked", "stale", "risk", "unowned"];
const INBOX_GROUP_TIER = {
  approval_pending: "gate",
  gate_failures: "gate",
  gate_watch: "gate",
  blocked: "blocked",
  stale: "stale",
  runtime_anomalies: "risk",
  cost_anomalies: "risk",
  unowned: "unowned",
};
function inboxGroupRank(key) {
  const tier = INBOX_GROUP_TIER[key];
  const idx = INBOX_TIER_ORDER.indexOf(tier);
  return idx < 0 ? INBOX_TIER_ORDER.length : idx;
}
let inboxDrawerPreviousFocus = null;

function inboxEl(tag, cls, text) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (text != null) el.textContent = text;
  return el;
}

function inboxGroupMeta(key) {
  const meta = INBOX_GROUPS[key] || { labelKey: "", icon: "\\u2022", tone: "low" };
  return {
    label: meta.labelKey ? t(meta.labelKey) : key,
    icon: meta.icon,
    tone: meta.tone,
  };
}

function localizedInboxTitle(item) {
  return item.title || item.id || t("cockpit.item.untitled");
}

function localizedInboxAction(action) {
  const map = {
    "approve / gate": "inbox.action.approve_gate",
    "resolve blocker": "inbox.action.resolve_blocker",
    "fix gate": "inbox.action.fix_gate",
    "review cost": "inbox.action.review_cost",
    "review / refresh": "inbox.action.review_refresh",
    "resolve claim": "inbox.action.resolve_claim",
    "assign owner": "inbox.action.assign_owner",
    "review gate": "inbox.action.review_gate",
  };
  const key = map[String(action || "")];
  return key ? t(key) : (action || "");
}

function localizedInboxWhy(why) {
  const raw = String(why || "");
  if (!raw) return "";
  if (raw === "approval_required") return t("inbox.why.approval_required");
  let match = raw.match(/^status=(.+)$/);
  if (match) return `${t("inbox.why.status")}=${match[1]}`;
  match = raw.match(/^(\\d+) gate failures$/);
  if (match) return `${match[1]} ${t("inbox.why.gate_failures")}`;
  match = raw.match(/^actual (\\d+) > budget$/);
  if (match) return `${t("inbox.why.actual")} ${match[1]} > ${t("inbox.why.budget")}`;
  match = raw.match(/^no update (\\d+)d$/);
  if (match) return `${t("inbox.why.no_update")} ${match[1]}d`;
  if (raw === "ready, no owner") return t("inbox.why.ready_no_owner");
  const conflictPrefix = "cross-host claim conflict: ";
  if (raw.indexOf(conflictPrefix) === 0) {
    return `${t("inbox.why.cross_host_claim_conflict")}: ${raw.slice(conflictPrefix.length)}`;
  }
  return raw;
}

function inboxSummary(items) {
  if (!items.length) return t("cockpit.summary.empty");
  const first = items[0] || {};
  const title = localizedInboxTitle(first);
  const why = first.why ? ` - ${localizedInboxWhy(first.why)}` : "";
  const action = first.action ? ` (${localizedInboxAction(first.action)})` : "";
  const more = items.length > 1 ? `; ${items.length - 1} ${t("cockpit.summary.more")}` : "";
  return `${title}${why}${action}${more}`;
}

function renderCockpit(data) {
  cockpitData = data || { groups: {}, total: 0 };
  const grid = $("inbox-groups");
  if (!grid) return;
  const total = (data && data.total) || 0;
  const totalEl = $("inbox-total");
  if (totalEl) {
    totalEl.textContent = total
      ? (total === 1 ? t("cockpit.total.one") : `${total} ${t("cockpit.total.many_suffix")}`)
      : t("cockpit.total.clear");
  }
  const empty = $("inbox-empty");
  if (empty) empty.hidden = total > 0;
  // TASK-AR-623: stamp the reference time so an empty cockpit reads as
  // "nothing to do as of HH:MM:SS", never an ambiguous stale/blank screen.
  const emptyAsOf = $("inbox-empty-asof");
  // Middot via char code to keep this JS block ASCII-only (see AR-341 guard).
  if (emptyAsOf) emptyAsOf.textContent = " " + String.fromCharCode(183) + " " + t("cockpit.empty.asof") + " " + freshnessClock();
  grid.hidden = total === 0;
  grid.innerHTML = "";
  const groups = (data && data.groups) || {};
  // Order group cards by the Owner-chosen urgency tier (gate > blocked > stale >
  // risk > unowned); ties fall back to the server's group order.
  const orderedKeys = Object.keys(groups).sort(
    (a, b) => inboxGroupRank(a) - inboxGroupRank(b)
  );
  // TASK-AR-631: the decision queue caps at 5 group cards above the fold; any
  // further non-empty groups collapse into one quiet "+N groups" note card.
  const nonEmptyKeys = orderedKeys.filter((key) => (groups[key] || []).length);
  const visibleKeys = nonEmptyKeys.slice(0, 5);
  for (const key of visibleKeys) {
    const items = groups[key] || [];
    if (!items.length) continue;
    const meta = inboxGroupMeta(key);
    const card = inboxEl("article", `inbox-card tone-${meta.tone}`);
    card.setAttribute("role", "listitem");
    const head = inboxEl("div", "inbox-card-head");
    const ico = inboxEl("span", "inbox-ico", meta.icon);
    ico.setAttribute("aria-hidden", "true");
    head.appendChild(ico);
    head.appendChild(inboxEl("span", "inbox-label", meta.label));
    head.appendChild(inboxEl("span", "inbox-count", String(items.length)));
    card.appendChild(head);
    card.appendChild(inboxEl("p", "inbox-summary-line", inboxSummary(items)));
    const action = inboxEl("button", "inbox-card-action", t("cockpit.open_details"));
    action.type = "button";
    action.dataset.inboxGroup = key;
    action.setAttribute("aria-haspopup", "dialog");
    action.setAttribute("aria-controls", "inbox-detail-drawer");
    action.addEventListener("click", () => openInboxDetail(key, action));
    card.appendChild(action);
    grid.appendChild(card);
  }
  if (nonEmptyKeys.length > visibleKeys.length) {
    const hiddenGroups = nonEmptyKeys.length - visibleKeys.length;
    const hiddenItems = nonEmptyKeys.slice(5).reduce((n, key) => n + (groups[key] || []).length, 0);
    const more = inboxEl(
      "article",
      "inbox-card inbox-card-more tone-low",
      t("cockpit.more_groups").replace("{n}", String(hiddenGroups)).replace("{m}", String(hiddenItems))
    );
    more.setAttribute("role", "listitem");
    grid.appendChild(more);
  }
  // TASK-AR-631: the bottom line references the inbox total, so refresh the
  // verdict strip whenever the cockpit data changes.
  if (typeof renderHomeSummary === "function") renderHomeSummary();
}

// SPEC-decision-inbox-v1: how many decisions the operator has recorded this
// session. Surfaced in the drawer summary so the operate-cycle is visible.
let decisionSessionCount = 0;

// Plain-language, jargon-free sentence explaining WHY this item needs the
// operator (keyed off the inbox group); falls back to the machine "why" so a
// readable line always renders. Understand-first, before any action.
function inboxPlainSentence(item) {
  const meaningKey = "inbox.mean." + String(item.group || "");
  if (i18nStrings && i18nStrings[meaningKey]) return t(meaningKey);
  const why = item.why ? localizedInboxWhy(item.why) : "";
  return why || localizedInboxTitle(item);
}

const DECISION_RECORDED_COPY = {
  "decision.acknowledge": "inbox.decide.recorded_ack",
  "decision.comment": "inbox.decide.recorded_comment",
  "decision.hold": "inbox.decide.recorded_hold",
};

// Proposal-only: records an operator decision under .ui_outbox/decisions/. NEVER
// mutates a canonical task from the UI (a runtime executor consumes it later).
function queueDecision(commandType, item, reason) {
  return sendJson("/api/commands", {
    type: commandType,
    payload: {
      type: commandType,
      target: item.id,
      payload: {
        actor: "owner",
        group: item.group || "",
        title: item.title || "",
        reason: reason || "",
      },
    },
  });
}

function restoreDecideBar(item, row) {
  // Undo (Owner: accidental clicks must be reversible): drop the recorded state and
  // bring the respond bar back so the item looks untouched.
  row.classList.remove("is-decided");
  const rec = row.querySelector(".inbox-decide-recorded");
  if (rec) rec.remove();
  const undo = row.querySelector(".inbox-decide-undo");
  if (undo) undo.remove();
  if (!row.querySelector(".inbox-decide")) row.appendChild(buildDecideBar(item, row));
}

async function undoDecision(item, row) {
  try {
    const result = await sendJson("/api/commands", {
      type: "decision.undo",
      payload: { type: "decision.undo", target: item.id, payload: { actor: "owner" } },
    });
    if (result && result.status === "failed") throw new Error("undo rejected");
    restoreDecideBar(item, row);
    if (decisionSessionCount > 0) decisionSessionCount -= 1;
    const summary = $("inbox-detail-summary");
    if (summary) summary.textContent = `${t("inbox.decide.tally")}: ${decisionSessionCount}`;
  } catch (err) {
    /* leave the recorded state + undo link so the operator can retry */
  }
}

function markDecisionRecorded(item, row, commandType, routed) {
  row.classList.add("is-decided");
  const bar = row.querySelector(".inbox-decide");
  if (bar) bar.remove();
  if (!row.querySelector(".inbox-decide-recorded")) {
    let copyKey = DECISION_RECORDED_COPY[commandType] || "inbox.decide.recorded_ack";
    // Honest copy: only claim "delivered to the agent" when the comment actually
    // reached a real task's agent inbox (server-confirmed agent_routed).
    if (commandType === "decision.comment" && routed) copyKey = "inbox.decide.recorded_comment_routed";
    row.appendChild(inboxEl("p", "inbox-decide-recorded", "\\u2713 " + t(copyKey)));
  }
  if (!row.querySelector(".inbox-decide-undo")) {
    const undoBtn = inboxEl("button", "inbox-decide-undo", t("inbox.decide.undo"));
    undoBtn.type = "button";
    undoBtn.addEventListener("click", () => undoDecision(item, row));
    row.appendChild(undoBtn);
  }
  // The activated control was just removed with the bar; keep keyboard focus on
  // the row (now showing the confirmation) instead of dropping it to <body>.
  row.setAttribute("tabindex", "-1");
  row.focus();
  decisionSessionCount += 1;
  const summary = $("inbox-detail-summary");
  if (summary) summary.textContent = `${t("inbox.decide.tally")}: ${decisionSessionCount}`;
}

async function submitDecision(commandType, item, row, reason, errorEl) {
  try {
    const result = await queueDecision(commandType, item, reason);
    if (result && result.status === "failed") throw new Error("decision rejected");
    const routed = !!(result && result.result && result.result.agent_routed);
    markDecisionRecorded(item, row, commandType, routed);
  } catch (err) {
    if (errorEl) {
      errorEl.textContent = t("inbox.decide.failed");
      errorEl.hidden = false;
    }
  }
}

// The respond bar: acknowledge submits immediately; comment/hold reveal a reason
// field (required) before sending. Real <button>/<textarea> for keyboard a11y.
function buildDecideBar(item, row) {
  const bar = inboxEl("div", "inbox-decide");
  bar.appendChild(inboxEl("span", "inbox-decide-prompt", t("inbox.decide.prompt")));
  const actions = inboxEl("div", "inbox-decide-actions");
  const errorEl = inboxEl("p", "inbox-decide-error");
  errorEl.hidden = true;
  errorEl.setAttribute("role", "alert");

  const reasonWrap = inboxEl("div", "inbox-decide-reason");
  reasonWrap.hidden = true;
  const textarea = document.createElement("textarea");
  textarea.className = "inbox-decide-reason-input";
  textarea.rows = 2;
  textarea.placeholder = t("inbox.decide.reason_placeholder");
  textarea.setAttribute("aria-label", t("inbox.decide.reason_placeholder"));
  const reasonActions = inboxEl("div", "inbox-decide-reason-actions");
  const sendBtn = inboxEl("button", "inbox-decide-btn is-primary", t("inbox.decide.submit"));
  sendBtn.type = "button";
  const cancelBtn = inboxEl("button", "inbox-decide-btn is-ghost", t("inbox.decide.cancel"));
  cancelBtn.type = "button";
  reasonActions.appendChild(sendBtn);
  reasonActions.appendChild(cancelBtn);
  reasonWrap.appendChild(textarea);
  reasonWrap.appendChild(reasonActions);

  let pendingType = null;
  let pendingOpener = null;
  function openReason(commandType, openerBtn) {
    pendingType = commandType;
    pendingOpener = openerBtn || null;
    reasonWrap.hidden = false;
    errorEl.hidden = true;
    textarea.focus();
  }
  cancelBtn.addEventListener("click", () => {
    reasonWrap.hidden = true;
    pendingType = null;
    // Cancel hides its own button; return focus to the trigger, not <body>.
    const opener = pendingOpener;
    pendingOpener = null;
    if (opener && typeof opener.focus === "function") opener.focus();
  });
  sendBtn.addEventListener("click", () => {
    const reason = textarea.value.trim();
    if (!reason) {
      errorEl.textContent = t("inbox.decide.reason_required");
      errorEl.hidden = false;
      textarea.focus();
      return;
    }
    submitDecision(pendingType || "decision.comment", item, row, reason, errorEl);
  });

  const ackBtn = inboxEl("button", "inbox-decide-btn", t("inbox.decide.acknowledge"));
  ackBtn.type = "button";
  ackBtn.addEventListener("click", () => submitDecision("decision.acknowledge", item, row, "", errorEl));
  const commentBtn = inboxEl("button", "inbox-decide-btn", t("inbox.decide.comment"));
  commentBtn.type = "button";
  commentBtn.addEventListener("click", () => openReason("decision.comment", commentBtn));
  const holdBtn = inboxEl("button", "inbox-decide-btn", t("inbox.decide.hold"));
  holdBtn.type = "button";
  holdBtn.addEventListener("click", () => openReason("decision.hold", holdBtn));
  actions.appendChild(ackBtn);
  actions.appendChild(commentBtn);
  actions.appendChild(holdBtn);

  bar.appendChild(actions);
  bar.appendChild(reasonWrap);
  bar.appendChild(errorEl);
  return bar;
}

function renderInboxDetailItem(item) {
  const row = inboxEl("article", "inbox-detail-item");
  row.setAttribute("role", "listitem");
  row.appendChild(inboxEl("h3", "inbox-detail-item-title", localizedInboxTitle(item)));
  // Understand-first: the plain-language sentence leads; machine detail is muted.
  row.appendChild(inboxEl("p", "inbox-detail-item-lead", inboxPlainSentence(item)));
  const meta = inboxEl("div", "inbox-detail-item-meta");
  if (item.id) meta.appendChild(inboxEl("span", "", item.id));
  if (item.age) meta.appendChild(inboxEl("span", "", item.age));
  if (item.why) meta.appendChild(inboxEl("span", "", localizedInboxWhy(item.why)));
  if (item.action) meta.appendChild(inboxEl("span", "inbox-detail-item-action", localizedInboxAction(item.action)));
  row.appendChild(meta);
  // Respond bar only for items with a stable id we can address in the proposal.
  if (item.id) row.appendChild(buildDecideBar(item, row));
  return row;
}

function openInboxDetail(groupKey, opener) {
  const drawer = $("inbox-detail-drawer");
  const backdrop = $("inbox-detail-backdrop");
  const title = $("inbox-detail-title");
  const summary = $("inbox-detail-summary");
  const list = $("inbox-detail-list");
  if (!drawer || !backdrop || !title || !summary || !list) return;
  const groups = (cockpitData && cockpitData.groups) || {};
  const items = groups[groupKey] || [];
  const meta = inboxGroupMeta(groupKey);
  inboxDrawerPreviousFocus = opener || document.activeElement;
  title.textContent = `${meta.label} (${items.length})`;
  summary.textContent = items.length
    ? t("cockpit.detail.summary")
    : t("cockpit.detail.empty");
  list.innerHTML = "";
  for (const item of items) list.appendChild(renderInboxDetailItem(item || {}));
  backdrop.hidden = false;
  drawer.hidden = false;
  drawer.focus();
  const close = $("inbox-detail-close");
  if (close) close.focus();
}

function closeInboxDetail() {
  const drawer = $("inbox-detail-drawer");
  const backdrop = $("inbox-detail-backdrop");
  if (drawer) drawer.hidden = true;
  if (backdrop) backdrop.hidden = true;
  const target = inboxDrawerPreviousFocus;
  inboxDrawerPreviousFocus = null;
  if (target && typeof target.focus === "function") target.focus();
}

function initInboxDetailDrawer() {
  $("inbox-detail-close")?.addEventListener("click", closeInboxDetail);
  $("inbox-detail-backdrop")?.addEventListener("click", closeInboxDetail);
  document.addEventListener("keydown", (event) => {
    const drawer = $("inbox-detail-drawer");
    if (event.key === "Escape" && drawer && !drawer.hidden) {
      event.preventDefault();
      closeInboxDetail();
    }
  });
}

async function loadCockpit() {
  try {
    const response = await fetch("/api/inbox", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderCockpit(await response.json());
  } catch (error) {
    const totalEl = $("inbox-total");
    if (totalEl) totalEl.textContent = t("cockpit.unavailable");
  }
}

function workStatePayload(data) {
  return (data && data.items) || data || { tasksets: [], totals: {} };
}

function localizedWorkBucket(bucket) {
  const raw = String(bucket || "waiting");
  const key = `work_state.bucket.${raw}`;
  return i18nStrings[key] ? t(key) : raw;
}

function renderWorkStateCount(label, value) {
  const tile = inboxEl("div", "work-state-count");
  tile.appendChild(inboxEl("strong", "", String(value || 0)));
  tile.appendChild(inboxEl("span", "", label));
  return tile;
}

function renderWorkStateCard(card) {
  const counts = card.counts || {};
  const article = inboxEl("article", "work-state-card");
  if ((card.active_total || 0) > 0) article.classList.add("is-hot");
  else if ((counts.waiting || 0) > 0) article.classList.add("is-waiting");
  article.setAttribute("role", "listitem");
  article.appendChild(inboxEl("p", "work-state-path", card.initiative_id || card.id || "taskset"));
  article.appendChild(inboxEl("h3", "work-state-card-title", card.title || card.id || "Untitled taskset"));

  const countGrid = inboxEl("div", "work-state-counts");
  countGrid.appendChild(renderWorkStateCount(t("work_state.count.waiting"), counts.waiting));
  countGrid.appendChild(renderWorkStateCount(t("work_state.count.active"), counts.active));
  countGrid.appendChild(renderWorkStateCount(t("work_state.count.review"), counts.review));
  countGrid.appendChild(renderWorkStateCount(t("work_state.count.done"), counts.done));
  article.appendChild(countGrid);

  const tasks = Array.isArray(card.tasks) ? card.tasks : [];
  const details = inboxEl("details", "work-state-drill");
  const summaryText = card.hidden_tasks
    ? `${tasks.length} ${t("work_state.units.shown")}, ${card.hidden_tasks} ${t("work_state.units.hidden")}`
    : `${tasks.length} ${t("work_state.units")}`;
  details.appendChild(inboxEl("summary", "", summaryText));
  const list = inboxEl("div", "work-state-units");
  list.setAttribute("role", "list");
  for (const task of tasks) {
    const row = inboxEl("div", "work-state-unit");
    row.setAttribute("role", "listitem");
    row.appendChild(inboxEl("span", "", task.id || task.title || "untitled"));
    row.appendChild(inboxEl("span", "work-state-bucket", localizedWorkBucket(task.bucket || task.status || "waiting")));
    list.appendChild(row);
  }
  details.appendChild(list);
  article.appendChild(details);
  return article;
}

function renderWorkState(data) {
  workStateData = data || null;
  const payload = workStatePayload(data);
  const board = $("work-state-board");
  if (!board) return;
  const tasksets = Array.isArray(payload.tasksets) ? payload.tasksets : [];
  const totals = payload.totals || {};
  const totalEl = $("work-state-total");
  if (totalEl) {
    const taskCount = totals.tasks || 0;
    totalEl.textContent = taskCount
      ? `${totals.tasksets || tasksets.length} ${t("work_state.total.tasksets")} / ${taskCount} ${t("work_state.total.units")}`
      : t("work_state.total.none");
  }
  const empty = $("work-state-empty");
  if (empty) empty.hidden = tasksets.length > 0;
  board.hidden = tasksets.length === 0;
  board.replaceChildren();
  for (const card of tasksets.slice(0, 6)) {
    board.appendChild(renderWorkStateCard(card || {}));
  }
}

async function loadWorkState() {
  try {
    const response = await fetch("/api/work-state", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    renderWorkState(await response.json());
  } catch (error) {
    const totalEl = $("work-state-total");
    if (totalEl) totalEl.textContent = t("work_state.unavailable");
  }
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
    $("status-line").textContent = t("error.state_load_failed") + ": " + error.message;
  }
}

function connectEventStream() {
  if (!window.EventSource || eventStream) return;
  eventStream = new EventSource("/api/stream");
  eventStream.addEventListener("state", (event) => {
    // B-03: dedupe identical snapshots. /api/stream is single-shot, so a
    // reconnect re-delivers a frame; if it matches the last one we skip the
    // expensive re-render + live-map reconciliation entirely so reconnects can't
    // storm the heavy state path on top of setInterval(loadState). The server
    // also advertises a long `retry:` so the reconnect cadence stays sane.
    if (event.data === lastStreamPayload) {
      setText("poll-state", "live");
      return;
    }
    lastStreamPayload = event.data;
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
""" + ui_design_assets.UI_COMPONENTS_JS + """
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
    // TASK-AR-591: componentEmptyState (via emptyState compat wrapper) for list surfaces.
    panel.innerHTML = emptyState(emptyLabel || t("empty.no_items"));
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
let commandPaletteIndex = 0;

// TASK-AR-625: derive palette targets from the live sidebar nav instead of a
// hardcoded list that drifted out of date (growth/workload/office/org/inbox/
// channels/calendar/deps/knowledge-graph were unreachable). Single source of
// truth = the nav links, so every registered view is always jumpable.
function commandPaletteCommands() {
  const seen = new Set();
  const commands = [];
  navLinks().forEach((link) => {
    const view = link.dataset.view;
    if (!view || seen.has(view)) return;
    seen.add(view);
    const label = (link.querySelector(".sidebar-label")?.textContent || view).trim();
    commands.push({ id: `view:${view}`, label: `Go to ${label}`, run: () => activateView(view) });
  });
  commands.push({ id: "action:refresh", label: "Refresh state", run: loadState });
  return commands;
}

// TASK-AR-625: the .tab-based activateView here was dead (the real nav uses
// .sidebar-link, and the later activateView declaration overrode this one), so
// it never ran. Removed to end the confusing duplicate. The canonical
// activateView(view, {updateHash}) lives with the hash router below.

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
let searchViewResults = [];
let searchViewActiveIndex = 0;
let searchViewDebounce = null;
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

function renderSearchViewResults(query) {
  const box = $("search-view-results");
  if (!box) return;
  if (!query) {
    box.innerHTML = "";
    return;
  }
  if (!searchViewResults.length) {
    box.innerHTML = `<div class="search-empty">No matches for &ldquo;${escapeHtml(query)}&rdquo;</div>`;
    return;
  }
  if (searchViewActiveIndex >= searchViewResults.length) searchViewActiveIndex = searchViewResults.length - 1;
  if (searchViewActiveIndex < 0) searchViewActiveIndex = 0;
  box.innerHTML = searchViewResults
    .map((item, index) => searchResultRow(item, index, index === searchViewActiveIndex))
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

function runSearchView() {
  const input = $("search-view-input");
  const query = input ? input.value.trim() : "";
  if (!query) {
    searchViewResults = [];
    renderSearchViewResults("");
    return;
  }
  fetchSearch(query)
    .then((payload) => {
      searchViewResults = payload.items || [];
      searchViewActiveIndex = 0;
      renderSearchViewResults(query);
    })
    .catch(() => {
      searchViewResults = [];
      renderSearchViewResults(query);
    });
}

function focusSearchView() {
  const input = $("search-view-input") || $("global-search-input");
  if (!input) return;
  input.focus();
  if (typeof input.select === "function") input.select();
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

// TASK-AR-623: freshness of the assembled snapshot. built_at is fixed for the
// life of a cached build (generated_at re-stamps every poll), so its age is the
// real "how current is this data" signal. Watch color only near the server TTL
// backstop (300s) -- a quiet system with recent data must stay calm.
const FRESHNESS_STALE_SECONDS = 240;

function parseIsoDate(value) {
  if (!value) return null;
  const d = new Date(value);
  return isNaN(d.getTime()) ? null : d;
}

function freshnessAgeText(seconds) {
  if (seconds < 5) return t("status.age_now");
  if (seconds < 90) return Math.round(seconds) + t("status.age_seconds_suffix");
  return Math.round(seconds / 60) + t("status.age_minutes_suffix");
}

function stateFreshness() {
  const built = parseIsoDate(runtimeState.built_at || runtimeState.generated_at);
  const ageSec = built ? Math.max(0, (Date.now() - built.getTime()) / 1000) : 0;
  return { built, ageSec, stale: built ? ageSec >= FRESHNESS_STALE_SECONDS : false };
}

function freshnessClock() {
  const f = stateFreshness();
  return f.built ? f.built.toLocaleTimeString() : "--:--:--";
}

// TASK-AR-631: decision screenfit. One glance answers "do I need to step in?":
// verdict badge + bottom line (from health_snapshot + inbox total), a quiet
// one-line summary strip, and three flow tiles (WIP / weekly throughput /
// median cycle time) with real-series sparklines only (honesty rule).
const HOME_ACTIVE_CLAIM_STATUSES = ["assigned", "claimed", "in_progress", "review", "waiting_review", "working"];
const HOME_WIP_LIMIT = 3;
const HOME_DONE_STATUSES = ["completed", "done", "closed"];

function flowTileHtml(label, value, unit, series, warn) {
  const spark = series && series.length >= 2 && typeof componentSparkline === "function"
    ? componentSparkline(series, { width: 96, height: 24 })
    : "";
  return '<div class="flow-tile' + (warn ? " ft-warn" : "") + '">' +
    '<span class="ft-label">' + escapeHtml(label) + '</span>' +
    '<span class="ft-value">' + escapeHtml(value) +
    (unit ? '<span class="ft-unit">' + escapeHtml(unit) + "</span>" : "") + "</span>" +
    '<span class="ft-spark">' + spark + "</span></div>";
}

function renderHomeSummary() {
  const ops = (runtimeState && runtimeState.ops_metrics) || {};
  const health = ops.health_snapshot || {};
  const verdict = String(health.verdict || "");
  const wrap = $("home-verdict");
  const badge = $("verdict-badge");
  const line = $("verdict-line");
  const inboxTotal = cockpitData && typeof cockpitData.total === "number" ? cockpitData.total : null;
  if (wrap) {
    wrap.hidden = !verdict;
    if (badge && verdict) {
      badge.textContent = t("health.verdict." + verdict);
      badge.setAttribute("data-verdict", verdict);
    }
    if (line) {
      let text = "";
      if (inboxTotal === 0) text = t("home.bottomline.clear");
      else if (inboxTotal !== null) text = t("home.bottomline.attention").replace("{n}", String(inboxTotal));
      line.textContent = text;
    }
  }
  const tasks = runtimeState.tasks || [];
  const openCount = tasks.filter(
    (task) => HOME_DONE_STATUSES.indexOf(String(task.status || "").toLowerCase()) < 0
  ).length;
  const claims = (runtimeState.task_claims || []).filter(
    (claim) => HOME_ACTIVE_CLAIM_STATUSES.indexOf(String(claim.status || "").toLowerCase()) >= 0
  );
  const wip = claims.length;
  const activeAgents = new Set(
    claims.map((claim) => String(claim.agent_instance_id || claim.agent || "")).filter(Boolean)
  ).size;
  const gateCounts = (ops.gates && ops.gates.counts) || {};
  const stripEl = $("strip-line");
  if (stripEl) {
    const gatesText = Number(gateCounts.block || 0) > 0
      ? "block " + gateCounts.block
      : Number(gateCounts.watch || 0) > 0
        ? "watch " + gateCounts.watch
        : "pass";
    const agentsText = activeAgents > 0 ? activeAgents + " " + t("strip.active") : t("strip.idle");
    const dot = " " + String.fromCharCode(183) + " ";
    stripEl.textContent =
      t("strip.open") + " " + openCount +
      dot + "WIP " + wip + "/" + HOME_WIP_LIMIT +
      dot + t("strip.gates") + " " + gatesText +
      dot + t("strip.agents") + " " + agentsText;
  }
  const tiles = $("flow-tiles");
  if (tiles) {
    const weeks = ((ops.velocity || {}).weeks || []).map((week) => Number(week.done || 0));
    const throughput = weeks.length ? weeks[weeks.length - 1] : null;
    const cycle = ops.cycle_time || {};
    const cycleSeries = (cycle.weeks || [])
      .map((week) => (week.median_hours == null ? null : Number(week.median_hours)))
      .filter((value) => value !== null);
    tiles.innerHTML =
      flowTileHtml(t("tile.wip"), String(wip), "/" + HOME_WIP_LIMIT, null, wip > HOME_WIP_LIMIT) +
      flowTileHtml(t("tile.throughput"), throughput === null ? "-" : String(throughput), t("tile.per_week"), weeks, false) +
      flowTileHtml(t("tile.cycle"), cycle.median_hours == null ? "-" : String(cycle.median_hours), "h", cycleSeries, false);
  }
}

function renderDashboard() {
  const tasks = runtimeState.tasks || [];
  const counts = taskCounts(tasks);
  setText("metric-tasks", tasks.length);
  setText("metric-active", counts.active);
  setText("metric-blocked", counts.blocked);
  setText("metric-warnings", (runtimeState.warnings || []).length + (runtimeState.gaps || []).length);
  const line = $("status-line");
  if (line) {
    const f = stateFreshness();
    let text = t("status.freshness_prefix") + " " + freshnessClock()
      + " (" + freshnessAgeText(f.ageSec) + ") - " + tasks.length + " " + t("status.tasks_suffix");
    if (f.stale) text += " - " + t("status.stale_note");
    line.textContent = text;
    line.classList.toggle("is-stale", f.stale);
    line.setAttribute("title", t("status.generated_prefix") + " " + (runtimeState.generated_at || "")
      + (runtimeState.source_latest_at ? " / src " + runtimeState.source_latest_at : ""));
  }
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
    return `${alias} \\uacc4\\ud68d: ${command} \\uc2e4\\ud589 \\ud6c4 next task, worktree, claim \\uacbd\\uacc4\\ub97c \\ubcf4\\uace0\\ud574\\uc918.`;
  }
  if (action === "start") {
    return `${alias} \\uc9c4\\ud589: ${command} \\uc2e4\\ud589 \\ud6c4 ${taskSet.id} \\ubc94\\uc704 \\uc548\\uc5d0\\uc11c\\ub9cc \\uc9c4\\ud589\\ud558\\uace0 \\uc644\\ub8cc \\uc2dc \\uc815\\uc9c0/\\ubcf4\\uace0\\ud574\\uc918.`;
  }
  return `${alias} gate \\ud655\\uc778: ${command} \\uc2e4\\ud589 \\ud6c4 \\uacb0\\uacfc\\ub97c \\ubcf4\\uace0\\ud574\\uc918.`;
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
  const options = ['<option value="">Move to taskset&hellip;</option>'].concat(
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
  pushActivityToast("assignment", t("toast.taskset_action_prefix") + " " + action, `${taskSetId} (${(result && result.status) || "queued"})`);
}

async function submitTasksetCreate(displayName, summary) {
  const payload = { actor: "owner", display_name: displayName };
  if (summary) payload.summary = summary;
  const result = await sendJson("/api/commands", { type: "taskset.create", payload: { type: "taskset.create", payload } });
  pushActivityToast("assignment", t("toast.taskset_created"), `${displayName} (${(result && result.status) || "queued"})`);
  return result;
}

async function instantiateTasksetTemplate(templateKey) {
  const result = await sendJson("/api/commands", {
    type: "taskset.template",
    payload: { type: "taskset.template", payload: { actor: "owner", template: templateKey } }
  });
  const created = (result && result.result) || {};
  pushActivityToast("assignment", t("toast.template_instantiated"), `${templateKey}: ${created.task_count || 0} tasks`);
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
    pushUndoToast(ids.length + " " + t("toast.tasks_moved_suffix"), null);
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
  pushUndoToast(ids.length + " " + t("toast.tasks_edited_suffix"), undo);
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
    button.textContent = t("toast.undo");
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
  pushActivityToast("review", t("toast.undo_applied"), (undo.items || []).length + " " + t("toast.tasks_restored_suffix"));
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
  host.innerHTML = taskSets.length
    ? taskSetCards(taskSets)
    : emptyState(questTerm("No tasksets yet", "No quests yet"), "Create a taskset to start coordinating work.");
  wireTaskSetActions(host);
  populateBulkMoveOptions();
  renderBulkBar();
  renderTasksetTemplates();
}

// Track the most recent completed taskset so a celebration fires exactly once
// per new completion (only when gamification is enabled).
let lastCelebratedTasksetId = null;

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
  // Gamification: celebrate a freshly-completed taskset once. No-op when the
  // gamify policy is off (celebrate() and playCompletionSound() both guard).
  const completedId = completion.completed_task_set_id || completion.completed_display_name || null;
  if (completedId && completedId !== lastCelebratedTasksetId) {
    if (lastCelebratedTasksetId !== null && gamifyEnabled()) {
      celebrate(48);
      playCompletionSound();
    }
    lastCelebratedTasksetId = completedId;
  }
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
  return patternClaimCard(task, {
    status,
    priority,
    statusClass: statusClassName(status),
    taskSet,
    evidence,
    inflight: inflightAnnotation(task),
    quickActions: [
      { action: "claim", label: "Claim" },
      { action: "verify", label: "Verify" },
      { action: "close", label: "Close" },
    ],
  });
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
    // Drag physics (lift + tilt) is motion-gated via CSS; safe to add always.
    card.classList.add("ar-dragging");
    hidePeek();
    if (event.dataTransfer) {
      event.dataTransfer.setData("text/plain", card.dataset.taskId);
      event.dataTransfer.effectAllowed = "move";
    }
  });
  card.addEventListener("dragend", () => {
    card.classList.remove("is-dragging");
    card.classList.remove("ar-dragging");
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

// SPEC-board-taskview-v1: don't dump all tasks. Done collapses to a few recents,
// every lane caps with "more", and a controls bar adds text filter / sort / density
// (mailbox-like). Pure helpers below are node-verified via the /app.js slice.
let boardSort = "priority";
let boardDensity = "comfortable";
let boardQuery = "";
const boardExpandedLanes = {};
// BOARD_PURE_START
const BOARD_LANE_CAP = 8;
const BOARD_DONE_CAP = 5;
const BOARD_PRIORITY_ORDER = { P0: 0, P1: 1, P2: 2, P3: 3 };

function boardFilterTasks(tasks, query) {
  const q = String(query || "").trim().toLowerCase();
  if (!q) return tasks.slice();
  return tasks.filter(function (t) {
    const hay = ((t.id || "") + " " + (t.title || "") + " " + (t.owner_agent || "") + " " + (t.task_set_id || "")).toLowerCase();
    return hay.indexOf(q) !== -1;
  });
}

function boardSortTasks(tasks, key) {
  const arr = tasks.slice();
  if (key === "updated") {
    arr.sort(function (a, b) { return String(b.updated_at || "").localeCompare(String(a.updated_at || "")); });
  } else if (key === "title") {
    arr.sort(function (a, b) { return String(a.title || a.id || "").localeCompare(String(b.title || b.id || "")); });
  } else {
    arr.sort(function (a, b) {
      const pa = (BOARD_PRIORITY_ORDER[a.priority] !== undefined) ? BOARD_PRIORITY_ORDER[a.priority] : 9;
      const pb = (BOARD_PRIORITY_ORDER[b.priority] !== undefined) ? BOARD_PRIORITY_ORDER[b.priority] : 9;
      return pa - pb;
    });
  }
  return arr;
}

function boardLaneCap(lane) {
  return lane === "Done" ? BOARD_DONE_CAP : BOARD_LANE_CAP;
}
// BOARD_PURE_END

function refreshBoardControlLabels() {
  const q = $("board-filter");
  if (q) q.placeholder = t("board.filter_placeholder");
  const s = $("board-sort");
  if (s) {
    const sortKeys = { priority: "board.sort_priority", updated: "board.sort_updated", title: "board.sort_title" };
    Array.from(s.options).forEach((o) => { o.textContent = t(sortKeys[o.value] || "board.sort_priority"); });
  }
  const d = $("board-density");
  if (d) d.textContent = boardDensity === "compact" ? t("board.density_comfortable") : t("board.density_compact");
}

function initBoardControls() {
  const q = $("board-filter");
  if (q) q.addEventListener("input", () => { boardQuery = q.value; renderKanban(); });
  const s = $("board-sort");
  if (s) s.addEventListener("change", () => { boardSort = s.value; renderKanban(); });
  const d = $("board-density");
  if (d) d.addEventListener("click", () => {
    boardDensity = boardDensity === "compact" ? "comfortable" : "compact";
    d.setAttribute("aria-pressed", boardDensity === "compact" ? "true" : "false");
    renderKanban();
  });
  refreshBoardControlLabels();
}

function renderKanban() {
  let tasks = (runtimeState.tasks || []).filter(taskMatchesTeamFilter);
  tasks = boardSortTasks(boardFilterTasks(tasks, boardQuery), boardSort);
  renderBoardTeamFilterBanner();
  if (boardLifted && !taskById(boardLifted.id)) clearLift();
  const kb = $("kanban");
  refreshBoardControlLabels();
  kb.classList.toggle("density-compact", boardDensity === "compact");
  kb.innerHTML = lanes.map((lane) => {
    const laneTasks = tasks.filter((task) => task.lane === lane);
    const cap = boardLaneCap(lane);
    const expanded = !!boardExpandedLanes[lane];
    const shown = expanded ? laneTasks : laneTasks.slice(0, cap);
    let body = shown.length
      ? shown.map(taskCard).join("")
      : `<div class="empty">${boardQuery ? t("board.no_matches") : t("board.no_tasks")}</div>`;
    const hidden = laneTasks.length - shown.length;
    if (hidden > 0) {
      body += `<button type="button" class="lane-more" data-lane="${escapeHtml(lane)}">${t("board.more")} (${hidden})</button>`;
    } else if (expanded && laneTasks.length > cap) {
      body += `<button type="button" class="lane-more" data-lane="${escapeHtml(lane)}">${t("board.collapse")}</button>`;
    }
    return patternTaskLane({ name: lane, className: laneClassName(lane), count: laneTasks.length, body });
  }).join("");
  kb.querySelectorAll(".task-card").forEach(wireBoardCard);
  kb.querySelectorAll(".lane").forEach(wireLaneDropTarget);
  kb.querySelectorAll(".lane-more").forEach((btn) => btn.addEventListener("click", () => {
    boardExpandedLanes[btn.dataset.lane] = !boardExpandedLanes[btn.dataset.lane];
    renderKanban();
  }));
  renderLift();
}

function agentProgressLabel(agent) {
  const pct = numericPct(agent.progress_pct);
  return pct === null ? "~" : `${pct}%`;
}

function agentCardTemplate(agent) {
  const avatarSeed = agent.id || agent.role || "agent";
  const avatarLabel = agent.display_name || agent.role || "agent";
  return `
    <article class="agent-card ${agent.online ? "ok" : "warn"}">
      <div class="agent-card-header">
        ${patternAgentAvatar(avatarSeed, { role: agent.role || "", size: 40, label: avatarLabel })}
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
  renderGroupedList("agents", agents, agentCardTemplate, t("empty.no_active_sessions"));
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
  renderGroupedList("messages", messages, messageRowTemplate, t("empty.no_messages"));
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
  const messageId = escapeHtml(message.id || "");
  // Pin / react are proposal-only (TASK-AR-338); buttons need a valid id.
  const actions = message.id
    ? `<div class="channel-message-actions">
        <button type="button" class="channel-msg-action" data-msg-pin="${messageId}" title="Pin message">Pin</button>
        <button type="button" class="channel-msg-action" data-msg-react="${messageId}" title="React (ack)">Ack</button>
      </div>`
    : "";
  return `
    <div class="channel-message" data-message-id="${messageId}">
      <span class="channel-avatar" style="--role-color: ${color}" aria-hidden="true">${escapeHtml(message.avatar || "?")}</span>
      <div class="channel-message-body">
        <div class="channel-message-head">
          <span class="channel-sender" style="--role-color: ${color}">${escapeHtml(message.from || "unknown")}</span>
          <span class="channel-ts">${escapeHtml(message.ts || "")}</span>
        </div>
        <div class="channel-message-text">${escapeHtml(message.body || "")}</div>
        ${actions}
      </div>
    </div>`;
}

async function pinMessage(messageId) {
  return sendJson("/api/commands", { type: "message.pin", payload: { type: "message.pin", target: messageId, payload: { actor: "owner" } } });
}

async function reactToMessage(messageId, reaction) {
  return sendJson("/api/commands", { type: "message.react", payload: { type: "message.react", target: messageId, payload: { actor: "owner", reaction: reaction || "ack" } } });
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
  host.querySelectorAll("[data-msg-pin]").forEach((node) => {
    node.addEventListener("click", () => pinMessage(node.dataset.msgPin));
  });
  host.querySelectorAll("[data-msg-react]").forEach((node) => {
    node.addEventListener("click", () => reactToMessage(node.dataset.msgReact, "ack"));
  });
}

function renderChannels() {
  renderChannelsList();
  renderChannelsMain();
}

// ----- TASK-AR-338: notification center + daily brief -----
const inboxFilters = { kind: "", severity: "", unread: false, showMuted: false };

function notificationsData() {
  return (runtimeState && runtimeState.notifications) || { inbox: [], muted: [], totals: {}, kinds: [], severities: [] };
}

function dailyBriefData() {
  return (runtimeState && runtimeState.daily_brief) || { completed: [], blocked: [], decisions: [], next_recommended: [], totals: {} };
}

function inboxSeverityLabel(severity) {
  const map = { overdue: "overdue", due_soon: "due soon", blocked: "blocked", approval: "approval", mention: "mention", error: "error", info: "info" };
  return map[severity] || String(severity || "info");
}

function inboxItemTemplate(item) {
  const severity = String(item.severity || "info").replace(/[^a-z_]/g, "");
  const classes = ["inbox-item"];
  if (!item.read) classes.push("is-unread");
  if (item.muted) classes.push("is-muted");
  if (item.highlighted) classes.push("is-highlighted");
  const meta = [];
  if (item.kind) meta.push(escapeHtml(item.kind));
  if (item.task_id) meta.push(escapeHtml(item.task_id));
  if (item.taskset_id) meta.push(escapeHtml(item.taskset_id));
  if (item.created_at) meta.push(escapeHtml(item.created_at));
  const link = item.deep_link ? escapeHtml(item.deep_link) : "";
  return `
    <article class="${classes.join(" ")}" data-severity="${escapeHtml(severity)}" data-notif-id="${escapeHtml(item.id || "")}" data-entity-id="${escapeHtml(item.entity_id || "")}">
      <span class="inbox-badge" data-severity="${escapeHtml(severity)}">${escapeHtml(inboxSeverityLabel(item.severity))}</span>
      <div class="inbox-item-main">
        <div class="inbox-item-title">${escapeHtml(item.title || item.id || "notification")}</div>
        <div class="inbox-item-body">${escapeHtml(item.body || "")}</div>
        <div class="inbox-item-meta">${meta.map((value) => `<span>${value}</span>`).join("")}</div>
      </div>
      <div class="inbox-item-actions">
        ${link ? `<button type="button" data-inbox-open="${link}">Open</button>` : ""}
        ${item.read ? "" : `<button type="button" data-inbox-read="${escapeHtml(item.id || "")}">Mark read</button>`}
        <button type="button" data-inbox-mute="${escapeHtml(item.id || "")}">Mute</button>
      </div>
    </article>`;
}

function renderInbox() {
  const host = $("inbox-list");
  if (!host) return;
  const data = notificationsData();
  const totals = data.totals || {};
  populateInboxSelectors(data);

  const summary = $("inbox-summary");
  if (summary) {
    summary.innerHTML = `<strong>${escapeHtml(totals.inbox || 0)}</strong> notifications`
      + ` &middot; unread <strong>${escapeHtml(totals.unread || 0)}</strong>`
      + ` &middot; muted <strong>${escapeHtml(totals.muted || 0)}</strong>`
      + ` &middot; proposal-only actions`;
  }

  const badge = $("inbox-nav-badge");
  if (badge) {
    const unread = Number(totals.unread || 0);
    badge.textContent = String(unread);
    badge.hidden = unread <= 0;
  }

  const base = inboxFilters.showMuted ? (data.muted || []) : (data.inbox || []);
  const rows = base.filter((item) => {
    if (inboxFilters.kind && item.kind !== inboxFilters.kind) return false;
    if (inboxFilters.severity && item.severity !== inboxFilters.severity) return false;
    if (inboxFilters.unread && item.read) return false;
    return true;
  });
  host.innerHTML = rows.length
    ? rows.map(inboxItemTemplate).join("")
    : `<div class="empty">No notifications</div>`;

  host.querySelectorAll("[data-inbox-open]").forEach((node) => {
    node.addEventListener("click", () => { window.location.hash = node.dataset.inboxOpen; });
  });
  host.querySelectorAll("[data-inbox-read]").forEach((node) => {
    node.addEventListener("click", () => markNotificationRead(node.dataset.inboxRead));
  });
  host.querySelectorAll("[data-inbox-mute]").forEach((node) => {
    node.addEventListener("click", () => muteNotification(node.dataset.inboxMute));
  });

  renderDailyBrief();
}

function populateInboxSelectors(data) {
  const kinds = data.kinds || [];
  const severities = data.severities || [];
  const fillSelect = (id, values, selected, anyLabel) => {
    const node = $(id);
    if (!node) return;
    const opts = [`<option value="">${escapeHtml(anyLabel)}</option>`]
      .concat(values.map((value) => `<option value="${escapeHtml(value)}"${value === selected ? " selected" : ""}>${escapeHtml(value)}</option>`));
    node.innerHTML = opts.join("");
    node.value = selected || "";
  };
  fillSelect("inbox-filter-kind", kinds, inboxFilters.kind, "All");
  fillSelect("inbox-filter-severity", severities, inboxFilters.severity, "All");
  fillSelect("inbox-sub-kind", kinds, "", "kind (any)");
  fillSelect("inbox-sub-severity", severities, "", "severity (any)");
}

function dailyBriefSection(kind, title, items, emptyLabel) {
  const body = items.length
    ? items.map((item) => {
        const link = item.deep_link ? escapeHtml(item.deep_link) : "";
        const idText = item.id ? `<code>${escapeHtml(item.id)}</code> ` : "";
        return `<span class="daily-brief-item"${link ? ` data-inbox-open="${link}"` : ""}>${idText}${escapeHtml(item.title || item.id || "")}</span>`;
      }).join("")
    : `<div class="daily-brief-empty">${escapeHtml(emptyLabel)}</div>`;
  return `<div class="daily-brief-section is-${escapeHtml(kind)}">
    <div class="daily-brief-section-title">${escapeHtml(title)} (${items.length})</div>
    ${body}
  </div>`;
}

function renderDailyBrief() {
  const host = $("daily-brief-body");
  if (!host) return;
  const data = dailyBriefData();
  const dateNode = $("daily-brief-date");
  if (dateNode) dateNode.textContent = data.date || "";
  host.innerHTML = [
    dailyBriefSection("completed", "Completed today", data.completed || [], "Nothing completed yet"),
    dailyBriefSection("blocked", "Blocked", data.blocked || [], "No blocked work"),
    dailyBriefSection("decisions", "Decisions", data.decisions || [], "No decisions today"),
    dailyBriefSection("next", "Next recommended", data.next_recommended || [], "No recommendations"),
  ].join("");
  host.querySelectorAll("[data-inbox-open]").forEach((node) => {
    node.addEventListener("click", () => { window.location.hash = node.dataset.inboxOpen; });
  });
}

function inboxHint(message, ok) {
  const hint = $("inbox-action-hint");
  if (!hint) return;
  hint.textContent = message;
  hint.classList.toggle("is-ok", !!ok);
  hint.classList.toggle("is-error", !ok);
}

async function markNotificationRead(notificationId) {
  const result = await sendJson("/api/commands", { type: "notification.read", payload: { type: "notification.read", target: notificationId, payload: { actor: "ui" } } });
  inboxHint(result && result.status !== "failed" ? "Marked read (proposal queued)." : `Failed: ${(result.errors || ["error"]).join("; ")}`, result && result.status !== "failed");
}

async function muteNotification(notificationId) {
  const result = await sendJson("/api/commands", { type: "notification.mute", payload: { type: "notification.mute", target: notificationId, payload: { actor: "ui" } } });
  inboxHint(result && result.status !== "failed" ? "Muted (proposal queued)." : `Failed: ${(result.errors || ["error"]).join("; ")}`, result && result.status !== "failed");
}

async function markAllNotificationsRead() {
  const result = await sendJson("/api/commands", { type: "notification.read", payload: { type: "notification.read", payload: { actor: "ui", all: true } } });
  inboxHint(result && result.status !== "failed" ? "Marked all read (proposal queued)." : `Failed: ${(result.errors || ["error"]).join("; ")}`, result && result.status !== "failed");
}

// Parse the owner input box into a runtime command. Slash commands:
//   /meeting <topic> @role @role   -> meeting.start
//   /seminar <topic>               -> seminar.start
//   /mention @target <message>     -> mention.notify (TASK-AR-338)
// A plain message that contains an @mention but no explicit target is routed to
// mention.notify so the mentioned agent/role/Owner receives a runtime message.
// Anything else is a directive (runtime.call_agent) to the @target / channel.
function parseChannelInput(raw, { target, channel } = {}) {
  const text = String(raw || "").trim();
  if (!text) return { error: "Enter a message or slash command." };
  const mentionMatch = text.match(/^\/mention\b\s*(.*)$/i);
  if (mentionMatch) {
    const rest = mentionMatch[1].trim();
    const first = (rest.match(/@[\w.-]+/) || [])[0];
    if (!first) return { error: "Usage: /mention @target <message>" };
    const mentionTarget = first.slice(1);
    const message = rest.replace(first, "").trim();
    if (!message) return { error: "Usage: /mention @target <message>" };
    return {
      command: {
        type: "mention.notify",
        target: mentionTarget,
        payload: { actor: "owner", message, channel: channel || null },
      },
    };
  }
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
  if (!to) {
    // No explicit target: if the message @mentions someone, notify them.
    const mention = (text.match(/@[\w.-]+/) || [])[0];
    if (mention) {
      return {
        command: {
          type: "mention.notify",
          target: mention.slice(1),
          payload: { actor: "owner", message: text, channel: channel || null },
        },
      };
    }
    return { error: "Add a @role target or @mention, or use /meeting, /seminar, /mention." };
  }
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

function eventCardTemplate(event) {
  return patternAuditCard({
    className: `event-card ${auditToneClass(event)}`,
    attrs: `data-entity-id="${escapeHtml(event.id || "")}"`,
    title: event.type || event.event || event.id || "event",
    chip: auditSeverityLabel(event),
    meta: `
        <span><span class="meta-label">Event</span><strong>${escapeHtml(event.type || event.event || "unknown")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>${escapeHtml(auditSeverityLabel(event))}</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(event.actor || event.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(event.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(event.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(event.source_path || event.id || "event stream")}</strong></span>
      `,
    body: event.error || event.message ? `<p>${escapeHtml(event.error || event.message)}</p>` : "",
    code: event.id || event.created_at || event.ts || "",
  });
}

function renderEvents() {
  // Legacy filter-row narrows first, then the shared list toolbar applies filter/sort/group/density.
  const events = filterEvents(runtimeState.events || []).slice(-80).reverse();
  renderGroupedList("events", events, eventCardTemplate, t("empty.no_events"));
}

function renderEvidence() {
  const errors = runtimeState.errors || [];
  const evidence = runtimeState.evidence || [];
  const replay = runtimeState.replay || [];
  $("errors-list").innerHTML = patternEvidencePanel(errors.slice(-40).reverse(), "No recent errors", (item) => patternAuditCard({
    className: "error-card fail",
    title: item.message || item.error || "runtime error",
    chip: "fail",
    meta: `
        <span><span class="meta-label">Event</span><strong>${escapeHtml(item.event_id || item.type || "error")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>fail</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.event_id || "error stream")}</strong></span>
      `,
  }));
  $("evidence-list").innerHTML = patternEvidencePanel(evidence.slice(-60).reverse(), "No evidence links", (item) => patternAuditCard({
    className: "evidence-card pass",
    attrs: `data-entity-id="${escapeHtml(item.id || "")}"`,
    title: item.evidence || item.source_path || "evidence",
    chip: "pass",
    meta: `
        <span><span class="meta-label">Evidence</span><strong>${escapeHtml(item.evidence || "linked")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>pass</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || item.source_type || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.source_id || "evidence index")}</strong></span>
      `,
  }));
  $("replay-list").innerHTML = patternEvidencePanel(replay.slice(-80).reverse(), "No replay records", (item) => patternAuditCard({
    className: `replay-card ${auditToneClass(item, "warn")}`,
    title: item.type || item.kind || "replay",
    chip: auditSeverityLabel(item, "replay"),
    meta: `
        <span><span class="meta-label">Replay</span><strong>${escapeHtml(item.type || item.kind || "record")}</strong></span>
        <span><span class="meta-label">Severity</span><strong>${escapeHtml(auditSeverityLabel(item, "replay"))}</strong></span>
        <span><span class="meta-label">Actor</span><strong>${escapeHtml(item.actor || item.role || "runtime")}</strong></span>
        <span><span class="meta-label">Task</span><strong>${escapeHtml(item.task_id || "no task")}</strong></span>
        <span><span class="meta-label">Goal</span><strong>${escapeHtml(item.goal_id || "no goal")}</strong></span>
        <span><span class="meta-label">Source</span><strong>${escapeHtml(item.source_path || item.source_id || "replay log")}</strong></span>
      `,
    body: item.summary ? `<p>${escapeHtml(item.summary)}</p>` : "",
  }));
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

function appendSvgStatusBadge(group, x, y, signal, classPrefix) {
  // Generated class names include dep-node-status-icon,
  // state-machine-node-status-icon, and live-map-node-status-icon.
  const token = graphSignalToken(signal);
  const badge = document.createElementNS(SVG_NS, "circle");
  badge.setAttribute("cx", x);
  badge.setAttribute("cy", y);
  badge.setAttribute("r", "8");
  badge.setAttribute("class", `${classPrefix}-status-badge signal-${token}`);
  group.appendChild(badge);
  const icon = document.createElementNS(SVG_NS, "text");
  icon.setAttribute("x", x);
  icon.setAttribute("y", y + 1);
  icon.setAttribute("class", `${classPrefix}-status-icon signal-${token}`);
  icon.textContent = graphStatusIconText(token);
  group.appendChild(icon);
}

function liveMapData() {
  return runtimeState.live_map || { nodes: [], edges: [], presence: { counts: {}, online: 0, agents: [] }, totals: {} };
}

function liveMapNodePositions(nodes, edges) {
  return patternSvgForceAgentLayout(nodes, edges, {
    width: 1000,
    height: 600,
    ticks: 72,
    linkDistance: 150,
    repulsion: 1800,
    spring: 0.035,
    damping: 0.72,
  });
}

function appendLiveMapAvatar(group, node, px, py, size) {
  const avatarSeed = String(node.id || node.role || node.label || "live-map-node");
  const role = String(node.role || node.agent_role || (node.kind === "agent" ? node.id : node.kind) || "");
  const label = String(node.label || node.id || "agent");
  const template = document.createElement("template");
  template.innerHTML = patternAgentAvatar(avatarSeed, { role, size, label });
  const avatar = template.content.querySelector("svg");
  if (!avatar) return false;
  avatar.classList.add("live-map-avatar");
  avatar.querySelectorAll("[fill], [stroke]").forEach((part) => {
    const fill = part.getAttribute("fill");
    const stroke = part.getAttribute("stroke");
    if (fill !== null) part.style.fill = fill;
    if (stroke !== null) part.style.stroke = stroke;
  });
  avatar.setAttribute("x", String(px - size / 2));
  avatar.setAttribute("y", String(py - size / 2));
  avatar.setAttribute("width", String(size));
  avatar.setAttribute("height", String(size));
  group.appendChild(document.importNode(avatar, true));
  return true;
}

// Live-map health token mapping (Datadog-style: stroke color = health).
const LIVE_MAP_HEALTH_STROKE = {
  working:    "var(--blue)",
  reviewing:  "var(--amber)",
  in_meeting: "var(--violet)",
  online:     "var(--success)",
  offline:    "var(--line-strong)",
};

// GitHub-Actions-style status icon glyphs for live-map nodes (shape+label, never color only).
// ASCII-only: cp949 node-check guard -- keep all literals in the [0,127] range.
const LIVE_MAP_STATUS_GLYPH = {
  working:    ">",   // > running
  reviewing:  "~",   // ~ reviewing / hourglass
  in_meeting: "@",   // @ in meeting
  online:     "v",   // v online (checkmark equivalent)
  offline:    "o",   // o offline
};

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
      `<li><span class="legend-swatch legend-${escapeHtml(kind)}"></span>${escapeHtml(LIVE_MAP_KIND_LABELS[kind])}</li>`
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
  // Force-directed layout using the d3-force-backed pattern helper when loaded.
  const positions = liveMapNodePositions(nodes, edges);

  // ---- Edge layer: Datadog-style encodings ----
  // stroke-width = magnitude (message_count or weight, clamped 1-6)
  // stroke color = health token (kind -> semantic token)
  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const magnitude = Math.min(6, Math.max(1, edge.weight || edge.message_count || 1));
    const healthColor = LIVE_MAP_HEALTH_STROKE[edge.health || ""] || "var(--line-strong)";
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", String(Math.round(a.x)));
    line.setAttribute("y1", String(Math.round(a.y)));
    line.setAttribute("x2", String(Math.round(b.x)));
    line.setAttribute("y2", String(Math.round(b.y)));
    line.setAttribute("class", `live-map-edge kind-${escapeHtml(edge.kind || "edge")}`);
    line.setAttribute("data-edge-id", String(edge.id));
    // Datadog-style: stroke-width encodes magnitude, color encodes health.
    line.setAttribute("stroke-width", String(magnitude));
    line.setAttribute("stroke", healthColor);
    // aria-label so assistive tech gets the edge info (not color-only).
    line.setAttribute("aria-label", `${escapeHtml(edge.from)} to ${escapeHtml(edge.to)}: ${escapeHtml(edge.kind || "edge")}`);
    edgeLayer.appendChild(line);
    // SPEC-relationship-edge-labels-v1: label block/review edges so a non-expert
    // reads WHY (the blocked reason) instead of a silent red line. Assignment and
    // message edges stay unlabeled (too dense). textContent => no XSS from reason.
    let edgeLabel = "";
    if (edge.kind === "block") {
      edgeLabel = t("livemap.blocked") + (edge.reason_label ? ": " + String(edge.reason_label) : "");
    } else if (edge.kind === "review") {
      edgeLabel = t("livemap.review");
    }
    if (edgeLabel) {
      const text = edgeLabel.slice(0, 28);
      const mx = Math.round((a.x + b.x) / 2);
      const my = Math.round((a.y + b.y) / 2);
      const wEst = Math.round(6.2 * text.length + 8);
      const bg = document.createElementNS(SVG_NS, "rect");
      bg.setAttribute("x", String(mx - wEst / 2)); bg.setAttribute("y", String(my - 9));
      bg.setAttribute("width", String(wEst)); bg.setAttribute("height", "16");
      bg.setAttribute("rx", "3");
      bg.setAttribute("class", "live-map-edge-label-bg");
      bg.setAttribute("aria-hidden", "true");
      edgeLayer.appendChild(bg);
      const lbl = document.createElementNS(SVG_NS, "text");
      lbl.setAttribute("x", String(mx)); lbl.setAttribute("y", String(my + 3));
      lbl.setAttribute("text-anchor", "middle");
      lbl.setAttribute("class", `live-map-edge-label kind-${escapeHtml(edge.kind)}`);
      // The edge line already carries the aria-label; this visible label is
      // decorative for AT to avoid a double announce.
      lbl.setAttribute("aria-hidden", "true");
      lbl.textContent = text;
      edgeLayer.appendChild(lbl);
    }
  });
  svg.appendChild(edgeLayer);

  // ---- Node layer: patternAgentAvatar + GitHub-Actions status icons ----
  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const px = Math.round(pos.x), py = Math.round(pos.y);
    const presenceKey = node.presence || "offline";
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `live-map-node kind-${escapeHtml(node.kind || "node")} presence-${escapeHtml(presenceKey)}`);
    group.setAttribute("data-node-id", String(node.id));

    const r = node.kind === "owner" ? 26 : 18;
    const avatarSize = r * 2;
    appendLiveMapAvatar(group, node, px, py, avatarSize);
    // Accent ring colored by health/presence token.
    const healthStroke = LIVE_MAP_HEALTH_STROKE[presenceKey] || "var(--line-strong)";
    const accentRing = document.createElementNS(SVG_NS, "circle");
    accentRing.setAttribute("cx", String(px)); accentRing.setAttribute("cy", String(py));
    accentRing.setAttribute("r", String(r - 1));
    accentRing.setAttribute("fill", "none");
    accentRing.setAttribute("stroke", healthStroke);
    accentRing.setAttribute("stroke-width", "2");
    group.appendChild(accentRing);

    // Node label text.
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", String(px));
    label.setAttribute("y", String(py + r + 13));
    label.setAttribute("class", "live-map-node-label");
    label.textContent = String(node.label || node.id).slice(0, 18);
    group.appendChild(label);

    // GitHub-Actions-style status icon (shape + glyph, not color-only).
    const glyph = LIVE_MAP_STATUS_GLYPH[presenceKey] || "?";
    const iconBg = document.createElementNS(SVG_NS, "circle");
    iconBg.setAttribute("cx", String(px + r - 6)); iconBg.setAttribute("cy", String(py - r + 6));
    iconBg.setAttribute("r", "8"); iconBg.setAttribute("fill", "var(--canvas)");
    iconBg.setAttribute("stroke", healthStroke); iconBg.setAttribute("stroke-width", "1.5");
    group.appendChild(iconBg);
    const iconText = document.createElementNS(SVG_NS, "text");
    iconText.setAttribute("x", String(px + r - 6)); iconText.setAttribute("y", String(py - r + 10));
    iconText.setAttribute("class", "live-map-status-icon");
    iconText.setAttribute("text-anchor", "middle");
    // aria-label: status is conveyed by glyph + label, not color alone.
    iconText.setAttribute("aria-label", escapeHtml(presenceKey));
    iconText.textContent = glyph;
    group.appendChild(iconText);

    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
}

function pulseLiveElement(selector) {
  // TASK-AR-592: skip non-essential pulse animation under prefers-reduced-motion.
  if (prefersReducedMotion()) return;
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
      pushActivityToast("review", t("toast.presence"), `${role}: ${before[role]} -> ${after[role]}`);
    }
  });
}

function renderMap() {
  renderLiveMap();
  const graph = runtimeState.graph || { nodes: [], edges: [] };
  const machines = runtimeState.state_machines || [];
  const roadmap = runtimeState.roadmap || { milestones: [] };
  // TASK-AR-591: componentEmptyState (via emptyState compat) for graph/state-machine surfaces.
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
  `).join("") : emptyState(t("empty.no_graph_edges"), t("empty.no_graph_edges_hint"));
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
  `).join("") : emptyState(t("empty.no_state_machines"), t("empty.no_state_machines_hint"));
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

// ----- TASK-AR-364: 2D office map -----
// Renders the company floor plan: one room per team function with cute avatar
// sprites and an emoji action glyph above each. All emoji come from the server
// payload (agent.glyph / action_glyphs) so this code stays ASCII-only (cp949
// node-check guard). In-meeting agents are placed in the meeting room by the
// Python derivation; this view just paints what it is given.
function officeMapData() {
  return runtimeState.office_map || {
    world: { cols: 12, rows: 8 },
    rooms: [],
    agents: [],
    action_glyphs: {},
    action_labels: {},
    totals: { agents: 0, actions: {} },
  };
}

function renderOfficeMap() {
  const grid = $("office-map-grid");
  if (!grid) return;
  const data = officeMapData();
  const rooms = data.rooms || [];
  const agents = data.agents || [];
  const totals = data.totals || { agents: 0, actions: {} };

  const actionParts = Object.keys(totals.actions || {}).sort().map((key) => `${key} ${totals.actions[key]}`);
  setText(
    "office-map-summary",
    `${totals.agents || 0} agents - ${actionParts.join(" / ") || "no activity"}`
  );

  // DOM positioning (room cells + agent sprites) is owned by the reusable
  // pattern helper (TASK-AR-592); this view owns summary + legend rendering.
  patternOfficeMapPlacement(grid, rooms, agents);

  const legend = $("office-map-legend");
  if (legend) {
    const glyphs = data.action_glyphs || {};
    const labels = data.action_labels || {};
    legend.innerHTML = Object.keys(glyphs).map((action) =>
      `<li><span class="legend-glyph">${escapeHtml(glyphs[action])}</span>${escapeHtml(labels[action] || action)}</li>`
    ).join("");
  }
}

// ----- Org Chart view (console org-chart): director -> teams -> roles --------
// Renders the static ORG-MODEL hierarchy top-down with the vendored Dagre
// layout (same helper the dependency graph uses). Role nodes carry the v3
// category sprite (patternOfficeSprite) + a tier badge (glyph + word, not color
// alone) + a team color token. Clicking a team or role node drills the Board to
// that team/role via the shared wireTeamDrilldown mechanism (AR-337), so the
// org chart, heatmap and board all agree. Renders with zero live agents.
function orgChartData() {
  return runtimeState.org_chart || { root: null, nodes: [], edges: [], totals: {} };
}

// Tier badge glyph fallback (server also ships tier_badge per node). Shape +
// word, never color alone (a11y: status not by hue).
const ORG_TIER_GLYPH = { director: "*", planner: "^", reviewer: "?", worker: "+", team: "#" };

// Embed a v3 category sprite as a child <svg> of the node group (mirrors the
// live-map avatar embed). Inline fills are promoted to style so dark-theme
// tokens cascade. Falls back to a token-colored disc if the sprite is empty.
function appendOrgSprite(group, node, px, py, size) {
  const role = String(node.id || node.role || "");
  const label = String(node.display_name || node.id || "role");
  let svg = null;
  if (typeof patternOfficeSprite === "function") {
    const template = document.createElement("template");
    template.innerHTML = patternOfficeSprite(role, { assetVersion: "v3", size, label });
    svg = template.content.querySelector("svg");
  }
  if (!svg) {
    const disc = document.createElementNS(SVG_NS, "circle");
    disc.setAttribute("cx", String(px)); disc.setAttribute("cy", String(py));
    disc.setAttribute("r", String(size / 2));
    disc.setAttribute("fill", `var(--${node.color_token || "muted"})`);
    group.appendChild(disc);
    return;
  }
  svg.querySelectorAll("[fill], [stroke]").forEach((part) => {
    const fill = part.getAttribute("fill");
    const stroke = part.getAttribute("stroke");
    if (fill !== null) part.style.fill = fill;
    if (stroke !== null) part.style.stroke = stroke;
  });
  svg.setAttribute("x", String(px - size / 2));
  svg.setAttribute("y", String(py - size / 2));
  svg.setAttribute("width", String(size));
  svg.setAttribute("height", String(size));
  group.appendChild(document.importNode(svg, true));
}

function orgChartNodePositions(nodes, edges) {
  // Owner: the chart was mangled -- 32 role cards crushed into a fixed 1200px width.
  // Size the layout to the widest rank (~190px per card) so cards never overlap;
  // renderOrgChart then sizes the SVG to the real extent and the stage scrolls.
  const list = nodes || [];
  const roleCount = list.filter((n) => n.kind === "role").length;
  const teamCount = list.filter((n) => n.kind === "team").length;
  const widest = Math.max(roleCount, teamCount, 1);
  const width = Math.max(1200, widest * 190 + 160);
  return patternSvgLayeredDagreLayout(nodes, edges, {
    rankdir: "TB",
    width,
    height: 720,
    marginX: 80,
    marginY: 70,
  }).positions;
}

// SPEC-org-chart-cards: build the glanceable team-card grid. Director banner on top;
// each team is a card with its roles grouped beneath it; the grid wraps to fit the
// viewport (so the whole org reads at a glance) with generous spacing. All text is
// escapeHtml'd; drill-down via data-drill-* (wired by wireTeamDrilldown).
function renderOrgChartCards(canvas, data) {
  const nodes = data.nodes || [];
  const director = nodes.filter((n) => n.kind === "director")[0];
  const teams = nodes.filter((n) => n.kind === "team" && (n.role_count || 0) > 0);
  const rolesByTeam = {};
  nodes.filter((n) => n.kind === "role").forEach((r) => {
    const key = String(r.team || "");
    (rolesByTeam[key] = rolesByTeam[key] || []).push(r);
  });
  const dirToken = (director && director.color_token) || "violet";
  const dirBadge = (director && director.tier_badge) || {};
  const dirName = director ? (director.display_name || director.id) : "Director";
  const teamCards = teams.map((team) => {
    const token = team.color_token || "muted";
    const roles = (rolesByTeam[String(team.id)] || []).slice()
      .sort((a, b) => String(a.display_name || a.id).localeCompare(String(b.display_name || b.id)));
    const active = Number(team.active_count || 0);
    const blocked = Number(team.blocked_count || 0);
    const band = String(team.load_band || "idle");
    const loadStr = `${active} ${t("org.load.active")}` + (blocked ? ` \\u00b7 ${blocked} ${t("org.load.blocked")}` : "");
    const roleRows = roles.map((r) => {
      const g = (r.tier_badge && r.tier_badge.glyph) || "-";
      const tier = (r.tier_badge && r.tier_badge.label) || r.tier || "";
      return `<li class="org-role-chip" role="button" tabindex="0"`
        + ` data-role-id="${escapeHtml(r.id)}"`
        + ` aria-label="${escapeHtml(String(r.display_name || r.id) + " - " + String(tier))}"`
        + ` title="${escapeHtml(String(r.display_name || r.id))} - ${escapeHtml(String(tier))}">`
        + `<span class="org-role-glyph" aria-hidden="true">${escapeHtml(g)}</span>`
        + `<span class="org-role-name">${escapeHtml(String(r.display_name || r.id))}</span>`
        + `<span class="org-role-tier">${escapeHtml(String(tier))}</span></li>`;
    }).join("");
    return `<article class="org-team-card tone-${escapeHtml(token)}" role="button" tabindex="0"`
      + ` aria-label="${escapeHtml(String(team.display_name || team.id) + " - " + String((team.role_count || roles.length)) + " roles")}"`
      + ` data-drill-team="${escapeHtml(team.id)}">`
      + `<header class="org-team-card-head">`
      + `<span class="org-team-card-name">${escapeHtml(String(team.display_name || team.id))}</span>`
      + `<span class="org-team-card-meta">${escapeHtml(String((team.role_count || roles.length) + " roles"))}</span>`
      + `</header>`
      + `<div class="org-team-card-load load-band-${escapeHtml(band)}${blocked ? " has-blocked" : ""}">${escapeHtml(loadStr)}</div>`
      + `<ul class="org-team-roles">${roleRows}</ul></article>`;
  }).join("");
  // The human Owner is the apex who directs the agent org -> shown above the
  // director (Owner -> Managing Partner -> teams -> roles).
  canvas.innerHTML =
    `<div class="org-owner-card">`
    + `<span class="org-owner-glyph" aria-hidden="true">\\u2605</span>`
    + `<span class="org-owner-name">${escapeHtml(t("org.owner_label"))}</span>`
    + `<span class="org-owner-sub">${escapeHtml(t("org.owner_sub"))}</span></div>`
    + `<div class="org-hierarchy-link" aria-hidden="true"></div>`
    + `<div class="org-director-card tone-${escapeHtml(dirToken)}">`
    + `<span class="org-director-glyph" aria-hidden="true">${escapeHtml(String(dirBadge.glyph || "*"))}</span>`
    + `<span class="org-director-name">${escapeHtml(String(dirName))}</span>`
    + `<span class="org-director-tier">${escapeHtml(String(dirBadge.label || "Director"))}</span></div>`
    + `<div class="org-hierarchy-link" aria-hidden="true"></div>`
    + `<div class="org-teams-grid">${teamCards}</div>`;
}

// SPEC-org-role-detail: clicking a role opens a panel describing that agent --
// tier + team + responsibilities (from tier) + skills/focus (from team) + a button
// to view its tasks. Descriptions are derived from the real delegation model.
let orgRoleDetailPrevFocus = null;

function openRoleDetail(roleId) {
  const panel = $("org-role-detail");
  if (!panel) return;
  const data = orgChartData();
  const nodes = (data && data.nodes) || [];
  const node = nodes.filter((n) => n.kind === "role" && String(n.id) === String(roleId))[0];
  if (!node) return;
  const team = nodes.filter((n) => n.kind === "team" && String(n.id) === String(node.team))[0];
  const teamName = (team && (team.display_name || team.id)) || node.team || "-";
  const tierBadge = node.tier_badge || {};
  const tierLabel = (tierBadge.glyph ? tierBadge.glyph + " " : "") + String(tierBadge.label || node.tier || "");
  const respKey = "org.resp." + String(node.tier || "");
  const skillKey = "org.skill." + String(node.team || "");
  const respText = i18nStrings[respKey] ? t(respKey) : "";
  const skillText = i18nStrings[skillKey] ? t(skillKey) : "";
  setText("org-role-name", String(node.display_name || node.id));
  const body = $("org-role-body");
  body.innerHTML =
    `<div class="org-role-meta">`
    + `<span class="org-role-tag"><span class="org-role-tag-k">${escapeHtml(t("org.detail.tier"))}</span> ${escapeHtml(tierLabel)}</span>`
    + `<span class="org-role-tag"><span class="org-role-tag-k">${escapeHtml(t("org.detail.team"))}</span> ${escapeHtml(String(teamName))}</span>`
    + `</div>`
    + (respText ? `<section class="org-role-sec"><h4>${escapeHtml(t("org.detail.responsibilities"))}</h4><p>${escapeHtml(respText)}</p></section>` : "")
    + (skillText ? `<section class="org-role-sec"><h4>${escapeHtml(t("org.detail.skills"))}</h4><p>${escapeHtml(skillText)}</p></section>` : "")
    + `<button type="button" class="org-role-drill" data-drill-team="${escapeHtml(node.team || "")}" data-drill-role="${escapeHtml(node.id)}">${escapeHtml(t("org.detail.viewtasks"))}</button>`;
  wireTeamDrilldown(body);
  const drill = body.querySelector(".org-role-drill");
  if (drill) drill.addEventListener("click", closeRoleDetail);
  orgRoleDetailPrevFocus = document.activeElement;
  const backdrop = $("org-role-backdrop");
  if (backdrop) backdrop.hidden = false;
  panel.hidden = false;
  const close = $("org-role-close");
  if (close) close.focus();
}

function closeRoleDetail() {
  const panel = $("org-role-detail");
  const backdrop = $("org-role-backdrop");
  if (panel) panel.hidden = true;
  if (backdrop) backdrop.hidden = true;
  const prev = orgRoleDetailPrevFocus;
  orgRoleDetailPrevFocus = null;
  if (prev && typeof prev.focus === "function") prev.focus();
}

function initOrgRoleDetail() {
  const close = $("org-role-close");
  if (close) close.addEventListener("click", closeRoleDetail);
  const backdrop = $("org-role-backdrop");
  if (backdrop) backdrop.addEventListener("click", closeRoleDetail);
  document.addEventListener("keydown", (event) => {
    const panel = $("org-role-detail");
    if (event.key === "Escape" && panel && !panel.hidden) { event.preventDefault(); closeRoleDetail(); }
  });
}

function renderOrgChart() {
  const svg = $("org-chart-svg");
  if (!svg) return;
  const data = orgChartData();
  const totals = data.totals || {};
  const load = data.load_summary || {};
  setText(
    "org-chart-summary",
    `${totals.teams || 0} teams - ${totals.roles || 0} roles`
    + (totals.nodes ? ` - ${totals.nodes} nodes` : "")
    + `  \\u00b7  ${load.active || 0} ${t("org.load.active")} \\u00b7 ${load.blocked || 0} ${t("org.load.blocked")}`
  );

  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const nodes = data.nodes || [];
  const edges = data.edges || [];
  if (!nodes.length || !data.root) {
    const note = document.createElementNS(SVG_NS, "text");
    note.setAttribute("x", "600"); note.setAttribute("y", "360");
    note.setAttribute("class", "org-chart-empty");
    note.setAttribute("text-anchor", "middle");
    note.textContent = "No org model";
    svg.appendChild(note);
    return;
  }

  // SPEC-org-chart-cards: a glanceable, spacious team-card grid (roles grouped under
  // their team) that wraps to fit the viewport -- replaces the wide flat SVG tree
  // that crushed 32 roles into one row. The SVG path below is kept as a fallback.
  const canvas = $("org-chart-canvas");
  if (canvas) {
    svg.setAttribute("hidden", "hidden");
    renderOrgChartCards(canvas, data);
    wireTeamDrilldown(canvas);
    // Clicking a role opens its detail panel (description), not a board drill.
    canvas.querySelectorAll(".org-role-chip").forEach((chip) => {
      const open = () => openRoleDetail(chip.getAttribute("data-role-id"));
      chip.addEventListener("click", open);
      chip.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); open(); }
      });
    });
    const legendEl = $("org-chart-legend");
    if (legendEl) {
      const tb = data.tier_badges || {};
      legendEl.innerHTML = ["director", "planner", "reviewer", "worker"].filter((tr) => tb[tr])
        .map((tr) => `<li><span class="legend-glyph">${escapeHtml(tb[tr].glyph)}</span>${escapeHtml(tb[tr].label)}</li>`).join("");
    }
    return;
  }

  const positions = orgChartNodePositions(nodes, edges);

  // Size the SVG to the real layout extent so cards render full-size (no squish);
  // the stage scrolls horizontally for large orgs. viewBox == element size = 1:1.
  let maxX = 1200, maxY = 560;
  Object.keys(positions).forEach((id) => {
    const p = positions[id];
    if (p) { maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); }
  });
  const W = Math.round(maxX + 140);
  const H = Math.round(maxY + 90);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.style.width = W + "px";
  svg.style.height = H + "px";

  // ---- Edge layer: director -> team -> role connectors ----
  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const midY = (a.y + b.y) / 2;
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", `M ${a.x} ${a.y} L ${a.x} ${midY} L ${b.x} ${midY} L ${b.x} ${b.y}`);
    path.setAttribute("class", "org-chart-edge");
    path.setAttribute("fill", "none");
    edgeLayer.appendChild(path);
  });
  svg.appendChild(edgeLayer);

  // ---- Node layer ----
  const reduced = prefersReducedMotion();
  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const px = Math.round(pos.x), py = Math.round(pos.y);
    const kind = String(node.kind || "node");
    const token = node.color_token || "muted";
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `org-chart-node kind-${escapeHtml(kind)}${reduced ? "" : " is-animated"}`);
    group.setAttribute("data-node-id", String(node.id));
    group.setAttribute("data-entity-id", String(node.id));
    // Drill-down wiring (AR-337): role -> team+role, team -> team. Director is
    // org-wide (no filter). The shared wireTeamDrilldown reads these.
    if (kind === "role") {
      group.setAttribute("data-drill-team", String(node.team || ""));
      group.setAttribute("data-drill-role", String(node.id));
    } else if (kind === "team") {
      group.setAttribute("data-drill-team", String(node.id));
    }
    const tierBadge = node.tier_badge || {};
    const tierWord = String(tierBadge.label || node.tier || kind);
    const a11y = `${node.display_name || node.id} - ${tierWord}`
      + (node.team ? ` - ${node.team}` : "")
      + (node.online_count ? ` - ${node.online_count} online` : "");
    group.setAttribute("role", (kind === "director") ? "img" : "button");
    group.setAttribute("tabindex", (kind === "director") ? "-1" : "0");
    group.setAttribute("aria-label", escapeHtml(a11y));

    const isRole = kind === "role";
    const isTeam = kind === "team";
    const w = isRole ? 168 : 200;
    // Team cards are taller to fit a third "load" line (SPEC-org-chart-load-v1).
    const h = isRole ? 58 : (isTeam ? 64 : 46);
    const rect = document.createElementNS(SVG_NS, "rect");
    rect.setAttribute("x", String(px - w / 2)); rect.setAttribute("y", String(py - h / 2));
    rect.setAttribute("width", String(w)); rect.setAttribute("height", String(h));
    rect.setAttribute("rx", "8");
    rect.setAttribute("class", "org-chart-card");
    rect.setAttribute("stroke", `var(--${token})`);
    // Team color token as a soft fill band (token-driven; no raw color).
    rect.setAttribute("fill", `var(--${token}-soft, var(--panel-strong))`);
    group.appendChild(rect);

    if (isRole) {
      // v3 category sprite on the left of the card.
      appendOrgSprite(group, node, px - w / 2 + 22, py, 34);
      // Role name.
      const name = document.createElementNS(SVG_NS, "text");
      name.setAttribute("x", String(px - w / 2 + 46)); name.setAttribute("y", String(py - 4));
      name.setAttribute("class", "org-chart-role-name");
      name.textContent = String(node.display_name || node.id).slice(0, 22);
      group.appendChild(name);
      // Tier badge: glyph + word (shape + text, not color-only).
      const badge = document.createElementNS(SVG_NS, "text");
      badge.setAttribute("x", String(px - w / 2 + 46)); badge.setAttribute("y", String(py + 13));
      badge.setAttribute("class", "org-chart-tier-badge");
      const glyph = String(tierBadge.glyph || ORG_TIER_GLYPH[node.tier] || "-");
      const liveStr = node.online_count ? ` - ${node.online_count} on` : "";
      badge.textContent = `${glyph} ${tierWord}${liveStr}`;
      group.appendChild(badge);
    } else {
      // Director / team group node: centered name + role count (+ load for teams).
      const nameY = isTeam ? py - 14 : py - 2;
      const subY = isTeam ? py - 1 : py + 13;
      const name = document.createElementNS(SVG_NS, "text");
      name.setAttribute("x", String(px)); name.setAttribute("y", String(nameY));
      name.setAttribute("class", `org-chart-group-name kind-${escapeHtml(kind)}`);
      name.setAttribute("text-anchor", "middle");
      const glyph = String((node.tier_badge || {}).glyph || ORG_TIER_GLYPH[kind] || "");
      name.textContent = `${glyph ? glyph + " " : ""}${String(node.display_name || node.id).slice(0, 24)}`;
      group.appendChild(name);
      const sub = document.createElementNS(SVG_NS, "text");
      sub.setAttribute("x", String(px)); sub.setAttribute("y", String(subY));
      sub.setAttribute("class", "org-chart-group-sub");
      sub.setAttribute("text-anchor", "middle");
      sub.textContent = isTeam
        ? `${node.role_count || 0} roles${node.online_count ? ` - ${node.online_count} online` : ""}`
        : "Director";
      group.appendChild(sub);
      if (isTeam) {
        // Load line: open-task workload band (color) + blocked count, always with
        // a text label (never color-only). Lets a non-expert see who's busy/blocked.
        const active = Number(node.active_count || 0);
        const blocked = Number(node.blocked_count || 0);
        const band = String(node.load_band || "idle");
        const load = document.createElementNS(SVG_NS, "text");
        load.setAttribute("x", String(px)); load.setAttribute("y", String(py + 17));
        load.setAttribute("text-anchor", "middle");
        load.setAttribute("class", `org-team-load load-band-${escapeHtml(band)}${blocked ? " has-blocked" : ""}`);
        load.textContent = `${active} ${t("org.load.active")}`
          + (blocked ? `  \\u00b7  ${blocked} ${t("org.load.blocked")}` : "");
        group.appendChild(load);
      }
    }
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);

  // Keyboard activation for the drillable nodes (mirrors the click handler).
  nodeLayer.querySelectorAll("[data-drill-team], [data-drill-role]").forEach((el) => {
    el.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        el.dispatchEvent(new MouseEvent("click", { bubbles: true }));
      }
    });
  });
  // Reuse the shared drill-down wiring (AR-337) so board/heatmap/org agree.
  wireTeamDrilldown(svg);

  // Legend: tier badges + team color meaning.
  const legend = $("org-chart-legend");
  if (legend) {
    const badges = data.tier_badges || {};
    const order = ["director", "planner", "reviewer", "worker"];
    legend.innerHTML = order
      .filter((tier) => badges[tier])
      .map((tier) =>
        `<li><span class="legend-glyph">${escapeHtml(badges[tier].glyph)}</span>${escapeHtml(badges[tier].label)}</li>`
      ).join("");
  }
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

function stateMachineNodePositions(nodes, edges) {
  return patternSvgLayeredDagreLayout(nodes, edges, {
    rankdir: "LR",
    width: 1000,
    height: 600,
    marginX: 130,
    marginY: 100,
  }).positions;
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
    legend.innerHTML = patternStateMachinePanelLegend();
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

  const layoutEdges = edges.map((edge) => {
    let fromId = edge.from;
    if (edge.wildcard) {
      const hub = currentState && currentState !== edge.to ? currentState : (edge.wildcard_sources || [])[0];
      fromId = hub || edge.from;
    }
    return { ...edge, from: fromId };
  });
  const layout = patternSvgLayeredDagreLayout(nodes, layoutEdges, {
    rankdir: "LR",
    width: 1000,
    height: 600,
    marginX: 130,
    marginY: 100,
  });
  const positions = layout.positions;

  const edgeLayer = document.createElementNS(SVG_NS, "g");
  layoutEdges.forEach((layoutEdge, index) => {
    const edge = edges[index] || layoutEdge;
    const a = positions[layoutEdge.from];
    const b = positions[layoutEdge.to];
    if (!a || !b) return;
    const traversed = traversedEdgeIds.has(edge.id);
    const route = layout.edgeRoutes[graphEdgeKey(layoutEdge, index)] || [{ x: a.x, y: a.y }, { x: b.x, y: b.y }];
    const path = document.createElementNS(SVG_NS, "path");
    path.setAttribute("d", svgLayeredEdgePath(route));
    path.setAttribute(
      "class",
      `state-machine-edge magnitude-${graphEdgeMagnitudeBucket(edge)} health-${graphEdgeHealth(edge, traversed ? "pass" : "watch")} ${edge.wildcard ? "is-wildcard" : ""} ${traversed ? "is-traversed" : ""}`
    );
    path.setAttribute("data-edge-id", edge.id);
    path.setAttribute("aria-label", `transition ${escapeHtml(layoutEdge.from)} to ${escapeHtml(layoutEdge.to)}${edge.trigger ? ": " + escapeHtml(edge.trigger) : ""}`);
    edgeLayer.appendChild(path);
    if (edge.trigger) {
      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", String(Math.round((a.x + b.x) / 2)));
      label.setAttribute("y", String(Math.round((a.y + b.y) / 2) - 4));
      label.setAttribute("class", "state-machine-edge-label");
      label.textContent = String(edge.trigger).slice(0, 22);
      edgeLayer.appendChild(label);
    }
  });
  svg.appendChild(edgeLayer);

  // ---- Node layer: GitHub-Actions-style status icons ----
  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const px = Math.round(pos.x), py = Math.round(pos.y);
    const isCurrent = node.id === currentState;
    const isTraversed = traversedStates.has(node.id);
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute(
      "class",
      `state-machine-node signal-${escapeHtml(node.signal_token || "subtle")} ${node.is_initial ? "is-initial" : ""} ${isCurrent ? "is-current" : ""} ${isTraversed ? "is-traversed" : ""}`
    );
    group.setAttribute("data-state-id", String(node.id));
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", String(px));
    circle.setAttribute("cy", String(py));
    circle.setAttribute("r", "26");
    group.appendChild(circle);
    appendSvgStatusBadge(group, pos.x + 21, pos.y - 21, isCurrent ? "info" : graphNodeSignal(node, "watch"), "state-machine-node");
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", String(px));
    label.setAttribute("y", String(py + 2));
    label.textContent = String(node.id).slice(0, 14);
    group.appendChild(label);
    if (node.score !== null && node.score !== undefined) {
      const score = document.createElementNS(SVG_NS, "text");
      score.setAttribute("x", String(px));
      score.setAttribute("y", String(py + 42));
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

function dependencyGraphFocusTasksetId() {
  const taskSets = (runtimeState && runtimeState.task_sets) || [];
  const active = taskSets.find((taskSet) => taskSet.active || taskSet.status === "active")
    || taskSets.find((taskSet) => taskSet.id === ((runtimeState && runtimeState.active_taskset_id) || ""));
  return active ? String(active.id || "") : "";
}

function dependencyGraphVisibleData(data) {
  const nodes = data.nodes || [];
  const edges = data.edges || [];
  const focusTasksetId = dependencyGraphFocusTasksetId();
  if (focusTasksetId) {
    const focusedIds = new Set([focusTasksetId]);
    nodes.forEach((node) => {
      if (String(node.task_set_id || "") === focusTasksetId) focusedIds.add(String(node.id));
    });
    const focusedNodes = nodes.filter((node) => focusedIds.has(String(node.id)));
    const focusedEdges = edges.filter((edge) => focusedIds.has(String(edge.from)) && focusedIds.has(String(edge.to)));
    if (focusedNodes.length > 1) {
      return {
        nodes: focusedNodes,
        edges: focusedEdges,
        capped: focusedNodes.length < nodes.length,
        reason: "active",
      };
    }
  }
  const linked = new Set();
  edges.forEach((edge) => {
    if (edge.from) linked.add(String(edge.from));
    if (edge.to) linked.add(String(edge.to));
  });
  (data.cycles || []).forEach((cycle) => (cycle || []).forEach((node) => linked.add(String(node))));
  if (!linked.size) return { nodes, edges, capped: false };
  const visibleNodes = nodes.filter((node) => linked.has(String(node.id)));
  const visibleIds = new Set(visibleNodes.map((node) => String(node.id)));
  const visibleEdges = edges.filter((edge) => visibleIds.has(String(edge.from)) && visibleIds.has(String(edge.to)));
  return {
    nodes: visibleNodes,
    edges: visibleEdges,
    capped: visibleNodes.length < nodes.length,
    reason: "linked",
  };
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

function dependencyNodePositions(nodes, edges) {
  return patternSvgLayeredDagreLayout(nodes, edges, {
    rankdir: "TB",
    width: 1000,
    height: 600,
    marginX: 90,
    marginY: 80,
  }).positions;
}

// Dependency graph health token mapping (Datadog-style: edge color = health).
const DEP_HEALTH_STROKE = {
  healthy:  "var(--success)",
  warning:  "var(--warning)",
  degraded: "var(--amber)",
  error:    "var(--danger)",
  cycle:    "var(--danger)",
};
// GitHub-Actions-style status glyphs for dep-graph nodes (shape + glyph, not color-only).
const DEP_STATUS_GLYPH = {
  completed:   "v",
  in_progress: ">",
  blocked:     "x",
  planned:     "o",
  parent:      "*",
  missing:     "?",
};

function renderDependencyGraph() {
  const data = dependencyGraphData();
  const totals = data.totals || {};
  const visible = dependencyGraphVisibleData(data);
  setText("dep-graph-summary",
    `${totals.nodes || 0} nodes - ${totals.dependency_edges || 0} deps - ${totals.parent_edges || 0} subtasks`
    + (visible.capped ? ` - showing ${visible.nodes.length} ${visible.reason || "linked"}` : "")
    + (data.has_cycle ? ` - ${(data.cycles || []).length} cycle(s)` : ""));
  renderCycleWarning("dep-cycle-warning", data.cycles);

  const legend = $("dep-graph-legend");
  if (legend) {
    legend.innerHTML = ["dependency", "parent", "cycle"].map((kind) =>
      `<li><span class="legend-swatch legend-${escapeHtml(kind)}"></span>${escapeHtml(DEP_KIND_LABELS[kind] || kind)}</li>`).join("");
  }

  const svg = $("dep-graph-svg");
  if (!svg) return;
  const nodes = visible.nodes || [];
  const edges = visible.edges || [];
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
  // Layered DAG layout using the Dagre-backed pattern helper when loaded.
  const positions = dependencyNodePositions(nodes, edges);

  // ---- Edge layer: Datadog-style encodings ----
  // stroke-width = magnitude (dependency_count or weight, clamped 1-5)
  // stroke color = health token
  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const magnitude = Math.min(5, Math.max(1, edge.weight || edge.dependency_count || 1));
    const healthKey = edge.in_cycle ? "cycle" : (edge.health || "");
    const healthColor = DEP_HEALTH_STROKE[healthKey] || "var(--line-strong)";
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", String(Math.round(a.x)));
    line.setAttribute("y1", String(Math.round(a.y)));
    line.setAttribute("x2", String(Math.round(b.x)));
    line.setAttribute("y2", String(Math.round(b.y)));
    line.setAttribute(
      "class",
      `dep-edge kind-${escapeHtml(edge.kind || "dependency")} magnitude-${graphEdgeMagnitudeBucket(edge)} health-${graphEdgeHealth(edge, edge.kind === "dependency" ? "watch" : "info")} ${edge.in_cycle ? "is-cycle" : ""}`
    );
    line.setAttribute("data-edge-id", String(edge.id));
    // Datadog-style: stroke-width = magnitude; stroke color = health.
    line.setAttribute("stroke-width", String(magnitude));
    line.setAttribute("stroke", healthColor);
    line.setAttribute("aria-label", `${escapeHtml(edge.from)} to ${escapeHtml(edge.to)}: ${escapeHtml(edge.kind || "dependency")}`);
    edgeLayer.appendChild(line);
  });
  svg.appendChild(edgeLayer);

  // ---- Node layer: GitHub-Actions-style status icons ----
  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const px = Math.round(pos.x), py = Math.round(pos.y);
    const r = node.kind === "parent" ? 20 : 14;
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `dep-node kind-${escapeHtml(node.kind || "task")} ${node.in_cycle ? "is-cycle" : ""}`);
    group.setAttribute("data-node-id", String(node.id));
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", String(px));
    circle.setAttribute("cy", String(py));
    circle.setAttribute("r", String(r));
    group.appendChild(circle);
    const label = document.createElementNS(SVG_NS, "text");
    label.setAttribute("x", String(px));
    label.setAttribute("y", String(py + r + 14));
    label.textContent = String(node.id).slice(0, 18);
    group.appendChild(label);
    appendSvgStatusBadge(group, px + r - 4, py - r + 4, node.in_cycle ? "block" : graphNodeSignal(node, node.status_bucket || "watch"), "dep-node");
    nodeLayer.appendChild(group);
  });
  svg.appendChild(nodeLayer);
}

// ----- Knowledge graph view (#5): on-demand, degree-ranked bounded subgraph -----
let knowledgeGraphState = { nodes: [], edges: [], totals: {}, error: null };
let knowledgeGraphFocus = null;
let knowledgeGraphLoading = false;
let knowledgeGraphSearch = "";
let knowledgeGraphHiddenKinds = new Set();
let knowledgeGraphControlsBound = false;

const KG_KIND_COLORS = {
  task: "var(--primary-line)", taskset: "var(--blue)", initiative: "var(--warning-line)",
  review: "var(--panel)", claim: "var(--subtle)", commit: "var(--canvas)",
};

async function loadKnowledgeGraph() {
  if (knowledgeGraphLoading) return;
  knowledgeGraphLoading = true;
  setText("kg-graph-summary", "Loading entities...");
  // TASK-AR-591: componentLoadingState for the knowledge-graph loading surface.
  setHtml("kg-graph-state-host", loadingState("Loading knowledge graph..."));
  try {
    const response = await fetch("/api/knowledge-graph", { cache: "no-store" });
    knowledgeGraphState = await response.json();
  } catch (error) {
    knowledgeGraphState = { nodes: [], edges: [], totals: {}, error: String(error) };
  } finally {
    knowledgeGraphLoading = false;
  }
  // Deep-link: a shared #/records/knowledge-graph?select=<id> focuses that node on load.
  knowledgeGraphFocus = parseHash().select || null;
  bindKnowledgeGraphControls();
  renderKnowledgeGraph();
}

function bindKnowledgeGraphControls() {
  if (knowledgeGraphControlsBound) return;
  const input = $("kg-search");
  if (!input) return;
  input.addEventListener("input", () => {
    knowledgeGraphSearch = input.value.trim().toLowerCase();
    renderKnowledgeGraph();
  });
  knowledgeGraphControlsBound = true;
}

function knowledgeGraphVisibleNodes() {
  const query = knowledgeGraphSearch;
  return (knowledgeGraphState.nodes || []).filter((node) =>
    !knowledgeGraphHiddenKinds.has(node.kind)
    && (!query
      || String(node.id).toLowerCase().includes(query)
      || String(node.label || "").toLowerCase().includes(query)));
}

function renderKnowledgeGraphFilters() {
  const host = $("kg-filters");
  if (!host) return;
  const kinds = Array.from(new Set((knowledgeGraphState.nodes || []).map((n) => n.kind))).sort();
  host.innerHTML = "";
  kinds.forEach((kind) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "kg-filter-chip";
    chip.setAttribute("aria-pressed", knowledgeGraphHiddenKinds.has(kind) ? "false" : "true");
    chip.innerHTML = `<span class="kg-chip-dot" style="background:${KG_KIND_COLORS[kind] || "var(--panel)"}"></span>${escapeHtml(kind)}`;
    chip.addEventListener("click", () => {
      if (knowledgeGraphHiddenKinds.has(kind)) knowledgeGraphHiddenKinds.delete(kind);
      else knowledgeGraphHiddenKinds.add(kind);
      renderKnowledgeGraph();
    });
    host.appendChild(chip);
  });
}

function updateKnowledgeGraphHash() {
  if (!(window.history && history.replaceState)) return;
  const base = "#/records/knowledge-graph";
  const hash = knowledgeGraphFocus ? `${base}?select=${encodeURIComponent(knowledgeGraphFocus)}` : base;
  try { history.replaceState(null, "", hash); } catch (error) { /* ignore */ }
}

function knowledgeGraphNodePositions(nodes) {
  // Cluster nodes by kind around a big ring; within each cluster, a small ring.
  // Deterministic so the layout reads the same across refreshes.
  const positions = {};
  const cx = 500, cy = 300;
  const byKind = {};
  nodes.forEach((node) => { (byKind[node.kind] || (byKind[node.kind] = [])).push(node); });
  const kinds = Object.keys(byKind).sort();
  kinds.forEach((kind, ki) => {
    const cluster = byKind[kind];
    const clusterAngle = (ki / Math.max(kinds.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const clusterX = cx + Math.cos(clusterAngle) * 300;
    const clusterY = cy + Math.sin(clusterAngle) * 210;
    const radius = Math.min(140, 18 + cluster.length * 7);
    cluster.forEach((node, ni) => {
      if (cluster.length === 1) { positions[node.id] = { x: clusterX, y: clusterY }; return; }
      const a = (ni / cluster.length) * Math.PI * 2;
      positions[node.id] = { x: clusterX + Math.cos(a) * radius, y: clusterY + Math.sin(a) * radius };
    });
  });
  return positions;
}

function renderKnowledgeGraph() {
  const data = knowledgeGraphState || { nodes: [], edges: [], totals: {} };
  const totals = data.totals || {};
  renderKnowledgeGraphFilters();

  const nodes = knowledgeGraphVisibleNodes();
  const visibleIds = new Set(nodes.map((n) => n.id));
  const edges = (data.edges || []).filter((edge) => visibleIds.has(edge.from) && visibleIds.has(edge.to));
  const isFiltered = Boolean(knowledgeGraphSearch) || knowledgeGraphHiddenKinds.size > 0;

  const summary = data.error
    ? `Unavailable: ${data.error}`
    : `${nodes.length}${isFiltered ? " shown / " + (totals.shown || (data.nodes || []).length) : ""} of ${totals.nodes || 0} entities`
      + ` · ${edges.length} edges`
      + (totals.capped ? " · most-connected" : "")
      + (knowledgeGraphFocus ? ` · focus: ${knowledgeGraphFocus}` : "");
  setText("kg-graph-summary", summary);

  const legend = $("kg-graph-legend");
  if (legend) {
    const kinds = Array.from(new Set(nodes.map((n) => n.kind))).sort();
    legend.innerHTML = kinds.map((kind) =>
      `<li><span class="legend-swatch" style="background:${KG_KIND_COLORS[kind] || "var(--panel)"}"></span>${escapeHtml(kind)}</li>`).join("");
  }

  const svg = $("kg-graph-svg");
  if (!svg) return;
  while (svg.firstChild) svg.removeChild(svg.firstChild);
  if (!nodes.length) {
    // TASK-AR-591: componentErrorState / componentEmptyState for knowledge-graph surface.
    const stateHost = $("kg-graph-state-host");
    if (stateHost) {
      if (data.error) {
        stateHost.innerHTML = errorState(t("error.knowledge_graph_unavailable"), data.error);
      } else if (isFiltered) {
        stateHost.innerHTML = emptyState(t("empty.no_entities_match_filter"), t("empty.no_entities_match_filter_hint"));
      } else {
        stateHost.innerHTML = emptyState(t("empty.no_knowledge_graph_data"), t("empty.no_knowledge_graph_data_hint"));
      }
    } else {
      const note = document.createElementNS(SVG_NS, "text");
      note.setAttribute("x", "500");
      note.setAttribute("y", "300");
      note.setAttribute("class", "kg-graph-empty");
      note.setAttribute("text-anchor", "middle");
      note.textContent = data.error ? "Knowledge graph unavailable" : (isFiltered ? "No entities match the filter" : "No knowledge graph data");
      svg.appendChild(note);
    }
    return;
  }
  // Clear loading/error state once data is available.
  const stateHostClear = $("kg-graph-state-host");
  if (stateHostClear) stateHostClear.innerHTML = "";
  const positions = knowledgeGraphNodePositions(nodes);
  const focusAdjacent = new Set();
  if (knowledgeGraphFocus) {
    edges.forEach((edge) => {
      if (edge.from === knowledgeGraphFocus) focusAdjacent.add(edge.to);
      if (edge.to === knowledgeGraphFocus) focusAdjacent.add(edge.from);
    });
  }

  const edgeLayer = document.createElementNS(SVG_NS, "g");
  edges.forEach((edge) => {
    const a = positions[edge.from];
    const b = positions[edge.to];
    if (!a || !b) return;
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
    line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
    line.setAttribute("class", `kg-edge type-${edge.type || "relates"}`);
    if (knowledgeGraphFocus) {
      const touches = edge.from === knowledgeGraphFocus || edge.to === knowledgeGraphFocus;
      line.style.opacity = touches ? "0.95" : "0.08";
    }
    edgeLayer.appendChild(line);
  });
  svg.appendChild(edgeLayer);

  const nodeLayer = document.createElementNS(SVG_NS, "g");
  nodes.forEach((node) => {
    const pos = positions[node.id];
    if (!pos) return;
    const isFocus = node.id === knowledgeGraphFocus;
    const dim = knowledgeGraphFocus && !isFocus && !focusAdjacent.has(node.id);
    const group = document.createElementNS(SVG_NS, "g");
    group.setAttribute("class", `kg-node kind-${node.kind || "entity"} ${isFocus ? "is-focus" : ""}`);
    group.setAttribute("data-entity-id", node.id);
    // TASK-AR-592: keyboard operable - role=button + tabindex so keyboard users can
    // focus nodes; Enter/Space toggles focus just as a click does.
    group.setAttribute("role", "button");
    group.setAttribute("tabindex", "0");
    group.setAttribute("aria-label", `${node.id} (${node.kind || "entity"}), ${node.degree || 0} links${isFocus ? ", focused" : ""}`);
    group.setAttribute("aria-pressed", isFocus ? "true" : "false");
    if (dim) group.style.opacity = "0.18";
    const circle = document.createElementNS(SVG_NS, "circle");
    circle.setAttribute("cx", pos.x); circle.setAttribute("cy", pos.y);
    circle.setAttribute("r", String(Math.min(22, 6 + Math.sqrt(node.degree || 1) * 2)));
    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = `${node.id} (${node.kind}) · ${node.degree} links\n${node.label || ""}`;
    circle.appendChild(title);
    group.appendChild(circle);
    if ((node.degree || 0) >= 6 || isFocus) {
      const label = document.createElementNS(SVG_NS, "text");
      label.setAttribute("x", pos.x); label.setAttribute("y", pos.y - 12);
      label.textContent = String(node.id).slice(0, 16);
      group.appendChild(label);
    }
    var kgNodeAction = function() {
      knowledgeGraphFocus = knowledgeGraphFocus === node.id ? null : node.id;
      updateKnowledgeGraphHash();
      renderKnowledgeGraph();
    };
    group.addEventListener("click", kgNodeAction);
    group.addEventListener("keydown", function(event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        kgNodeAction();
      }
    });
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
  host.innerHTML = patternCommandBar(rows);
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

// Calendar anchor/mode -> visible day matrix + period label. The reusable
// orchestration lives in patternCalendarState (TASK-AR-592); this view owns the
// mutable anchor/mode module state and re-render side effects.
function calendarVisibleDays() {
  return patternCalendarState(calendarAnchorDate(), calendarMode, { months: CALENDAR_MONTHS }).days;
}

function calendarPeriodLabel() {
  return patternCalendarState(calendarAnchorDate(), calendarMode, { months: CALENDAR_MONTHS }).periodLabel;
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
  grid.innerHTML = patternCalendarGrid(days, byDate, {
    weekdays: CALENDAR_WEEKDAYS,
    todayKey,
    dateKey: calendarDateKey,
  });
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

function renderNotificationRouting() {
  const host = $("subscription-list");
  if (!host) return;
  const data = (runtimeState && runtimeState.notification_routing) || { channels: [], totals: {} };
  const totals = data.totals || {};
  const status = $("routing-status");
  if (status) {
    const dormant = data.dormant !== false;
    status.innerHTML = `Routing is <strong>${dormant ? "dormant" : "active"}</strong>`
      + ` &middot; channels <strong>${escapeHtml(totals.channels || 0)}</strong>`
      + ` &middot; enabled <strong>${escapeHtml(totals.enabled || 0)}</strong>`
      + ` &middot; secrets configured <strong>${escapeHtml(totals.configured || 0)}</strong>`
      + ` &middot; secrets stay in the local config (never served)`;
  }
  const summary = $("subscription-summary");
  if (summary) {
    summary.innerHTML = `Config ${data.config_present ? "present" : "absent"} at <strong>${escapeHtml(data.source_path || "local config")}</strong>`
      + ` &middot; template <strong>${escapeHtml(data.example_path || "")}</strong>`
      + ` &middot; proposal-only CRUD (dispatch is an opt-in local runner)`;
  }
  const channels = data.channels || [];
  host.innerHTML = channels.length ? channels.map((channel) => {
    const stateClass = channel.enabled ? (channel.configured ? "is-active" : "is-inactive") : "is-inactive";
    const stateLabel = channel.enabled ? (channel.configured ? "enabled" : "enabled (no secret)") : "disabled";
    const severities = (channel.severities || []).map((sev) =>
      `<span class="routing-token routing-token-${escapeHtml(sev)}">${escapeHtml(sev)}</span>`).join("");
    return `
    <article class="config-card">
      <div class="config-card-header">
        <b>${escapeHtml(channel.name)}</b>
        <span class="rule-state ${stateClass}">${escapeHtml(stateLabel)}</span>
      </div>
      <div class="rule-flow">
        <span class="rule-token">${escapeHtml(channel.kind)}</span>
        <span class="rule-flow-arrow" aria-hidden="true">&#8594;</span>
        ${severities}
      </div>
      <div class="config-card-meta">
        <span>Secret <strong>${escapeHtml(channel.configured ? "configured (hidden)" : "not set")}</strong></span>
        <span>Window <strong>${escapeHtml(channel.aggregate_minutes || 5)} min</strong></span>
      </div>
      <div class="config-card-actions">
        <button class="config-action" type="button" onclick="toggleSubscription('${escapeHtml(channel.name)}', ${channel.enabled ? "false" : "true"})">${channel.enabled ? "Disable" : "Enable"}</button>
        <button class="config-action" type="button" onclick="deleteSubscription('${escapeHtml(channel.name)}')">Delete</button>
      </div>
    </article>`;
  }).join("") : `<div class="empty">No notification channels &mdash; routing is dormant. Author the local config from the example template.</div>`;
}

function toggleSubscription(channel, enabled) {
  return sendJson("/api/commands", { type: "subscription.toggle", payload: { type: "subscription.toggle", target: channel, payload: { actor: "ui", enabled } } });
}

function deleteSubscription(channel) {
  return sendJson("/api/commands", { type: "subscription.delete", payload: { type: "subscription.delete", target: channel, payload: { actor: "ui" } } });
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
  // Streak is derived from the AR-324 computed lifetime values; it is only
  // visible under the gamify policy (CSS-gated) so calm mode stays clean.
  const streak = Number((card.lifetime || {}).streak ?? card.streak ?? 0);
  const streakMarkup = streak > 0
    ? `<span class="agent-character-streak" title="Completion streak">&#9650; ${escapeHtml(streak)} streak</span>`
    : "";
  return `<div class="agent-character-level"><span>Lv <strong>${escapeHtml(card.level ?? 1)}</strong></span><span>${escapeHtml(card.xp ?? 0)} XP (${escapeHtml(card.xp_for_next ?? 0)} to next)</span>${streakMarkup}</div>
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
  // TASK-AR-591: patternAgentAvatar replaces the placeholder text avatar in the
  // team/agents-identity surface. seed = card.id for deterministic per-agent art.
  const teamAvatarSeed = card.id || card.role || "agent";
  const teamAvatarLabel = card.callsign || card.display_name || card.role || "agent";
  const teamAvatar = patternAgentAvatar(teamAvatarSeed, { role: card.role || "", size: 36, label: teamAvatarLabel });
  return `
    <article class="agent-character-card presence-${escapeHtml(presence)}" data-agent-id="${escapeHtml(card.id)}">
      <header class="agent-character-header">
        <span class="agent-character-avatar">${teamAvatar}<span class="presence-ring" title="${escapeHtml(presence)}"></span></span>
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

// ----- TASK-AR-363: growth system (project Lv / business stage / XP) -----
// Computed-only from outcomes; token spend is shown ONLY as a separate
// efficiency stat and NEVER contributes XP. The view honours a self-contained
// global toggle (growth.enabled, from the AR-340 policy when present) and an
// in-session user override; there are NO streak/punishment surfaces.
let growthUserShow = true;

function growthData() {
  return (runtimeState && runtimeState.growth) || { enabled: false };
}

// ASCII keys only here (cp949 node-check guard). The KR label is provided by the
// Python payload (business_stage.label_ko) and rendered via escapeHtml.
const GROWTH_STAGE_LABELS = {
  garage: "Garage",
  seed: "Seed",
  startup: "Startup",
  scaleup: "Scaleup",
  unicorn: "Unicorn",
};

function growthStageLabel(stage) {
  const key = String((stage && stage.key) || "garage");
  return GROWTH_STAGE_LABELS[key] || key;
}

function growthHero(data) {
  const project = data.project || {};
  const stage = data.business_stage || {};
  const pct = numericPct(project.xp_pct) ?? 0;
  const ladder = (stage.ladder || []).map((key) =>
    `<li class="${key === stage.key ? "is-current" : ""}">${escapeHtml(GROWTH_STAGE_LABELS[key] || key)}</li>`
  ).join("");
  const nextStage = stage.next_key
    ? `${escapeHtml(stage.achievements_to_next ?? 0)} to ${escapeHtml(growthStageLabel({ key: stage.next_key }))}`
    : "max stage";
  return `
    <div class="growth-hero-card">
      <span class="growth-hero-label">Project Level</span>
      <span class="growth-level-value">Lv ${escapeHtml(project.level ?? 1)}</span>
      <div class="progress-track" role="img" aria-label="XP ${escapeHtml(pct)}%"><div class="growth-xp-bar" style="width: ${pct}%"></div></div>
      <span class="growth-hero-label">${escapeHtml(project.cumulative_xp ?? 0)} XP - ${escapeHtml(project.xp_for_next ?? 0)} to next</span>
    </div>
    <div class="growth-hero-card">
      <span class="growth-hero-label">Business Stage</span>
      <span class="growth-stage-chip">${escapeHtml(growthStageLabel(stage))} (${escapeHtml(stage.label_ko || "")})</span>
      <span class="growth-hero-label">${escapeHtml(stage.achievements ?? 0)} achievements - ${nextStage}</span>
      <ul class="growth-ladder">${ladder}</ul>
    </div>
  `;
}

function growthFormula(data) {
  const formula = data.xp_formula || {};
  const weights = formula.weights || {};
  const counts = formula.counts || {};
  const contrib = formula.contributions || {};
  const rows = [
    ["Completed tasks", counts.completed_tasks, weights.completed_task, contrib.completed_tasks],
    ["Gate passes", counts.gate_passes, weights.gate_pass, contrib.gate_passes],
    ["Test growth", counts.test_growth, weights.test_growth, contrib.test_growth],
    ["Review outputs", counts.review_outputs, weights.review_output, contrib.review_outputs],
  ].map((row) =>
    `<div class="growth-formula-row"><span>${escapeHtml(row[0])} (${escapeHtml(row[1] ?? 0)} x ${escapeHtml(row[2] ?? 0)})</span><strong>${escapeHtml(row[3] ?? 0)} XP</strong></div>`
  ).join("");
  return `
    <p class="growth-section-title">XP Formula (outcomes only)</p>
    <div class="growth-formula-rows">
      ${rows}
      <div class="growth-formula-row growth-formula-total"><span>Cumulative XP</span><strong>${escapeHtml(formula.cumulative_xp ?? 0)} XP</strong></div>
    </div>
    <p class="growth-note">Token consumption is excluded from XP by design (anti-waste).</p>
  `;
}

function growthEfficiency(data) {
  const eff = data.efficiency || {};
  const stats = [
    ["Tokens / task", eff.tokens_per_task],
    ["Total tokens", eff.token_total],
    ["Rework events", eff.rework_events],
    ["Rework rate", `${escapeHtml(eff.rework_rate_pct ?? 0)}%`],
  ].map((stat) =>
    `<div class="growth-stat"><span class="growth-stat-label">${escapeHtml(stat[0])}</span><span class="growth-stat-value">${escapeHtml(stat[1] ?? 0)}</span></div>`
  ).join("");
  return `
    <p class="growth-section-title">Efficiency (separate from XP)</p>
    <div class="growth-stat-grid">${stats}</div>
    <p class="growth-note">Efficiency stats never affect XP; they are not penalties.</p>
  `;
}

function growthTeams(data) {
  const teams = data.teams || [];
  if (!teams.length) return "";
  const rows = teams.map((team) =>
    `<div class="growth-row"><span><strong>${escapeHtml(team.team_id || "team")}</strong> <span class="growth-row-meta">${escapeHtml(team.agent_count ?? 0)} agents</span></span><span>Lv ${escapeHtml(team.level ?? 1)} - ${escapeHtml(team.xp ?? 0)} XP</span></div>`
  ).join("");
  return `<p class="growth-section-title">Team XP (team achievement first)</p>${rows}`;
}

function growthAgents(data) {
  const agents = data.agents || [];
  if (!agents.length) return "";
  const rows = agents.slice(0, 50).map((agent) =>
    `<div class="growth-row"><span><strong>${escapeHtml(agent.callsign || agent.id || "agent")}</strong> <span class="growth-row-meta">${escapeHtml(agent.role || "unknown")}</span></span><span>Lv ${escapeHtml(agent.level ?? 1)} - ${escapeHtml(agent.xp ?? 0)} XP</span></div>`
  ).join("");
  return `<p class="growth-section-title">Per-agent XP (role-based)</p>${rows}`;
}

function renderGrowth() {
  const body = $("growth-body");
  if (!body) return;
  const data = growthData();
  const toggle = $("growth-enabled-toggle");
  // The global toggle disables the whole feature; the user override only hides
  // the display for this session. Both gates must allow it to show.
  const globallyEnabled = data.enabled !== false;
  if (toggle) toggle.disabled = !globallyEnabled;
  const show = globallyEnabled && growthUserShow;
  const disabledNote = $("growth-disabled");
  if (disabledNote) {
    disabledNote.hidden = show;
    disabledNote.textContent = globallyEnabled ? "Growth display is turned off." : "Growth is disabled by policy.";
  }
  body.hidden = !show;
  if (!show) return;
  setHtml("growth-hero", growthHero(data));
  setHtml("growth-formula", growthFormula(data));
  setHtml("growth-efficiency", growthEfficiency(data));
  setHtml("growth-teams", growthTeams(data));
  setHtml("growth-agents", growthAgents(data));
}

function wireGrowthToggle() {
  const toggle = $("growth-enabled-toggle");
  if (!toggle || toggle.dataset.wired) return;
  toggle.dataset.wired = "1";
  toggle.addEventListener("change", () => {
    growthUserShow = !!toggle.checked;
    renderGrowth();
  });
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
  // TASK-AR-590: sparkline shows agent/team load trend across periods.
  // Numeric coercion: each cell.load is passed through Number(); non-finite
  // values are filtered inside componentSparkline (security/numeric purity).
  const sparkData = periods.map((period) => {
    const cell = (row.cells || []).find((item) => item.period === period) || { load: 0 };
    return Number(cell.load);
  });
  const spark = componentSparkline(sparkData, { label: escapeHtml(row.id) + " load trend" });
  return `<div class="workload-row">` +
    `<button type="button" class="workload-label workload-sparkline" ${drill} title="Show ${escapeHtml(row.id)} tasks">` +
    `<span>${escapeHtml(row.id)}<small>${escapeHtml(row.open_total ?? 0)} open - peak ${escapeHtml(row.peak_band || "idle")}</small></span>` +
    spark +
    `</button>` +
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
    const consumed = (row.consumed_pct === null || row.consumed_pct === undefined)
      ? "est-only"
      : `${row.consumed_pct}% used`;
    return patternOpsTokenBar({
      name: row.display_name || row.task_set_id || "",
      est,
      actual,
      maxEst,
      overBudget: !!row.over_budget,
      consumedLabel: consumed,
      estLabel: opsFormatTokens(est),
    });
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
  const spark = componentSparkline(points.map((p) => Number(p.score)), {
    label: `Eval score sparkline, ${escapeHtml(String(trend.count || n))} runs`,
  });
  host.innerHTML =
    `<div class="opsdash-sparkline-strip">` +
    `<span>${escapeHtml(String(points[0].score))} -> ${escapeHtml(String(points[points.length - 1].score))}</span>` +
    spark +
    `</div>` +
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
    const bars = weeks.map((w) => patternOpsVelocityBar(w, peak)).join("");
    velHost.innerHTML = `<div class="opsdash-velocity-head">Weekly velocity - ` +
      `avg ${escapeHtml(String(vel.avg_per_week || 0))}/wk, peak ${escapeHtml(String(vel.peak_week || 0))}</div>` +
      `<div class="opsdash-velocity-bars">${bars}</div>`;
  }
}

// SPEC-health-snapshot-v1: insight-first "is it healthy now?" strip. Verdict shows
// color AND a text label (never color-only). A sparkline appears ONLY for signals
// with a real series (throughput, quality); risk/budget are current-state only.
function healthVerdictMeta(verdict) {
  const map = {
    healthy: { tone: "success", key: "health.verdict.healthy" },
    watch: { tone: "warning", key: "health.verdict.watch" },
    at_risk: { tone: "danger", key: "health.verdict.at_risk" },
  };
  return map[verdict] || map.healthy;
}

function healthSignalText(sig) {
  if (sig.key === "throughput") {
    if (sig.value == null) return t("health.throughput") + ": " + t("health.no_data");
    let s = t("health.throughput") + ": " + sig.value + " " + t("health.per_week");
    if (sig.direction) {
      const arrow = sig.direction === "up" ? "\\u2191" : (sig.direction === "down" ? "\\u2193" : "\\u2192");
      s += " " + arrow + " (" + t("health.prev_week") + " " + sig.prev + ")";
    }
    return s;
  }
  if (sig.key === "quality") {
    if (sig.value == null) return t("health.quality") + ": " + t("health.no_data");
    let s = t("health.quality") + ": " + sig.value;
    if (typeof sig.avg === "number") s += " (" + t("health.avg") + " " + sig.avg + ")";
    return s;
  }
  if (sig.key === "risk") {
    if (!sig.blocking && !sig.overloaded) return t("health.risk_clear");
    return t("health.risk") + ": " + t("health.blocked") + " " + sig.blocking +
      " \\u00b7 " + t("health.overloaded") + " " + sig.overloaded;
  }
  if (sig.key === "budget") {
    return sig.over_budget ? (t("health.budget_over") + " " + sig.over_budget) : t("health.budget_ok");
  }
  return "";
}

function renderHealthSnapshot(data) {
  const host = $("health-snapshot");
  if (!host) return;
  const snap = data && data.health_snapshot;
  if (!snap) { host.hidden = true; host.innerHTML = ""; return; }
  host.hidden = false;
  const v = healthVerdictMeta(snap.verdict);
  const tiles = (snap.signals || []).map((sig) => {
    const spark = (sig.series && sig.series.length >= 2)
      ? componentSparkline(sig.series, { label: t("health." + sig.key) })
      : "";
    return `<div class="health-tile tone-${escapeHtml(sig.tone || "info")}">` +
      `<span class="health-tile-text">${escapeHtml(healthSignalText(sig))}</span>` +
      (spark ? `<span class="health-tile-spark" aria-hidden="true">${spark}</span>` : "") +
      `</div>`;
  }).join("");
  host.innerHTML =
    `<div class="health-verdict tone-${escapeHtml(v.tone)}">` +
    `<span class="health-verdict-dot" aria-hidden="true"></span>` +
    `<strong>${escapeHtml(t(v.key))}</strong></div>` +
    `<div class="health-tiles">${tiles}</div>`;
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
  renderHealthSnapshot(data);
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
  renderHomeSummary();
  renderKanban();
  renderWorkExplorer();
  renderMeetingRoom();
  renderTaskSetDirectory();
  renderTasksetCompletion();
  renderTasksetBoard();
  renderTeamAgents();
  renderGrowth();
  renderWorkloadHeatmap();
  renderOpsDashboard();
  renderAgents();
  renderInbox();
  renderChannels();
  renderMessages();
  renderEvents();
  renderEvidence();
  renderPlanning();
  renderRoadmapTimeline();
  renderTimeline();
  renderDependencyGraph();
  renderMap();
  renderOfficeMap();
  renderOrgChart();
  renderStateMachineViewer();
  renderSources();
  renderCommands();
  renderTriage();
  renderCalendar();
  renderSchedules();
  renderAutomation();
  renderProperties();
  renderLabels();
  renderNotificationRouting();
  renderWorkspaces();
  renderWidgets();
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
  const shell = $("runtime-console-app");
  if (shell) {
    shell.dataset.workSurfaceOpen = "true";
    // TASK-AR-624: expose the active view so the task/runtime action forms can
    // be scoped to board/work only (they are noise atop Labels, graphs, etc.).
    shell.dataset.activeView = view;
  }
  let activeLink = null;
  navLinks().forEach((item) => {
    const isActive = item.dataset.view === view;
    item.classList.toggle("is-active", isActive);
    item.setAttribute("aria-selected", isActive ? "true" : "false");
    if (isActive) activeLink = item;
  });
  const activeMore = activeLink ? activeLink.closest(".sidebar-more") : null;
  if (activeMore) activeMore.open = true;
  document.querySelectorAll(".view").forEach((item) => item.classList.remove("is-active"));
  target.classList.add("is-active");
  if (view === "knowledge-graph") loadKnowledgeGraph();
  if (view === "search") focusSearchView();
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
  const shell = $("runtime-console-app");
  const view = route ? viewForRoute(route) : "board";
  activateView(view || "board", { updateHash: false });
  if (!route && shell) shell.dataset.workSurfaceOpen = "false";
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

// TASK-AR-341: workspace switcher menu open/close + safe switch delegation.
$("workspace-switcher-toggle")?.addEventListener("click", (event) => {
  event.stopPropagation();
  toggleWorkspaceMenu();
});
$("workspace-switcher-menu")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-workspace-switch]");
  if (!button) return;
  event.preventDefault();
  switchWorkspace(button.getAttribute("data-workspace-switch"));
});
document.addEventListener("click", (event) => {
  const switcher = $("workspace-switcher-menu");
  if (!switcher || switcher.hidden) return;
  if (!event.target.closest(".workspace-switcher")) toggleWorkspaceMenu(false);
});

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
  if (event.target === $("search-view-input")) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      searchViewActiveIndex += 1;
      renderSearchViewResults($("search-view-input").value.trim());
      return;
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      searchViewActiveIndex = Math.max(0, searchViewActiveIndex - 1);
      renderSearchViewResults($("search-view-input").value.trim());
      return;
    } else if (event.key === "Enter") {
      event.preventDefault();
      navigateToResult(searchViewResults[searchViewActiveIndex]);
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
  const viewInput = $("search-view-input");
  if (viewInput) {
    viewInput.addEventListener("input", () => {
      searchViewActiveIndex = 0;
      if (searchViewDebounce) clearTimeout(searchViewDebounce);
      searchViewDebounce = setTimeout(runSearchView, 140);
    });
  }
  const viewBox = $("search-view-results");
  if (viewBox) {
    viewBox.addEventListener("click", (event) => {
      const row = event.target.closest(".search-result");
      if (!row) return;
      navigateToResult(searchViewResults[Number(row.dataset.resultIndex) || 0]);
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
wireGrowthToggle();
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
// ----- TASK-AR-338: notification inbox filters + subscription forms -----
$("inbox-filter-kind")?.addEventListener("change", (event) => { inboxFilters.kind = event.target.value; renderInbox(); });
$("inbox-filter-severity")?.addEventListener("change", (event) => { inboxFilters.severity = event.target.value; renderInbox(); });
$("inbox-filter-unread")?.addEventListener("change", (event) => { inboxFilters.unread = event.target.checked; renderInbox(); });
$("inbox-show-muted")?.addEventListener("change", (event) => { inboxFilters.showMuted = event.target.checked; renderInbox(); });
$("inbox-mark-all-read")?.addEventListener("click", markAllNotificationsRead);
$("inbox-subscribe-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const payload = { actor: "ui" };
  const kind = $("inbox-sub-kind")?.value;
  const severity = $("inbox-sub-severity")?.value;
  const taskset = ($("inbox-sub-taskset")?.value || "").trim();
  if (kind) payload.kinds = [kind];
  if (severity) payload.severities = [severity];
  if (taskset) payload.tasksets = [taskset];
  const result = await sendJson("/api/commands", { type: "notification.subscribe", payload: { type: "notification.subscribe", payload } });
  const hint = $("inbox-subscribe-hint");
  if (hint) {
    const ok = result && result.status !== "failed";
    hint.textContent = ok ? "Subscription proposal queued." : `Failed: ${(result.errors || ["error"]).join("; ")}`;
    hint.classList.toggle("is-ok", ok);
    hint.classList.toggle("is-error", !ok);
  }
  if (taskset && $("inbox-sub-taskset")) $("inbox-sub-taskset").value = "";
});
$("inbox-keyword-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const keyword = ($("inbox-keyword")?.value || "").trim();
  if (!keyword) return;
  const result = await sendJson("/api/commands", { type: "notification.mute", payload: { type: "notification.mute", payload: { actor: "ui", keyword } } });
  const hint = $("inbox-subscribe-hint");
  if (hint) {
    const ok = result && result.status !== "failed";
    hint.textContent = ok ? "Keyword mute proposal queued." : `Failed: ${(result.errors || ["error"]).join("; ")}`;
    hint.classList.toggle("is-ok", ok);
    hint.classList.toggle("is-error", !ok);
  }
  if ($("inbox-keyword")) $("inbox-keyword").value = "";
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
$("subscription-form")?.addEventListener("submit", async (event) => {
  event.preventDefault();
  const severityChoice = $("subscription-severity").value;
  const severities = severityChoice === "all" ? ["immediate", "aggregate", "digest"] : [severityChoice];
  await sendJson("/api/commands", {
    type: "subscription.create",
    payload: {
      type: "subscription.create",
      payload: {
        actor: "ui",
        channel: $("subscription-channel").value,
        kind: $("subscription-kind").value,
        severities,
        aggregate_minutes: Number($("subscription-window").value) || 5,
        enabled: false,
      },
    },
  });
  $("subscription-channel").value = "";
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
  host.innerHTML = items.length
    ? items.map((item) => patternPortabilityPreviewRow(item)).join("")
    : `<div class="empty">No rows parsed</div>`;
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

// TASK-AR-340: experience policy + onboarding/help wiring. Policy attributes
// are already set by the no-flash bootstrap; this re-applies after the DOM is
// ready and wires the settings controls, tour, and contextual help.
initExperienceSettings();
initOnboardingTour();
initContextualHelp();
initWorkStateCollapse();
// TASK-AR-341: language bootstrap + i18n string load.
initLanguage();
loadI18n();
initInboxDetailDrawer();
initBoardControls();
initOrgRoleDetail();

loadState();
connectEventStream();
setInterval(loadState, 4000);
// TASK-AR-564: decision-first cockpit - load the attention inbox and keep it
// fresh (slower cadence than state; it is a derived read over work items).
loadCockpit();
setInterval(loadCockpit, 8000);
// TASK-AR-567: secondary Work hero over org_read_api.work_state.
loadWorkState();
setInterval(loadWorkState, 15000);
"""
