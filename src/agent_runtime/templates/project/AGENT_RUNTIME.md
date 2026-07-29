# AGENT_RUNTIME.md

Runtime model for the repository's local agent automation.

## 한국어

이 문서는 설치된 Agent Runtime이 직접 관리하는 공통 계약이다. 프로젝트가
`AGENTS.md`와 `CLAUDE.md`를 호스트 소유로 유지하더라도
`agents/project/NEXT-SESSION-POINTER.yml`의 `active_work`, `pane_id`,
`progress_pct`를 갱신하고 `agents/project/`에 근거를 남긴다.

반복 요청은 Repeated Request API 원칙에 따라 function/API, 스크립트 또는
게이트로 승격한다. 반복 실수와 비판은 Compound에 자동·필수로 기록하고,
실패 사례와 edge case를 golden set으로 보존한다. 개선은
Evaluate -> Propose -> Verify -> Merge 순서를 따르며 최종 기준과 병합 권한은
Owner에게 있다.

## English

This is the managed common contract for an installed Agent Runtime. A project
may keep `AGENTS.md` and `CLAUDE.md` host-owned, but it must maintain
`agents/project/NEXT-SESSION-POINTER.yml`, including `active_work`, `pane_id`,
and `progress_pct`, and preserve evidence under `agents/project/`.

The Repeated Request API promotes repetition into a function/API, script, or
gate. Compound capture is automatic and mandatory for repeated mistakes and
criticism. Preserve failures and edge cases as a golden set. Improvement
follows Evaluate -> Propose -> Verify -> Merge, while Owner retains final
criteria and merge authority.

## Portable Continuity Contract

- The pointer schema and required fields remain mandatory in every project.
- Host-owned documents are never rewritten merely to satisfy Runtime wording.
- Managed Runtime contracts must match the installed v2 lock.
- Missing or inconsistent configuration, lock, ownership, contract, or pointer
  evidence fails closed.

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
