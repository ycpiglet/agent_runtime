---
type: retro
id: RETRO-2026-06-14-knowledge-stack
audience: owner
status: watch
signal: watch
score: 80
priority: High
tags: [retro, knowledge-graph, fixture-lock, ci, process, agent-primitive]
recorded_at: 2026-06-14T12:45:00+09:00
---

# RETRO 2026-06-14 — Agent knowledge stack (#1–#4)

## Bottom Line

- Summary: graph/digest/lint/ask 4종을 결정적 우선 + LLM 옵인으로 머지하고 막힌 PR 4건을 풀었다. 잘된 것은 TDD-우선·실레포 스모크·게이트 선검증, 갈린 것은 git-tracked fixture lock의 쌍별 충돌과 cp949/heredoc 같은 환경 메카닉스.
- Boundary: 본 레코드는 프로세스 회고 + 실행 가능한 forward action 등록이다. 점수는 wave 품질 신호이며 채택 주장 아님.

## Signal — What went well

- TDD를 매 서브프로젝트에 적용(테스트 먼저 → 구현). 41건 green을 머지 게이트로 삼음.
- 머지 전 **로컬 검증 표준화**: 거버넌스 게이트 + clean-bundle release-preflight host-lock을 푸시 전 EXIT=0 확인 → 모든 PR이 force-merge 없이 CI green으로 auto-merge.
- 실레포 스모크가 설계 결함을 조기 포착: #3 orphan 노이즈(474→0), #4 cp949 크래시.

## Signal — What hurt

- **fixture lock thrash(systemic)**: lock을 건드리는 PR이 동시 다발일 때 파생 lock이 쌍별 충돌. #135가 #142/#146 머지마다 DIRTY → 3회 재머지·재생성. GitHub은 DIRTY PR에 머지커밋을 못 만들어 `pull_request` CI 자체가 안 돌아 auto-merge가 막히는 2차 효과까지. → COMPOUND-2026-06-14-003.
- **환경 메카닉스 재발**: (a) Bash 툴에서 PowerShell heredoc(`@'...'@`)을 써 커밋 제목에 `@` 누수 → 메시지 파일로 amend; (b) cp949 콘솔이 em-dash 출력에 크래시.
- #1 ingest가 review/meeting/research를 고립 노드로 적재(reference 엣지 미생성) → 실레포 260 reviews 전부 graph-orphan. digest backlink/ask grounding 손실.

## Insight

- 파생 산출물(lock)을 소스처럼 커밋 + 모든 템플릿 PR이 재생성 → 머지 위상에서 필연적 충돌. 단발 재머지로 넘기면 thrash가 숨는다.
- 도구별 셸 문법(Bash vs PowerShell)·플랫폼 인코딩(cp949)을 커맨드 작성 시 비검증하면 재발한다.
- #1 ingest 설계가 work-item topology에 집중, 서술형 레코드의 상호참조 추출 미구현 → review/meeting이 그래프에서 고립.

## Risk

- fixture-lock 자동화(forward #1) 미구현 상태로 다중 템플릿 PR이 동시 진행되면 thrash 재발 — DIRTY→CI 미실행→auto-merge 정지의 침묵 실패 포함.
- forward action 1·2를 task로 등록할 때 분류기/인덱스 재생성이 wave89 미커밋 항목과 충돌할 수 있어 격리 커밋 필요(wave89 closeout 레시피 준수).
- #4 LLM 경로는 CI 미커버 — 실 provider 회귀는 라이브 평가로만 잡힌다.

## Action (executable)

| # | 액션 | 산출물/방법 | 강제 |
| --- | --- | --- | --- |
| 1 | fixture-lock 자동 재생성 | merge/pre-push 훅 또는 CI 단계에서 `agent_runtime lock --write` 후 정합 검사; 또는 derived lock 비커밋(.gitignore+CI 생성) 중 택1 — TASK 등록 | 후속 task |
| 2 | #1 ingest reference 엣지 | review/meeting/research 본문의 `TASK-AR-\d+`/엔티티 id를 `references`로 엣지화 → digest backlink/ask grounding 강화 — TASK 등록 | 후속 task |
| 3 | #5 UI knowledge 뷰 scope 결정 | 최소 read-only(digest/ask 호출) / 전체 그래프 시각화 / task만 등록 중 Owner 택1 | Owner |
| 4 | CLI unicode 안전 | knowledge CLI는 __main__에서 stdout utf-8 재설정(ask 적용 완료); graph/digest/lint도 동일 적용 검토 | 점검 |
| 5 | 셸 문법 가드 | 멀티라인 커밋 메시지는 파일(`-F`)로 — Bash 툴에서 PowerShell heredoc 금지 | 규칙 |
| 6 | #3 lint 거버넌스 편입 | `knowledge_lint check`(block-only)를 owner_governance 비강제 watch 단계로 후보화 | Owner |

## Decision

- Decision: forward action 1·2는 후속 TASK로 등록(본 PR에서는 인덱스/분류기 재생성 회피 — wave89 미커밋 충돌 격리). 등록 부킹은 wave89 closeout 레시피대로 일괄.
- Decision: forward action 5(파일 기반 커밋 메시지)는 즉시 규칙화.
- Decision: #5는 본 wave에서 분리, Owner scope 결정.

## Next

- COMPOUND-003·REVIEW·RETRO를 owner-docs 등재 후 본 closeout PR 머지(CI green auto-merge).
- Owner의 #5 scope 결정 수신 후 진행.
