---
type: review
id: RESEARCH-2026-06-10-realtime-collab-conflict-patterns
audience: owner
status: pass
signal: pass
score: 94
priority: High
tags: [research, collaboration, concurrency, conflict-resolution, owner-brief]
---

# Realtime Collaboration Conflict Pattern Research

## Bottom Line

- Summary: researched collaboration platforms and translated the patterns into `agent_runtime` concurrency controls.
- Result: the right model is not one global merge algorithm; it is typed state plus ownership boundaries.
- Boundary: this review summarizes public platform patterns and local design decisions, not proprietary internal algorithms.

## Signal

| Platform family | Pattern | Local mapping |
| --- | --- | --- |
| Google Docs/Slides | operation history and operational transformation for text | avoid direct shared markdown editing from workers |
| Figma | object/property-level multiplayer with server authority | represent task, claim, pane, and worktree as separate objects |
| Notion | page/block records with last edit metadata | keep task/task-set state block-like and source-linked |
| Firestore | transactions retry when read state changes | use CAS/lease checks before mutating canonical state |
| ActivityPub / AT Protocol | append-only activities or signed commits | record pane events append-only and replay derived views |

## Insight

- Whole-document collaboration algorithms are a poor fit for generated SSoT files because semantic conflicts matter more than text offsets.
- The repeated repo failure mode was a false safety signal: a claim named a worktree even when that worktree did not exist.
- The durable pattern is `worker event -> claim/worktree evidence -> orchestrator merge/regenerate`.

## Decision

- Decision: use event sourcing for pane lifecycle records.
- Decision: keep SSoT files single-writer by policy and gate.
- Decision: require actual worktree existence before task-set claims.
- Decision: derive UI/board status from event logs, claim files, and task files.

## Action Board

| Status | Action | Evidence |
| --- | --- | --- |
| Done | Add append-only pane events | `scripts/pane_event_log.py` |
| Done | Add SSoT write finding gate | `scripts/collaboration_concurrency_gate.py` |
| Done | Add worktree auto-create path | `scripts/taskset_dispatcher.py` |
| Done | Add UI state collaboration summary | `agent_runtime.ui_state` |

## Risks / Blockers

- Risk: public platform articles describe architectural patterns, not all proprietary conflict-resolution internals.
- Risk: generated markdown SSoT files can still conflict if panes bypass dispatcher/worktree conventions.
- Blocker: none for translating the research into local runtime controls.

## Next Steps

1. Keep pane collaboration state append-only and replayable.
2. Keep shared SSoT writes orchestrator-owned.
3. Revisit CRDT/OT only if the runtime starts supporting true multi-editor text editing inside the same file.

## References

- Google Drive Blog: `https://drive.googleblog.com/2010/09/whats-different-about-new-google-docs_22.html`
- Figma multiplayer overview: `https://www.figma.com/blog/how-figmas-multiplayer-technology-works/`
- Notion page/block API: `https://developers.notion.com/reference/page`, `https://developers.notion.com/reference/block`
- Firestore transactions: `https://firebase.google.com/docs/firestore/manage-data/transactions`
- ActivityPub: `https://www.w3.org/TR/activitypub/`
- AT Protocol repository spec: `https://atproto.com/specs/repository`
