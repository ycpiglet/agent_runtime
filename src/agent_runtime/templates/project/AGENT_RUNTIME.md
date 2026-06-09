# AGENT_RUNTIME.md

Runtime model for the repository's local agent automation.

## Mental Model

```text
Agent        = role identity + state + inbox contract
Worker       = running process that handles one role
Provider     = LLM or deterministic backend used by a worker
Message      = file-based work or coordination packet
Event        = append-only runtime record
Pane         = optional observer view, not the source of truth
Orchestrator = command layer that routes work and starts workers
Context      = host-owned project overlay under agents/project/
```

A terminal pane is only a view. The durable state lives in files, task records,
and event logs.

## Flow

```text
User or CEO instruction
  -> orchestrator
  -> project context overlay
  -> message/task store
  -> role worker
  -> provider adapter
  -> reply, record, event log
  -> observer pane or report
```

## Worker Loop

A role worker should:

1. load its role configuration
2. poll or watch the inbox
3. claim one open message
4. call its provider
5. write a reply or result
6. update message status
7. append runtime events
8. continue until stopped

## Boundaries

- Do not treat interactive panes as autonomous agents.
- Do not assume a provider is available unless configured.
- Do not write secrets to messages, events, reports, or logs.
- Do not let runtime artifacts become public release content.
- Prefer deterministic local checks before expensive model calls.
- Do not encode project-specific product behavior in upstream SKILL.md files.
- Put host vision, roadmap, organization, and link maps under `agents/project/`.
- Automate branch, commit, PR, and merge for routine R1/R2 work when checks pass.
- Escalate only critical release boundaries to Owner; routine patch/minor
  release decisions can be made by the agent release council.
- Reports and plans should use concise Executive BRIEF structure with
  frontmatter, tags, action summaries, evidence links, and clear visual tables.

## Autonomous Delivery

```text
Task or direct user request
  -> branch
  -> scoped commit
  -> focused checks
  -> PR/review agents
  -> merge gate
  -> record evidence
```

Agents should ask for Owner approval only when a critical boundary is present:
secrets, production data, legal/billing, destructive actions, failed critical
gates, untrusted external publication, force push, or major/breaking release.

## Release Council

```text
Release candidate
  -> Lead Engineer scope check
  -> QA validation check
  -> Independent Auditor risk check
  -> Doc Steward report/handoff check
  -> release decision gate
  -> execution evidence
```

The council may approve routine patch/minor releases when gates pass. Owner
approval remains mandatory for critical releases.

## Common Commands

```powershell
python scripts/agent_orchestrator.py --help
python scripts/agent_worker.py --help
python scripts/agent_observer.py --help
python scripts/check_messages.py
```

If a command is unavailable in this host project, check the installed
`agent_runtime` template version and run the repository sync plan.
