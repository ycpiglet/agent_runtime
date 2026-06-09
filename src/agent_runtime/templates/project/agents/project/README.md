# Project Context Overlay

This directory is the host-owned place for product context.

Agent Runtime owns the reusable runtime files:

- `agents/*/SKILL.md`
- `agents/roles.yml`
- `scripts/*`
- `AGENTS.md`
- `AGENT_RUNTIME.md`

Host projects should not tune those files for product-specific behavior. Put
project identity, vision, roadmap, organization, decisions, and external links
here instead, then let context packets attach these files to every role.

## Recommended Files

- `PROJECT-CONTEXT.yml`: compact machine-readable project map.
- `CONTEXT-SOURCES.yml`: ranked sources of truth, metadata owners, access rules.
- `DATASET-CATALOG.yml`: eval datasets, gold labels, lineage, and quality gates.
- `EVAL-POLICY.yml`: offline and live validation thresholds.
- `SKILL-GOVERNANCE.md`: host skill/router/runbook rules and CI expectations.
- `VISION.md`: product vision, user, problem, scope, and non-goals.
- `ROADMAP.md`: phases, milestones, current MVP slice, release plan.
- `ORG.md`: owner, decision makers, agent team mapping, escalation rules.
- `TEAMS.md`: human and agent teams, roles, responsibilities, handoffs.
- `LINKS.md`: canonical external references and documents.
- `teams/{team-id}.md`: optional team-specific operating context.

Use `PROJECT-CONTEXT.example.yml` as the starter. The example file is managed by
Agent Runtime; copy its structure into `PROJECT-CONTEXT.yml` for host-owned
content.

Use the other `*.example.yml` files the same way: keep the examples managed, and
write project-owned copies without `.example` in the filename.

## Rule

Project-specific behavior changes through this overlay, not by editing upstream
runtime skills. If a host needs a different skill contract, create a host note
under `agents/project/` and reference it from the task or context packet.
