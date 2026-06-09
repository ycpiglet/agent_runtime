# REVIEW-2026-06-09 agent_runtime v0.1.6 agentic knowledge plan

## Bottom Line

`agent_runtime` is being prepared as a reusable agent development team runtime for multiple host projects. The next version should separate runtime-owned skills/hooks/scripts from host-project context overlays, then enforce that separation through context discovery, metadata, CI gates, and eval policy.

## Signal

- Added `AGENTIC_KNOWLEDGE_EVAL_PLAN.md` for TASK-AR-201 through TASK-AR-208.
- Added project overlay templates for context sources, dataset catalog, eval policy, and skill governance.
- Updated backlog/status so the next session can continue without reconstructing the decision trail.
- Release target is local `v0.1.6`; public tag/release remains owner-dependent.

## Insight

The core failure mode is not model quality alone. Accuracy depends on context plus verification. If host projects tune package-owned skills directly, each project forks the runtime behavior and loses upgradeability. Project-specific mission, roadmap, org, data lineage, and trusted-source ranking need to live in the host overlay; runtime-owned skills need contracts, metadata, tests, and CI enforcement.

## Decision

Prioritize TASK-AR-201 and TASK-AR-204 before adding more agent behavior. A router and CI-backed skill/data governance give the runtime a stable extension boundary. Then add offline eval, live reviewer agents, correction collectors, and A2A message contracts.

## Owner-dependent items

- Approve public `v0.1.6` tag/release.
- Decide which host project should become the first real fixture for SSoT/source-tier evaluation.
- Approve any external integration for scheduled correction collection or chat-channel scanning.
