# Agentic Knowledge And Eval Plan

## Bottom Line

`v0.1.6`은 Hold, `v0.1.7`은 미통과 판정 종료, `v0.1.8`은 2026-07-02 후보 판정으로 재설정한다.

- 핵심 전략: 모델 점수보다 **정답 보유 데이터 자체보다 쿼리 정의 + 근거 체인 + 검증 루프**가 안정성의 핵심이다.
- 필수 게이트: 오프라인 90% + reviewer footer + correction collector + A2A trace + 레거시 이식 증빙
- 다음 공개 판정 창: `2026-07-02`, `2026-07-09`, `2026-07-16`

## Source Research

- Anthropic (Claude): test and evaluate / MCP
  - https://docs.anthropic.com/en/docs/mcp
  - https://docs.anthropic.com/en/docs/test-and-evaluate/define-success
  - https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool
- OpenAI:
  - https://platform.openai.com/docs/guides/agent-evals
  - https://platform.openai.com/docs/guides/agent-builder-safety
  - https://platform.openai.com/docs/guides/trace-grading
  - https://platform.openai.com/docs/guides/evaluation-best-practices
  - https://openai.github.io/openai-agents-python/tracing/
- OpenAI Deployment/Governance mirror:
  - https://developers.openai.com/api/docs/guides/agent-evals
  - https://developers.openai.com/api/docs/guides/evaluation-best-practices
- OpenAI 안전/운영/실무 가이드:
  - https://openai.com/index/running-codex-safely/
  - https://help.openai.com/en/articles/11369540-codex-in-chatgpt
  - https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
  - https://help.openai.com/en/articles/20001062-elevated-risk-labels
- A2A/상호운용성:
  - https://github.com/google-a2a/A2A
  - https://a2a-protocol.org/latest/
- Anthropic security (Claude Code):
  - https://code.claude.com/docs/en/security
  - https://www.anthropic.com/engineering/claude-code-best-practices
  - https://docs.anthropic.com/en/docs/claude-code/cli-usage
  - https://docs.anthropic.com/en/docs/claude-code/getting-started
  - https://code.claude.com/docs/en/hooks-guide

### 공식 정합 정리(2026-06-09 기준)

- Hook/permission 조합: Claude 측 hook 명세는 동일 이벤트의 `deny`가 다른 훅의 `allow`를 덮고, 여러 hook가 병렬 실행되어 처리 후 결정 규칙을 합성한다(deny > ask > allow).
- MCP는 데이터/툴/워크플로우를 외부 시스템에 연결하는 표준을 지향하고, 멀티 툴 오케스트레이션의 기반 연결점으로 사용한다.
- OpenAI Trace-grading은 결정 경로+도구 호출+추론 이력(trace) 기반의 구조적 라벨/점수화로 실패 원인 진단을 설계한다.
- OpenAI eval 가이드는 task-specific eval를 만들고, 모델 output score 외에 데이터/로그를 결합해 해석해야 하며, 완성도가 낮은 "vibe-based" 운영을 지양한다.
- OpenAI `agent-builder-safety`는 prompt-injection 완화, 고위험 동작 시 승인/리뷰 라우팅, 거버넌스가 부족한 경로 차단을 권고한다.
- Running Codex safely는 샌드박스, 승인 정책, 네트워크/권한 제어, 에이전트 네이티브 telemetry로 보안을 운영한다고 정리한다.
- Agents SDK tracing에서는 tool call/guardrail/handoff/span을 추적으로 남기고, 실행 종료 전 flush 정책으로 로그 손실을 줄인다.
- A2A 규격은 `contextId`/`taskId`의 지속성과 `input-required`/상태 전이 표현으로 멀티 턴 협업의 재개성과 재시도를 정합한다.

### 공식 연구 반영(정렬 강화, 2026-06-20 기준)

- 최신 공식 리서치(직접 점검): OpenAI trace-grading은 에이전트 trace(결정/도구호출/추론 이력)에 구조적 점수·라벨을 부여해
  `왜 실패했는지`를 추적하는 방식으로 성능/품질 개선 루프를 권고한다.
- Claude/Claude Code Hook 가이드는 hook 실행 후 `deny`/`ask`/`allow` 우선순위를 설명하며,
  `deny`가 강제되어도 다른 hook의 허용 시그널을 덮어쓰지 못하도록 설계되어야 한다고 한다(deny 우선).
