# Agent Runtime UI Console - Product & Build Brief

## 0. One-Line Goal

Build a user-interactive web UI for the existing `agent_runtime`.

The UI must let the user see, control, and understand the whole agent work process without repeatedly asking the CLI to print backlog, status, logs, or task details.

Core rule:

```text
Runtime is the source of truth.
UI is the control room.
Agents are visible workers.
Tasks are visible work items.
Messages are visible team chat.
Events are visible history.
```

---

## 1. Current Project State

The project already has an agent runtime that can run long loops through `/goal`.

Observed current capability:

```text
/goal can keep the system running for 12+ hours or 24+ hours.
The runtime can continue work without constant user prompting.
The runtime has state-machine based process tracking.
The runtime has tasks, logs, agent states, and messages in some form.
The CLI can execute commands, but the user has to repeatedly ask for backlog/status/logs.
```

Current pain:

```text
User must ask "show backlog" again and again.
CLI output gets truncated or formatted poorly.
Repeated status requests waste tokens and time.
CLI is a poor UI for backlog, kanban, scheduling, history, logs, and agent communication.
The user needs a persistent visual control room.
```

Therefore:

```text
Do not solve this by making the CLI print prettier.
Build a web UI that reads runtime state and events directly.
```

---

## 2. Product Vision

Create a web-based visual control room for the agent runtime.

The UI should feel like a mix of:

```text
Slack / Discord  -> agent messages and channels
Notion           -> editable task and project pages
Jira / Linear    -> backlog, kanban, roadmap, milestones
Online RPG       -> agent team presence, login/logout, working status
ROS rqt graph    -> node graph of agents and communication links
GitHub           -> issues, PRs, commits, errors, evidence
```

The target user should be able to open the UI and immediately understand:

```text
What is the current goal?
What tasks exist?
What is being worked on now?
Which agent is working?
Which tasks are blocked?
What did agents say to each other?
What errors happened?
What changed recently?
What is next?
```

---

## 3. Primary Principle

The UI must not become the runtime.

The backend runtime owns:

```text
agent state
task state
message routing
event log
goal loop
provider execution
state machine
```

The UI owns:

```text
visualization
human interaction
CRUD requests
task ordering
manual prompt entry
status inspection
filters and search
```

All UI actions must go through runtime APIs or runtime command files.

Preferred architecture:

```text
agent_runtime
  -> state/events/messages/tasks
  -> backend API or file adapter
  -> web UI
```

---

## 4. MVP Goal

Build a first UI that solves the original pain.

MVP must show:

```text
1. Backlog
2. Current tasks
3. Kanban board
4. Agent status
5. Event log
6. Message log
7. Goal status
8. Basic task detail panel
```

MVP must allow:

```text
create task
edit task title/description/status
reorder tasks
assign task to agent
send prompt/instruction to an agent through runtime
pause/resume goal loop if runtime supports it
refresh state manually
```

MVP does not need:

```text
beautiful game graphics
full auth system
Slack integration
Notion integration
calendar sync
real-time websocket if polling is simpler
terminal emulation
direct Claude/Codex TUI embedding
multi-user permissions
```

---

## 5. First UI Screens

### 5.1 Dashboard

Purpose:

```text
Show whole runtime at a glance.
```

Widgets:

```text
Current goal
Runtime status: running / idle / paused / error
Active agents
Active tasks
Blocked tasks
Recent errors
Recent events
Next recommended task
```

---

### 5.2 Backlog / Kanban Board

Purpose:

```text
Replace repeated "show backlog" CLI requests.
```

Columns:

```text
Backlog
Ready
In Progress
Review
Blocked
Done
```

Task card fields:

```text
task id
title
status
priority
assignee
owner agent
updated time
blocked reason
short summary
```

Interactions:

```text
click task -> open detail drawer
drag task -> reorder or change status
edit title
edit description
edit priority
edit assignee
create task
archive task
```

Important:

```text
The UI must preserve task order.
Order matters because the runtime may choose next work from ordered backlog.
```

---

### 5.3 Task Detail Drawer

Purpose:

```text
Show full information without flooding CLI.
```

Fields:

```text
task id
title
description
status
priority
assignee
labels
goal link
parent task
child tasks
acceptance criteria
latest agent notes
related messages
related events
related logs
artifacts
error links
PR/commit links if available
created_at
updated_at
completed_at
```

