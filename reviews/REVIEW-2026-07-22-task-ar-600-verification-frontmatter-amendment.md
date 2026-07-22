---
type: planning
title: TASK-AR-600 verification frontmatter amendment
date: 2026-07-22
signal: pass
score: 99
tags: [planning-record, task-ar-600, verification, schema]
---

# TASK-AR-600 verification frontmatter amendment

## Bottom Line

Unit W4a passed both registered commands. Task-level `work verify` then correctly refused because
the older TASK-AR-600 record stored its three verification commands only in the Markdown body, not
in machine-readable frontmatter. No product test failed.

## Decision

- Copy the existing task body commands into canonical `verification` frontmatter and initialize
  `verification_status: pending`.
- Preserve the already-passed unit evidence unchanged.
- Refresh T0/T3 assumptions with the task record as an anchor, then rerun task-level W4a.

