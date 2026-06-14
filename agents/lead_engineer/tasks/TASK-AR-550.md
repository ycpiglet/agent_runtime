---
id: TASK-AR-550
display_id: TASK-AR-550
task_uid: 1f502ba9-46ec-4e28-89ad-80cf1f292f56
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P2
difficulty: L
est_hours: 16
est_tokens: 12000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - ui
  - realtime
  - sse
  - performance
---

# TASK-AR-550 - Real-time updates via Server-Sent Events (replace polling)

## Goal

- The console polls every 5-10s, adding latency and wasted bandwidth. Add Server-Sent Events (SSE) with delta updates so new tasks/messages/events appear in near-real-time.

## Scope

### Input
- The console's `/api/state` / `/api/stream` polling path; pane/event sources.
- Verification case VC-UIN-3 (notification latency).

### Process
- Add an SSE endpoint that streams deltas (changed tasks/events) keyed by a sequence/cursor; client applies deltas without a full re-render.
- Fall back to polling when SSE is unavailable.

### Output
- SSE endpoint + client consumer + graceful fallback.

## Acceptance Criteria

- A new message/event appears within ~1s (vs poll interval) over SSE.
- Delta updates avoid full-page re-render; fallback to polling works.
- No regression when SSE is disabled.

## Acceptance note

- Structural change (rendering model); land behind a flag and stage incrementally.

## Evidence Targets

- Endpoint + client diff; latency measurement before/after; VC-UIN-3.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`.