- A2A 공식 스펙은 `contextId`/`taskId` 기반 다중 턴 일관성, 상태 전이, 이벤트 순서 보존을 요구하며,
  추적 가능한 메시지 단위의 연속성을 가드키로 전제한다.

- `Running Codex safely`는 샌드박스 경계, 승인 정책, 네트워크 제한, 에이전트 네이티브 감사 로그를 판정 운영의 기본값으로 둔다.
- Trace 단위 평가(`trace-grading`)는 재현 가능한 라벨/점수와 함께 "왜 실패했는지" 추적을 목표로 한다.
- Agent 평가(`agent-evals`)는 워크플로 디버깅 초기 단계에서 trace가 가장 빠른 실패 지점 탐색 수단이라고 명시한다.
- Agents SDK tracing은 tool call/guardrail/handoff까지 기본 span으로 남겨 A2A 재구성성을 확보한다.
- Anthropic eval tool 문서는 task/trial/grader/trace 구성으로 다중 실행 시 정합을 맞추는 방식이다.
- A2A 규격은 독립 에이전트 간 과업 전달과 결정 재개를 상태 메시지로 구조화해, 멀티 에이전트 협업에서 감사성과 복구력을 높인다.
- A2A 3.3/3.4는 taskId + contextId로 멀티턴 연속성/재시도 가능한 상태 전환을 강제해 메시지 중복·단절 리스크를 줄인다.
- OpenAI 가이드는 에이전트 복잡도 증가를 수치적 근거로 정당화하고, 계속 평가(continuous eval) 루프를 기본 운영에 넣을 것을 권고한다.
- Codex 안전 가이드는 샌드박스+승인경계+OpenTelemetry 감사 로그를 함께 운영해야 신뢰도 있는 상용 운영이 가능하다고 본다.
- Claude Hook 가이드는 이벤트별 훅이 모두 실행된 뒤 정책을 집계하고, deny > ask > allow 우선순위로 의사결정한다.

### 운영 권고 반영 (공식 문서 기준)

- 공식 문서는 단일 점수보다 `재현성 + 근거 + 허가경계`를 반복 운영의 핵심으로 둔다.
- 다중 에이전트에서는 trace/감사 로그의 연결성 및 HITL(사람 승인)이 릴리스 품질을 좌우한다.
- 민감/고위험 단계에서는 도구 승인 경계와 허용 목록(allowlist), 위험 레이블을 함께 운영해야 한다.
- trace는 `왜`, `무엇이`, `누가 승인`했는지를 함께 남기는 방식으로 운영해야 멀티 프로젝트 이관/감사 대응이 가능하다.

### External Research Note (2026-06-09 업데이트)

- 최근 공개 가이드는 trace-grading/agent eval를 중심으로 “왜 실패했는지”를 추적할 수 있는 근거를 요구한다.
- OpenAI/Anthropic 가이드는 “모델 자체 성능”보다 query contract, trust source 우선순위, guardrail 및 로그 강제화를 우선.
- Codex 운영 권고는 “문서 + 로그 + 승인 루트”의 세 축이 없으면 배포 신뢰가 약화된다고 본다.
- 실험으로만 쓰는 평가보다 실제 사용자 플로우와 reviewer 피드백을 묶는 구조가 장기 신뢰를 만든다.
- 결론: v0.1.8 판정은 다음 4층 게이트가 모두 번들로 남을 때만 통과.
  - query contract
  - offline 90% dataset
  - live reviewer/footer
  - correction + A2A + migration-map 근거
- A2A 관점에서는 과업 의사결정 재현을 위해 `decision_cycle_id`, `trace_id`, `idempotency` 같은 상태키를
  판정 산출과 결합할 것을 권고.

### 최신 공식/연구 반영(2026-06-09~)

- OpenAI 운영 가이드(Trace grading)는 에이전트 품질 검증을 trace 단위로 구조화해, "왜 실패했는지" 추적이 가능한 라벨/평점 기반 검증을 권고한다.
- OpenAI `agent-builder-safety`는 고위험 단계에서 승인 또는 휴먼 리뷰를 넣고, 허가 경계와 거버넌스가 없는 고위험 흐름은 제한해야 한다는 방향을 반복한다.
- OpenAI 공개 가이드(`Running Codex safely`)는 네트워크 및 작업 권한을 제한하고, 낮은 위험은 마찰을 줄이되 높은 위험은 명시적 리뷰로 전환하는 운영 패턴을 보여준다.
- Claude/Anthropic 가이드는 `명확한 성공 기준 + task-specific eval + edge case` 설계 후 eval을 확장하고, 평가 신뢰를 위해 LLM 채점보다 코드 기반 채점 우선을 우선순위로 둔다.
- Claude Code 보안 가이드는 기본 read-only + 명시적 승인 기반, sandboxing, 명령어 allowlist, 네트워크 제어, 감사 로그를 기본으로 제시한다.
- A2A 프로토콜/체계는 에이전트 간 메시지 계약과 재시도 복구 체계를 통해 멀티 프로젝트 오퍼레이션의 추적성 확보에 직접 기여한다.