Actions:

```text
save edits
assign to agent
send task to runtime
mark blocked
mark ready
add comment
request review
```

---

### 5.4 Agent Team View

Purpose:

```text
Show agent team like online RPG characters.
```

Each agent card shows:

```text
avatar/icon
role
status
current task
last message
model/provider
online/offline
heartbeat time
tools available
error state
```

Possible statuses:

```text
online
idle
thinking
working
waiting
blocked
reviewing
in_meeting
offline
error
```

Interactions:

```text
click agent -> open agent detail
send prompt to agent
view agent messages
view agent task history
view agent logs
```

Do not overbuild avatars in MVP.
Simple cards and status badges are enough.

---

### 5.5 Messages / Team Chat

Purpose:

```text
Show agent-to-agent communication like Slack or Discord.
```

Views:

```text
All messages
By agent
By task
By goal
By channel
System messages
Human messages
```

Message item fields:

```text
message id
from
to
channel
task id
content
timestamp
status
```

Statuses:

```text
open
claimed
answered
archived
failed
```

Interactions:

```text
send message to agent
reply to thread
filter by task
filter by agent
jump to related task
```

---

### 5.6 Event Timeline

Purpose:

```text
Show what happened over time.
```

Event types:

```text
goal.started
goal.iteration.started
goal.iteration.completed
task.created
task.updated
task.started
task.completed
task.blocked
agent.started
agent.stopped
agent.output
message.sent
message.received
error.created
file.changed
commit.created
pr.created
```

Interactions:

```text
filter by type
filter by agent
filter by task
search
open related task/message/log
```

This is the "combat log" of the agent world.

---

### 5.7 Process / State Machine View

Purpose:

```text
Visualize current workflow states.
```

Show:

```text
global runtime state machine
goal loop state
task lifecycle state
agent lifecycle state
individual task state
```

Simple version:

```text
Use cards or a vertical stepper.
No need for complex graph library at first.
```

Future version:

```text
Use graph visualization.
```

---

### 5.8 Agent Communication Graph

Purpose:

```text
Show agents as nodes and messages/tasks as edges, similar to ROS rqt graph.
```

Nodes:

```text
user
orchestrator
ceo
planner
coder
qa
tester
reviewer
```

Edges:

```text
message
task assignment
review request
dependency
blocked by
```

MVP:

```text
Static graph generated from latest state.
```

Later:

```text
Live graph updated from event stream.
```

---

### 5.9 Roadmap / Goals / Milestones

Purpose:

```text
Show high-level direction, not just individual tasks.
```

Entities:

```text
vision
objective
goal
milestone
roadmap item
task
subtask
```

Hierarchy:

```text
Vision
  -> Objective
    -> Goal
      -> Milestone
        -> Task
          -> Subtask
```

UI:

```text
roadmap list
milestone timeline
goal detail
objective progress
```

---

### 5.10 Logs / Errors / Issues / PRs

Purpose:

```text
Make debugging and history visible.
```

Sections:

```text
runtime logs
agent logs
error list
issue list
PR list
commit list
evidence files
screenshots
test results
```

Interactions:

```text
open error detail
link error to task
mark resolved
copy stack trace
jump to related event
```

---

## 6. LLM / CLI Integration Reality

Do not try to embed Claude Code or Codex CLI as a real terminal emulator in the first UI.

That is hard and fragile.

Better model:

```text
UI sends instruction to runtime.
Runtime creates task/message.
Agent worker receives task/message.
Agent worker calls provider.
Provider may be Claude, Codex, OpenAI, Anthropic, Dummy, Cursor, OpenCode.
Runtime stores output.
UI displays output.
```

Correct flow:

```text
User prompt in web UI
  -> POST /commands or write command file
  -> runtime creates message/task
  -> agent worker processes it
  -> output saved as event/message
  -> UI refreshes or receives event
```

Wrong first approach:

```text
Web UI embeds Claude CLI directly.
Browser tries to control terminal panes.
Browser tries to type into arbitrary Claude sessions.
```

This may be explored later with PTY/WebSocket terminal support, but it is not MVP.

---

## 7. Data Model Required by UI

If these models already exist, adapt to them.
If not, add thin normalized views for UI.

