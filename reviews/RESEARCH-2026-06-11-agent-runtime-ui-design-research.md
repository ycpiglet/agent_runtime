---
title: Agent Runtime UI Research Synthesis
date: 2026-06-11
status: accepted
task_set_id: TASKSET-AR-UI-DESIGN-SYSTEM
---

# Agent Runtime UI Research Synthesis

## Bottom Line

The closest design fit for Agent Runtime is Linear's dense execution workspace, adapted into an operator console. Agent Runtime should use Raycast-like command affordances, Sentry-like evidence surfacing, Vercel-like status clarity, and Miro/FigJam-like map views as secondary patterns.

## Signal

Agent Runtime combines backlog ownership, agent state, command execution, event streams, evidence, roadmaps, source maps, writes, and governance checks. The strongest UI pattern is therefore not a generic analytics dashboard. It is a precise execution surface for operators.

## Insight

Comparable platforms emphasize different parts of the same problem:

| Platform | Primary emphasis | Useful pattern |
| --- | --- | --- |
| Linear | fast issue execution | dense task lists, low-friction keyboard workflow, calm visual hierarchy |
| Raycast | command initiation | command-first interaction and compact action states |
| Sentry | evidence and triage | severity, traceability, and issue context |
| Vercel | status and deployment confidence | clear health states, activity feed, and inspectable build output |
| Miro/FigJam | planning topology | spatial maps for dependencies and design/planning context |

## Decision

Use a Linear-like operator console as the base UI design. Use Raycast for command surfaces, Sentry for evidence cards, Vercel for status affordances, and Miro/FigJam for maps.

## Action

The first implementation target is the local Agent Runtime console. The HTML structure and API contracts remain stable, while the CSS token system and component styling move to the selected design model.

## Risk

The main risk is making the interface visually polished but operationally weaker. The design guide therefore treats evidence, labels, and command results as primary UI objects rather than decorative secondary metadata.