### v0.1.8 버전 업데이트 실행 규칙(공식 반영)

- 목표일: 2026-07-02(1차), 2026-07-09(2차 보완), 2026-07-16(최종 freeze).
- 판정 1차 통과 시:
  - `TASK-AR-221` 완료 조건 충족 증적이 `TASK-AR-210`에 연결됨
  - `TASK-AR-219`/`TASK-AR-220`/`TASK-AR-217` 번들이 `release-preflight` 번들에 수렴
  - Owner 승인 전 `publish-bundle`/`publish-tag-smoke`/`release-preflight`의 최신 증적을 갱신
- 판정 2차/3차 미통과 시:
  - 공통 `release-state`는 `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`로 분리
  - HOLD 원인과 재작업 항목은 `TASK-AR-216`로 이관해 1:1 추적
- 배포 실행 전 조건: 공식 문서/리뷰/연구 증빙 문구가 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에 동일

## 원칙

- 정확도 = 맥심맥락(context) + 검증(validation) / 모델 스코어는 보조 신호일 뿐.
- 질문의 정답은 코드처럼 증명되지 않는다. `question / business_scope / time_window / tolerance / ambiguity_level / source_tier`가 먼저 정렬되어야 함.
- 강제되지 않은 규칙은 누적되면 무력화된다. `warn`는 기록, `block`은 종료 조건.
- SSoT는 한 개 레이어가 아닌 신뢰 순위 체인으로 관리: certified semantic layer → lineage → history → context knowledge.
- 메타데이터는 필수: `owner`, `lineage`, `freshness_sla`, `access_level`, `confidence`, `source_tier`, `tradeoff`.
- 멀티 프로젝트는 런타임 코어 재작성보다 오버레이(`vision/roadmap/org/links/team/communication`) 정합으로 해결.

## 요구사항 반영 매핑 (1~16 + 통합)

1. 지식 스킬 최상위 라우터: `TASK-AR-201`, `TASK-AR-214`
2. runbook(명확화/탐색/실행/적대적검토/검증/기록): `TASK-AR-202`
3. 창고 문서 템플릿: `TASK-AR-203`, `SKILL-GOVERNANCE.md`
4. 스킬 문서 동기화/CI 강제: `TASK-AR-204`
5. 오프라인 90% 게이트: `TASK-AR-205`
6. 실시간 reviewer + footer: `TASK-AR-206`
7. 자동 교정 수집: `TASK-AR-207`
8. 정의 책임은 사람: `TASK-AR-201`, `TASK-AR-214`
9. 강제 규칙: `TASK-AR-204`, `TASK-AR-210`
10. 질의 정제/오해 처리: `TASK-AR-214`, `TASK-AR-202`
11. SSoT 정렬: `CONTEXT-SOURCES.yml`, `DATASET-CATALOG.yml`
12. 정확도-속도-비용 트레이드오프: `TASK-AR-205`, `TASK-AR-206`, `TASK-AR-207`
13. 메타데이터 고정: `CONTEXT-SOURCES.yml`, `SKILL-DATA-MAP.yml`
14. 팀/로드맵/조직 연결: `TASK-AR-215`, `TASK-AR-211`, `ROADMAP.md`
15. 멀티 프로젝트 오버레이 구조: `TASK-AR-211`, `TASK-AR-215`
16. A2A 메시지 버스: `TASK-AR-208`
17. 공식 가이드 반영: `TASK-AR-219`
18. 레거시 이식 근거: `TASK-AR-220`
19. 전체 통합 오케스트레이션: `TASK-AR-221`
20. v0.1.8 closeout 번들 정합: `TASK-AR-222`
21. closeout 통합과 hold/판정 템플릿 정합: `TASK-AR-223`
22. A2A/멀티 프로젝트 추적성: `TASK-AR-208`, `TASK-AR-223`

## Target Architecture