### 7.1 Task

```json
{
  "id": "TASK-123",
  "title": "Implement backlog UI",
  "description": "Build kanban board for runtime tasks",
  "status": "ready",
  "priority": "high",
  "order": 10,
  "assignee": "coder",
  "labels": ["ui", "runtime"],
  "goal_id": "GOAL-001",
  "parent_id": null,
  "blocked_reason": null,
  "created_at": "...",
  "updated_at": "...",
  "completed_at": null
}
```

### 7.2 Agent

```json
{
  "id": "agent-coder-001",
  "role": "coder",
  "display_name": "Coder",
  "status": "working",
  "provider": "claude",
  "model": "opus",
  "current_task_id": "TASK-123",
  "last_heartbeat": "...",
  "last_message": "Working on backlog UI"
}
```

### 7.3 Message

```json
{
  "id": "MSG-001",
  "from": "planner",
  "to": "coder",
  "channel": "task:TASK-123",
  "task_id": "TASK-123",
  "content": "Please implement the kanban columns first.",
  "status": "answered",
  "created_at": "...",
  "answered_at": "..."
}
```

### 7.4 Event

```json
{
  "id": "EVT-001",
  "type": "task.updated",
  "actor": "agent-coder-001",
  "task_id": "TASK-123",
  "payload": {},
  "created_at": "..."
}
```

### 7.5 Goal

```json
{
  "id": "GOAL-001",
  "title": "Build Agent Runtime UI",
  "status": "running",
  "current_iteration": 42,
  "started_at": "...",
  "updated_at": "..."
}
```

---

## 8. Backend Interface

Prefer API if possible.

Minimum API:

```text
GET  /api/state
GET  /api/tasks
POST /api/tasks
PATCH /api/tasks/:id
POST /api/tasks/:id/reorder
GET  /api/agents
GET  /api/messages
POST /api/messages
GET  /api/events
GET  /api/goals
POST /api/commands
```

If API does not exist yet, create a file adapter.

File adapter can read:

```text
runtime state files
task files
message files
event logs
goal logs
agent status files
```

File adapter can write:

```text
new command request file
task update file
message request file
```

Recommended fallback:

```text
.ui_outbox/COMMAND-*.json
```

Runtime watches this directory or polls it.

Example command:

```json
{
  "type": "call_agent",
  "target": "coder",
  "instruction": "Implement TASK-123",
  "created_by": "user"
}
```

---

## 9. Real-Time Strategy

Start simple.

Phase 1:

```text
UI polls /api/state every 2-5 seconds.
Manual refresh button exists.
```

Phase 2:

```text
Server-Sent Events for event stream.
```

Phase 3:

```text
WebSocket for live messages, logs, and agent status.
```

Do not block MVP on true real-time infrastructure.

Polling is acceptable if state is reliable.

---

## 10. Frontend Recommendation

Use a simple modern web stack.

Good default:

```text
React + Vite + TypeScript
```

Useful UI components:

```text
cards
tables
drawers
tabs
badges
kanban columns
timeline
graph view
modal
command input
```

Recommended libraries if allowed:

```text
TanStack Table for task lists
dnd-kit for drag/drop task ordering
React Flow for agent graph
date-fns for time formatting
Zustand or simple React state for client store
```

If dependencies must be minimal, implement plain React first.

---

## 11. Backend Recommendation

If the runtime is Python:

```text
FastAPI is a good backend option.
```

If no API server should be added yet:

```text
Build static UI + small local Node/Python file adapter.
```

Preferred direction:

```text
agent_runtime remains independent.
ui_server reads runtime files and exposes safe APIs.
```

Do not let the frontend directly mutate random runtime files.

---

## 12. UX Rules

### Rule 1: Always show current state

The user should never need to ask:

```text
show backlog
show status
show current task
```

These are always visible.

### Rule 2: Click instead of ask

If the user wants detail, they click task/agent/message.

### Rule 3: Every item links to history

Task detail should link to:

```text
messages
events
logs
errors
artifacts
commits
```

### Rule 4: Show confidence and freshness

Every panel should show:

```text
last updated time
source file or API source
runtime status
```

### Rule 5: UI cannot silently corrupt runtime

All writes must go through safe commands or runtime APIs.

---

## 13. Better Ideas to Add

