---
title: Agent Runtime UI Design Guide
status: accepted
date: 2026-06-11
task_set_id: TASKSET-AR-UI-DESIGN-SYSTEM
---

# Agent Runtime UI Design Guide

## Decision

Agent Runtime should use a Linear-like operator console as the primary UI model: dense, calm, keyboard-friendly, evidence-first, and dark enough to reduce operational noise. The supporting references are Raycast for command execution, Sentry for issue/evidence surfacing, Vercel for deployment/status clarity, and Miro/FigJam for graph and planning surfaces.

## Product fit

Agent Runtime is not a marketing surface. It is a control room for agents, tasks, owner gates, evidence, state machines, and handoffs. The UI should help an operator answer four questions quickly:

1. What needs attention now?
2. Which task set owns this work?
3. What evidence supports the current state?
4. What command or next action is safe?

## Visual system

Core tokens:

```css
--canvas: #010102;
--panel: #0f1011;
--panel-strong: #15171a;
--surface-raised: #1b1d22;
--ink: #f7f8f8;
--muted: #a2a8b3;
--subtle: #62666d;
--line: #23252a;
--line-strong: #343844;
--primary: #5e6ad2;
--primary-hover: #828fff;
--success: #27a644;
--warning: #d99a2b;
--danger: #f04438;
```

Typography should feel precise and technical. Prefer `Geist` or `IBM Plex Sans` with tight display spacing for headers and readable medium-weight body text for dense cards.

## Layout principles

Use a persistent top command area, compact tab navigation, a main work surface, and a sticky detail panel. The main surface can switch between backlog, agents, messages, events, evidence, planner, map, sources, and writes without changing the operator's mental model.

Prioritize density over decoration. Use thin borders, shallow elevation, and small status colors rather than large color blocks. Visual drama should come from structure, not ornament.

## Interaction principles

Commands are first-class. Every command must expose intent, target, and result. Evidence is also first-class. A task without evidence should look incomplete even if it is marked done.

Status color usage:

```text
green  = pass, completed, healthy
amber  = pending, in progress, warning
red    = blocked, failed, error
blue   = info, external reference
purple = primary command and active context
```

## Component guidance

Task cards should show id, title, status, priority, task set, and evidence hooks. Agent cards should show role, status, score, and currently claimed work. Event cards should be filterable and severity-colored. Evidence cards should look audit-ready and link naturally to commands, files, and gates.

## Do not

Do not use a generic SaaS dashboard style. Do not hide evidence behind secondary pages. Do not make the UI feel like a chat app. Do not make task states depend on color alone; keep labels visible.

## Implementation target

The first implementation target is `src/agent_runtime/ui_console.py`. The DOM and API contracts must stay stable while the CSS moves toward the operator-console visual model.

## Amendment 2026-06-11 (Owner decision)

The default theme changes from dark to **light (Notion-like)**. The dark token set above is preserved verbatim as the optional Dark Mode. All components must consume semantic tokens only so both themes share one structure. The single-page tab navigation is superseded by a collapsible sidebar IA. See `docs/superpowers/plans/2026-06-11-ui-ux-v2-console.md` (TASKSET-AR-UI-UX-V2) for the full V2 plan; the rest of this guide (density, evidence-first, status colors, component guidance) remains in force.

## Amendment 2026-06-13 (TASK-AR-320 — theme token system implemented)

The theme system from the V2 plan is implemented in `src/agent_runtime/ui_console.py`.

- **Dual token scopes.** `:root` defines the default **light (Notion-style)** palette; `[data-theme="dark"]` overrides the same token names with the **Linear dark** values. Each block sets `color-scheme` so native form controls follow the surface. The previous hard-coded color literals throughout the stylesheet were replaced with `var(--token)` references — the only raw color literals that remain live inside these two token-definition blocks (plus the brand glyph, which is intentionally white-on-gradient in both themes).
- **Semantic token set.** Surfaces (`--canvas/--panel/--panel-strong/--surface-raised`), text (`--ink/--muted/--subtle/--on-accent`), lines (`--line/--line-strong`), status (`--primary/--success/--warning/--danger/--info/--purple` plus legacy aliases `--teal/--blue/--amber/--red/--violet`), soft status fills (`--*-soft`, `--*-line`), generic overlays (`--raise/--tile/--inset-soft`), and effect tokens (`--shadow/--shadow-pop/--focus`, plus brand/canvas/progress gradients). Components reference tokens only.
- **Status colors stay consistent and labelled.** The green/amber/red/blue/purple meanings are identical in both themes and are always paired with a visible text label (status chips, pills, lane names, phase chips) — color is never the sole signal. Light-theme status values keep WCAG-adequate contrast against the warm white canvas.
- **Toggle + auto-detection + persistence.** A header `#theme-toggle` button switches light/dark and persists the choice in `localStorage` (`agent-runtime-theme`). First load resolves: saved choice → OS `prefers-color-scheme` → light default. An inline `<head>` bootstrap applies `data-theme` before first paint (no flash); `app.js` re-applies, wires the toggle, and live-follows OS preference changes until the user makes an explicit choice.

DOM ids and structure are unchanged so the sibling V2 foundation tasks (sidebar IA, list patterns) merge cleanly.