```text
User request
  -> knowledge-router (source_tier + ambiguity + owner routing)
  -> query contract resolver (scope/time_window/tolerance/tradeoff)
  -> context-source resolver (ranked SSoT: semantic layer → lineage → history → context knowledge)
  -> runbook (clarify -> search -> execute -> adversarial review -> verify -> record)
  -> offline/online verifier and correction collector
  -> A2A trace reconstruction
  -> source footer + tags + reviewer verdict
  -> owner/team approval routing
  -> release evidence bundle
```

## RSI Planning Loop / Trace-Eval-Grader Integration

`TASK-AR-234`~`TASK-AR-245`는 기존 eval/correction/A2A 체인을 planning loop의 입력으로 승격한다.

- `trace`: agent run의 model/tool/guardrail/handoff 흐름을 planning evidence로 저장한다.
- `grader`: trace 또는 output의 실패 유형을 구조화해 proposal category와 acceptance criteria로 변환한다.
- `eval`: 반복 가능한 dataset/run 결과를 release readiness뿐 아니라 future task 생성 근거로 사용한다.
- `correction`: live reviewer와 correction collector 결과를 retro/compound synthesizer가 읽어 재발 방지 task로 제안한다.
- `A2A`: `contextId`/`taskId`를 proposal lineage와 follow-up task 연결 키로 사용한다.
- `task_claim`: 병렬 worker의 `task_id`/`agent_instance_id`/`callsite_id`/worktree/branch/handoff/log를 묶어 실행 충돌과 세션 중단을 감지한다.

### RSI Task Mapping

| Task | Eval/trace role | Output |
| --- | --- | --- |
| `TASK-AR-234` | Defines planning state/proposal schema | B/C boundary and state machine |
| `TASK-AR-235` | Reads eval/review/release evidence | Read-only planning scan JSON |
| `TASK-AR-236` | Converts evidence into proposals | Proposal outbox and draft task writer |
| `TASK-AR-240` | Checks release/version drift | Version/release consistency report |
| `TASK-AR-241` | Reads history/compound/retro | Preventive task proposals |
| `TASK-AR-243` | Normalizes trace/eval/grader inputs | Evidence-linked planning proposals |
| `TASK-AR-244` | Blocks unstable recursion | Non-divergence guardrails |
| `TASK-AR-245` | Promotes/demotes C-mode | C-mode gate and rollback rules |
| `TASK-AR-246` | Separates parallel execution state | Worktree claim dispatcher and resume pointers |

### Promotion Rule

- B-mode may scan and propose autonomously.
- C-mode may auto-apply only low-risk planning hygiene after repeated passing cycles.
- C-mode is blocked until version/release consistency, trace/eval/grader integration, and non-divergence guardrails pass together.
- Any proposal that weakens gates, mutates release/version state, performs external publication, touches secrets/prod data, or performs destructive actions remains owner-required.

## Task Plan

### TASK-AR-221 운영 정합 통합(권고 반영 묶음)

- 목표: 요구사항 1~16을 하나의 릴리스 게이트 체인으로 묶어, v0.1.8 판정 루프에서 누락 없이 검증.
- 산출:
  - 판정 날짜(07-02/07-09/07-16)와 실행 로그 정합 룰셋
  - `query contract` 미충족/오버레이 누락/migration 결손 보류 경로 일치표
  - 스킬 문서 동기화 및 migration 근거 추적 규칙
- 완료 조건:
  - v0.1.8 판정 일자 문구가 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에 동일
  - `TASK-AR-219`~`TASK-AR-220` 증빙이 동일 감사 번들에 수렴

### TASK-AR-219 공식 가이드 정합과 v0.1.8 판정 근거 고정

- 목적: Claude/Codex/OpenAI 권고를 release readiness 템플릿에 정식 반영한다.
- 산출:
  - `release_state`/`decision_deadline`/`decision_template` 표준안
  - v0.1.8 판정 번들 구성(오프라인 90%, reviewer footer, correction, A2A trace, release-preflight 링크)
  - 공식 가이드 반영 항목 체크리스트
- 완료 조건:
  - `2026-07-02`/`07-09`/`07-16` 판정 문구가 핵심 문서에 동일
  - `TASK-AR-216`/`TASK-AR-217` 결과가 `TASK-AR-219` 증거 번들에 합치
  - 공식 가이드 반영 항목이 실제 release evidence와 추적 가능하게 연결

### TASK-AR-220 이식 근거 분리 및 보존