### 13.1 Replay Mode

Allow user to replay what happened during a long `/goal` loop.

```text
timeline scrubber
iteration by iteration playback
filter by task/agent/error
```

### 13.2 Daily Brief

Generate a short daily summary:

```text
completed today
blocked today
important decisions
errors
next recommended work
```

### 13.3 Agent Focus Mode

Click one agent and see:

```text
current task
recent thoughts/output
messages
logs
tools used
state transitions
```

### 13.4 Human Approval Queue

Some actions should wait for user approval:

```text
delete file
commit
push
PR creation
large refactor
dependency install
long-running goal
```

### 13.5 Workload Heatmap

Show:

```text
which agent is overloaded
which task is stuck
which status has too many items
```

### 13.6 Command Palette

Keyboard command palette:

```text
create task
assign task
send prompt
start goal
pause runtime
open logs
filter errors
```

### 13.7 Templates

Create domain-specific workspaces:

```text
software project
robotics R&D
paper writing
proposal writing
bug triage
QA sprint
```

### 13.8 Evidence Panel

For each completed task, show proof:

```text
test result
screenshot
diff
commit
PR
log excerpt
```

---

## 14. Implementation Order

### Phase 0: Discover Existing Runtime Files

Goal:

```text
Find where current runtime stores:
tasks
agents
messages
events
goals
logs
state machine
```

Deliverable:

```text
docs/UI_RUNTIME_DATA_MAP.md
```

---

### Phase 1: Read-Only UI

Goal:

```text
Display runtime state without mutating anything.
```

Build:

```text
Dashboard
Backlog table
Agent status cards
Event timeline
Message log
Task detail drawer
```

No CRUD yet.

Success:

```text
User can open UI and see current backlog/status without asking CLI.
```

---

### Phase 2: Basic CRUD

Goal:

```text
Let user manage tasks from UI.
```

Build:

```text
create task
edit task
change status
assign agent
reorder backlog
add comment/message
```

Writes go through API or command outbox.

---

### Phase 3: Runtime Commands

Goal:

```text
Let user control runtime from UI.
```

Build:

```text
send prompt to agent
start goal
pause goal
resume goal
stop goal
request review
request meeting
```

Do not embed Claude terminal.
Use runtime command interface.

---

### Phase 4: Live Updates

Goal:

```text
Make UI feel alive.
```

Build:

```text
SSE or WebSocket event stream
live agent heartbeat
live task updates
live message updates
toast notifications
```

---

### Phase 5: Graph and Process Views

Goal:

```text
Visualize agent topology and state machines.
```

Build:

```text
agent communication graph
goal state machine view
task lifecycle view
process detail view
```

---

### Phase 6: Game-Like UX

Goal:

```text
Make agent team understandable to non-experts.
```

Build:

```text
agent avatars
online/offline animations
meeting room
quest board terminology option
agent activity feed
```

---

## 15. What To Avoid

Avoid these early:

```text
Do not build a full clone of Notion.
Do not build a full clone of Slack.
Do not build a full clone of Jira.
Do not embed raw Claude/Codex terminal first.
Do not make frontend write directly to many runtime files.
Do not require perfect real-time streaming for MVP.
Do not make the UI the source of truth.
Do not add authentication until local single-user UI works.
```

---

## 16. Success Criteria for First Useful Version

The first useful version is done when:

```text
User starts runtime.
User opens UI.
UI shows backlog without asking CLI.
UI shows active agents.
UI shows active/current goal.
UI shows recent events.
UI shows recent messages.
User can click a task and see detail.
User can create/edit/reorder tasks.
User can send a prompt to an agent through runtime.
All changes are reflected in runtime state.
```

---

## 17. Caveman Summary for LLM Builder

```text
Build web control room.

Runtime already works.
CLI is annoying.
User wants persistent UI.

Show:
- backlog
- kanban
- tasks
- agents
- messages
- events
- logs
- goals
- errors
- roadmap

First: read-only.
Then: CRUD.
Then: send commands.
Then: live updates.
Then: graph.
Then: game feel.

Do not control Claude terminal directly.
Send commands to runtime.
Runtime talks to LLM.
UI watches runtime.

Runtime = truth.
UI = eyes and hands.
Agents = workers.
Tasks = work.
Messages = chat.
Events = history.
```
