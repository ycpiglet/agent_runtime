# Agent Runtime

Reusable automation core for repository-based AI agent workflows.

[한국어](#한국어) | [English](#english)

## 한국어

Agent Runtime은 여러 AI 에이전트가 같은 저장소에서 일할 때 필요한
역할, 문서, 게이트, 메시지 큐, 자가개선 루프를 제공하는 런타임 템플릿입니다.

이 README는 사용자와 설치자를 위한 입구입니다. 실제 작업 규칙과 세부 정책은
호스트에 설치되는 `AGENTS.md`, `CLAUDE.md`, `agents/project/`, 그리고
이 저장소의 `src/agent_runtime/templates/project/`를 기준으로 확인하세요.

### 빠른 시작

호스트 프로젝트에서는 이 저장소를 직접 복사하지 말고, 릴리스 태그를 핀한 뒤
`agent_runtime update` 흐름으로 관리 템플릿을 적용합니다.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8"
```

```yaml
# agent_runtime.yml
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.8
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
```

```powershell
.\.venv\Scripts\agent_runtime update-plan --check
.\.venv\Scripts\agent_runtime update --check
.\.venv\Scripts\agent_runtime update --diff
.\.venv\Scripts\agent_runtime update --apply
Copy-Item agents\project\PROJECT-CONTEXT.example.yml agents\project\PROJECT-CONTEXT.yml
```

macOS/Linux에서는 같은 흐름을 `python3`, `. .venv/bin/activate`, `cp`로 실행하면 됩니다.

### 핵심 개념

| 개념 | 설명 |
|---|---|
| Live Work Pointer | `agents/project/NEXT-SESSION-POINTER.yml`와 `agents/runtime/task_claims/*.json`은 온라인 게임 상태판처럼 현재 에이전트, 팀, pane, 작업, 단계, 진행률, worktree, 다음 행동을 계속 남깁니다. |
| Shared Protocol | `AGENTS.md`는 모든 에이전트가 따르는 공통 운영 규칙입니다. |
| Tool Companion | `CLAUDE.md` 같은 도구별 문서는 공통 규칙을 보조하지만 `AGENTS.md`와 충돌하면 공통 규칙이 우선합니다. |
| Project Overlay | 제품 비전, 로드맵, 조직, 링크는 `agents/project/`에 둡니다. 런타임 템플릿에 제품 지식을 직접 섞지 않습니다. |
| Measured Improvement | `Evaluate -> Propose -> Verify -> Merge` 루프로 개선합니다. 고정된 golden set, 실패 사례, 엣지 케이스를 보존합니다. |
| Repeated Request API | 사용자가 같은 요청이나 비판을 반복하면 문장으로만 남기지 말고 함수, API, 스크립트, 훅, 게이트, 태스크로 승격합니다. |
| Compound Capture | 반복 실수는 `agents/lead_engineer/compound_log.md`에 기록하고, 가능하면 실행 가능한 예방책으로 닫습니다. |

### 개발자와 AI가 먼저 읽을 문서

| 필요 | 문서 |
|---|---|
| 현재 작업 상태를 빠르게 재개 | `agents/project/NEXT-SESSION-POINTER.yml`, `agents/runtime/task_claims/*.json` |
| 공통 작업 규칙 | `AGENTS.md` 또는 `src/agent_runtime/templates/project/AGENTS.md` |
| Claude 계열 도구 규칙 | `CLAUDE.md` 또는 `src/agent_runtime/templates/project/CLAUDE.md` |
| 호스트 프로젝트 정체성 | `agents/project/PROJECT-CONTEXT.yml` |
| 역할과 책임 | `agents/roles.yml` |
| 열린 작업과 우선순위 | `agents/lead_engineer/tasks/BACKLOG.md` |
| 현재 운영 상태 | `agents/lead_engineer/STATUS.md` |
| 반복 실수와 개선 기록 | `agents/lead_engineer/compound_log.md` |
| 런타임 템플릿 원본 | `src/agent_runtime/templates/project/` |

### 검증

호스트 적용 후에는 좁은 확인부터 실행합니다.

```powershell
agent_runtime update --check
python scripts/continuity_contract_gate.py --check
python scripts/owner_governance_gate.py
python scripts/check_agent_docs.py
python -m pytest tests -q
```

이 저장소를 공개 릴리스로 준비할 때는 다음 게이트가 기본 기준입니다.

```powershell
PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check
PYTHONPATH=src python -m pytest tests -q
```

### 상태 표현

기계가 읽는 상태값은 `pass`, `watch`, `block`과 `score: 0-100`을 사용합니다.
색상명은 UI 표시 보조로만 허용하고, 의사결정 상태값으로 쓰지 않습니다.

## English

Agent Runtime is a reusable runtime template for AI agents working inside a
repository. It provides shared roles, documents, gates, message queues, and a
measured self-improvement loop.

This README is the friendly entry point for users and installers. Detailed
operating rules live in the host-installed `AGENTS.md`, `CLAUDE.md`,
`agents/project/`, and this repository's `src/agent_runtime/templates/project/`.

### Quick Start

In a host project, do not copy files by hand. Pin a release tag and apply the
managed templates through `agent_runtime update`.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.1.8"
```

```yaml
# agent_runtime.yml
project: my-project
upstream:
  package: agent_runtime
  remote_url: https://github.com/ycpiglet/agent_runtime.git
  ref: v0.1.8
sync:
  mode: check-diff-apply
  allow_silent_overwrite: false
```

```bash
agent_runtime update-plan --check
agent_runtime update --check
agent_runtime update --diff
agent_runtime update --apply
cp agents/project/PROJECT-CONTEXT.example.yml agents/project/PROJECT-CONTEXT.yml
```

### Core Concepts

| Concept | Meaning |
|---|---|
| Live Work Pointer | `agents/project/NEXT-SESSION-POINTER.yml` and `agents/runtime/task_claims/*.json` act like an online-game state board for active agents, teams, panes, tasks, phases, progress, worktrees, and next actions. |
| Shared Protocol | `AGENTS.md` is the common operating contract for all agents. |
| Tool Companion | Tool-specific files such as `CLAUDE.md` may add guidance, but `AGENTS.md` wins on conflict. |
| Project Overlay | Product identity, roadmap, organization, and links belong in `agents/project/`, not in reusable runtime templates. |
| Measured Improvement | Improve through `Evaluate -> Propose -> Verify -> Merge`, with a fixed golden set, failure notes, and edge cases. |
| Repeated Request API | Repeated user requests or criticism must be promoted into a function, API, script, hook, gate, or explicit task proposal. |
| Compound Capture | Repeated mistakes go into `agents/lead_engineer/compound_log.md` and should close with executable prevention when feasible. |

### Read This First

| Need | Document |
|---|---|
| Resume current work state | `agents/project/NEXT-SESSION-POINTER.yml`, `agents/runtime/task_claims/*.json` |
| Shared agent rules | `AGENTS.md` or `src/agent_runtime/templates/project/AGENTS.md` |
| Claude-specific guidance | `CLAUDE.md` or `src/agent_runtime/templates/project/CLAUDE.md` |
| Host project identity | `agents/project/PROJECT-CONTEXT.yml` |
| Roles and responsibilities | `agents/roles.yml` |
| Open work | `agents/lead_engineer/tasks/BACKLOG.md` |
| Current operating status | `agents/lead_engineer/STATUS.md` |
| Recurring mistakes and improvements | `agents/lead_engineer/compound_log.md` |
| Runtime template source | `src/agent_runtime/templates/project/` |

### Verification

After applying templates in a host project, run the narrow checks first.

```bash
agent_runtime update --check
python scripts/continuity_contract_gate.py --check
python scripts/owner_governance_gate.py
python scripts/check_agent_docs.py
python -m pytest tests -q
```

For public release preparation from this source repository:

```bash
PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-check --root . --check
PYTHONPATH=src python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check
PYTHONPATH=src python -m pytest tests -q
```

### Status Language

Machine-readable state uses `pass`, `watch`, `block`, plus `score: 0-100`.
Color labels may be visual hints only; they are not decision-state values.