- 목적: 레거시 전신 프로젝트의 skill/hook/script 이식 차이를 source/run-time/provenance 단위로 영구 추적한다.
- 산출:
  - 레거시 감사 스냅샷 근거 정합 강화
  - 누락/의도적 제외의 보류 사유와 승인 경로 템플릿
  - `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210` 연동 증적
- 완료 조건:
  - `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper` 미정이 적어도 하나의 분류군으로 정렬
  - 승인 누락 항목은 `hold_for_data` 또는 `hold_for_overlay`로 즉시 이관
  - 코어/오버레이에서 동일 사유 링크로 재조회 가능

### TASK-AR-222 Closeout Bundle And Cross-Project Version Readiness

- 목적: 요구사항 1~16 + 공식 가이드 + 레거시 이식 근거를 v0.1.8 판정 번들 하나로 마감.
- 산출:
  - `TASK-AR-221` 실행 증적과 `TASK-AR-219` 공식 가이드 항목의 1:1 추적표
  - migration 누락/변경/의도적 제외 근거와 hold 경로 매핑표
  - `offline evaluator`, `reviewer footer`, `correction collector`, `A2A trace`가 하나의 audit bundle로 묶인 증적
  - 오버레이 변경 최소화 시나리오(vision/roadmap/org/links/team/communication) 2건 실행 기록
- 완료 조건:
  - `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210` 판정 문구 완전 정합
  - `TASK-AR-220` 미완 항목이 `TASK-AR-204` 또는 `TASK-AR-213`/`TASK-AR-210`으로 즉시 이관
  - `TASK-AR-205`에서 domain별 90% 미달 항목이 traceable correction으로 남고 재검증 예약됨
  - `TASK-AR-206`/`TASK-AR-207`/`TASK-AR-208` 결과가 `release-preflight` 번들에 남아 재현 가능
  - `TASK-AR-222` 작업 산출(산출물, 결정 로그, 교차 링크)이 `reviews/MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan.md`에 정리

### TASK-AR-223 Multi-Project Version Closeout Integration

- 목적: 1~16 + 공식 권고 + migration 근거 + 오버레이 연결을 `TASK-AR-223` 단일 closeout bundle로 수렴.
- 산출:
  - 판정 템플릿(1차/2차/최종)과 hold 라우팅(`hold_for_query_contract`/`hold_for_overlay`/`hold_for_data`)의 일치 규칙
  - `TASK-AR-204` 강제 규칙이 미반영 시 block로 동작하는 감사 증적
  - 레거시 감사 스냅샷 미완 항목이 `TASK-AR-204`/`TASK-AR-213`/`TASK-AR-210`으로 즉시 이관되는 근거 체인
  - 오버레이 변경만으로 프로젝트 투입하는 멀티 프로젝트 시뮬레이션 결과 1건 이상
- 완료 조건:
  - 오프라인 90% + reviewer footer + correction collector + A2A trace + migration 근거가 같은 번들 내 재현
  - 2026-07-02/07-09/07-16 판정 문구가 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에 동일
  - `TASK-AR-221`~`TASK-AR-222`/`TASK-AR-219`/`TASK-AR-220`이 `TASK-AR-223` closeout 증적으로 1:1 추적
  - 미완 항목은 미해결 건당 `owner/block_reason/decision_deadline`이 남아야 함

### TASK-AR-224 Official And Migration Source-Control Gate

- 목표: 공식 근거와 레거시 이식 근거를 v0.1.8 closeout 번들에 선행 결합.
- 현재 상태: `in_progress`
- 완료 조건:
  - 공식 근거 링크가 research/meeting/call/seminar cycle에 남음
  - `scripts-source-only` 53건이 레거시 hold routing 스냅샷에서 세부 이유군으로 분리됨
  - migration hold routing table이 `TASK-AR-223` closeout 번들로 이관됨
  - `RELEASE-GATE-TEMPLATE.yml` required fields가 `TASK-AR-210`과 정합
  - executable packet proof와 release-preflight proof가 review로 남음
  - warn-only 판정 경로가 남지 않음

### TASK-AR-216 Release Transition and v0.1.8 Gate Freeze

- 목적: v0.1.7 미통과 항목을 v0.1.8 판정 이관 상태로 정합.
- 완료 조건:
  - `release-state`/`request_for_v0.1.8`/`decision_deadline` 필드가 `TASK-AR-210` 규칙과 정합
  - 미해결 항목을 `hold_for_*`로 이관하고 Owner/blocked_by가 비어 있지 않음

### TASK-AR-217 Release Rehearsal For Public Readiness

