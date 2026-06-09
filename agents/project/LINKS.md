# Links (Host Overlay)

## Canonical References

- policy_docs:
  - agents/project/README.md
  - agents/project/SKILL-GOVERNANCE.md
  - agents/project/SKILL-DATA-MAP.yml
  - agents/project/DATASET-CATALOG.yml
- decision_logs:
  - STATUS.md
  - BACKLOG.md
  - agents/lead_engineer/tasks/TASK-AR-210.md
  - agents/lead_engineer/tasks/TASK-AR-216.md
  - agents/lead_engineer/tasks/TASK-AR-217.md
  - agents/lead_engineer/tasks/TASK-AR-218.md
  - agents/lead_engineer/tasks/TASK-AR-219.md
  - agents/lead_engineer/tasks/TASK-AR-221.md
  - agents/lead_engineer/tasks/TASK-AR-220.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-214-owner-sync.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-215-context-packet-sync-call.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-215-cross-project-overlay.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-plan.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md
  - reviews/MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning.md
  - reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md
  - reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync.md
  - reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md
- architecture_refs:
  - src/agent_runtime/templates/project/scripts/agent_context_packet.py
  - src/agent_runtime/templates/project/agents/project/CONTEXT-SOURCES.example.yml
  - src/agent_runtime/templates/project/agents/project/SKILL-DATA-MAP.example.yml

## Cross-Team Links

- owning_team: agent-runtime-core
- mcp_endpoints:
  - src/agent_runtime/cli.py
  - src/agent_runtime/publish_check.py
- communication_channels:
  - reviews/
  - agents/lead_engineer/tasks/
  - agents/project/corrections/

## Repository/Issue References

- task_index: agents/lead_engineer/tasks/INDEX.md
- sprint_folder: agents/lead_engineer/tasks
- review_folder: agents/lead_engineer/reviews
- eval_set_folder: agents/project/evals

## Official Guidance References

- https://docs.anthropic.com/en/docs/test-and-evaluate/define-success
- https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool
- https://docs.anthropic.com/en/docs/mcp
- https://platform.openai.com/docs/guides/agent-builder-safety
- https://platform.openai.com/docs/guides/trace-grading
- https://platform.openai.com/docs/guides/agent-evals
- https://platform.openai.com/docs/guides/evaluation-best-practices
- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-js/guides/tracing
- https://openai.com/index/running-codex-safely/
- https://github.com/google-a2a/A2A
- https://a2a-protocol.org/latest/
- https://code.claude.com/docs/en/security
- https://code.claude.com/docs/en/hooks-guide
- https://www.anthropic.com/engineering/claude-code-best-practices

## Cross-Project Overlay Simulation Approval Log

- simulation: agents/project/overlays/simulations/mvp-client-2026-06-09/context-packet-simulation.json
- gate: scripts/overlay_simulation_gate.py
- report: reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json
- approved_by: lead-engineer
- decision_date: 2026-06-09
- expiry: 2026-07-16
- justification: Project-specific vision, roadmap, organization, team, links, and communication context are represented as overlay files; shared runtime core edits are not required.
- hold_route: missing overlay dimensions must route to hold_for_overlay through TASK-AR-204 and TASK-AR-216.