- 목표: 오프라인 90% + live reviewer + correction collector + A2A를 한 번의 rehearsal bundle로 검증.
- 완료 조건:
  - `release-preflight --source .` / `--source .tmp/release-bundle --check` 증적
- 실패시: `rehearsal-block` 및 `BACKLOG` 재이관 로그 남김

### TASK-AR-201 Knowledge Skill Router

- 목표: 질문 정합을 route-level로 고정하고 오버레이 누락을 high-risk 처리.
- 완료 조건: 필수 메타 누락 시 `TASK-AR-204` 이관

### TASK-AR-202 Runbook Skill Contract

- 목표: 베테랑 프로세스(명확화-탐색-실행-적대적검토-검증-기록) 표준화
- 완료 조건: 패턴 라이브러리 재사용이 증빙되어야 함

### TASK-AR-203 Warehouse Document Standard

- 목표: 창고 문서의 빠른 참조형 템플릿 정착
- 완료 조건: 5개 필수 항목 포함 + stale/staleness 경고

### TASK-AR-204 Skill/Data Co-Location And CI Enforcement

- 목표: 모델/provider/data 변경 시 `SKILL-DATA-MAP.yml` 변경 동기화 실패가 release-block
- 완료 조건: same-dir 관리 정책 + `warn→block` 정책 적용

### TASK-AR-205 Offline Eval Gate

- 목표: 도메인별 골든셋 정량평가
- 완료 조건: 도메인별 정확도 90% 미달 시 block

### TASK-AR-206 Live Verification And Adversarial Review

- 목표: 고위험 요청은 reviewer 및 footer 강제
- 완료 조건: 답변 footer + reviewer verdict 필수

### TASK-AR-207 Auto-Correction Collector

- 목표: 정기 스캐너 기반 correction 이벤트 생성
- 완료 조건: 오답/누락 패턴이 correction으로 생성

### TASK-AR-208 A2A Message Bus Hardening

- 목표: chain reconstruct 가능한 메시지 체인 정합
- 완료 조건: envelope/retry/access control/idempotency 운영

### TASK-AR-211 Project Overlay Contract

- 목표: 오버레이만 바꾸어 프로젝트별 투입
- 완료 조건: 최소 2개 시나리오에서 오버레이 교체만으로 동작

### TASK-AR-212 Migration Evidence Closure

- 목표: migration 분류 결과와 릴리스 블로커를 연결
- 완료 조건: owner/rationale/approval 비어 있는 항목 block

### TASK-AR-213 Migration Parity Lock

- 목표: skill/hook/script 이식 차이를 최종 상태로 정렬
- 완료 조건: 의도적 제외/누락은 근거 없으면 block

### TASK-AR-214 Query Contract

- 목표: 질문 계약을 메타로 고정
- 완료 조건: 필수 필드 미입력 시 clarify/reviewer_review 라우팅

### TASK-AR-215 Overlay Packet

- 목표: 팀/조직/로드맵 문맥을 런타임 라우팅에 반영
- 완료 조건: context packet 누락 시 hold_for_overlay

## Execution Order (Next Cycle)

1. `TASK-AR-224` (공식/이식 근거 동기화 선행)
2. `TASK-AR-221` (운영 정합 통합)
3. `TASK-AR-219` (공식 가이드 반영/판정 문구 고정)
4. `TASK-AR-220` (이식 근거 마감)
5. `TASK-AR-222` (closeout bundle 정합)
6. `TASK-AR-223` (closeout 통합 및 hold/routing 정합)
7. `TASK-AR-216` (release-state 이관)
8. `TASK-AR-218` (migration-map 승인 정합)
9. `TASK-AR-217` (release rehearsal)
10. `TASK-AR-214` (질의 계약 고정)
11. `TASK-AR-215` (오버레이 패킷 고정)
12. `TASK-AR-210` (버전 gate 최종)
13. `TASK-AR-204` (동기화 block)
14. `TASK-AR-213` (migration lock)
15. `TASK-AR-209` (이식 감사 정렬)
16. `TASK-AR-212` (증빙 클로징)
17. `TASK-AR-201` (라우터)
18. `TASK-AR-202`/`TASK-AR-203` (runbook/warehouse)
19. `TASK-AR-205` (오프라인 게이트)
20. `TASK-AR-206` (live reviewer)
21. `TASK-AR-207` (correction)
22. `TASK-AR-208` (A2A)
23. `TASK-AR-246` (parallel worktree/task claim dispatcher)
