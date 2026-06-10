# Roadmap (Host Overlay)

## Current Phase

- phase: v0.1.8 local release evidence closed + remote publish scoped out of TASK-AR-210
- next_milestone: TASK-AR-240 version/release consistency steward -> TASK-AR-223 closeout integration -> TASK-AR-234 RSI planning loop contract -> TASK-AR-235 read-only planning scan
- target_date: 2026-07-02(1차), 2026-07-09(2차), 2026-07-16(최종)
- owner: lead-engineer

## Milestones

 - [x] 2026-06-10: `TASK-AR-221`/`TASK-AR-219`/`TASK-AR-220`/`TASK-AR-216`/`TASK-AR-218` 순차 실행 사이클 킥오프 (기록 연속성 정비)
 - [x] 2026-06-10: `TASK-AR-234`~`TASK-AR-245` RSI planning loop B-C 장기 계획 등록
 - [x] 2026-06-10: `TASK-AR-246` parallel worktree/task-claim protocol 등록 및 gate 1차 구현
 - [x] 2026-06-10: `TASK-AR-251`~`TASK-AR-256` collaboration concurrency task set 완료: append-only pane event, SSoT write gate, worktree-first dispatch preflight, UI collaboration state, governance integration
 - [x] 2026-06-10: `TASK-AR-210` local `v0.1.8` release evidence closed as `release_evidence_ready`; external GitHub publish scoped out as `remote_publish_deferred_out_of_scope`
 - [x] 2026-06-12: v0.1.7 공개 사전 gate 조건 정리
 - [x] 2026-06-13: PROJECT-CONTEXT/ROADMAP/ORG/LINKS/TEAMS 오버레이 생성
- [x] 2026-06-14: 오버레이 기반 `TASK-AR-201`/`TASK-AR-204` 연계 검증 및 `TASK-AR-213` 착수
- [x] 2026-06-18: `TASK-AR-205` 90% 임계치 및 `TASK-AR-209/212` 통합 반영 후 v0.1.7 후보 판단
 - [x] 2026-06-25: fallback-1 평가 보류/완화 판단
- [x] 2026-06-30: fallback-2 평가 보류/완화 판단
- [ ] 2026-06-19: TASK-AR-224 공식/이식 근거 동기화 사전 라운드(문헌-이식-hold 경로 정합)
- [ ] 2026-06-20: `TASK-AR-234` planning loop contract/state-machine closure
- [ ] 2026-06-20: `TASK-AR-246` worktree dispatcher and claim release helper proof
- [ ] 2026-06-21: `TASK-AR-235` read-only planning scan first proof
- [ ] 2026-07-02: `TASK-AR-221`, `TASK-AR-219`, `TASK-AR-220`, `TASK-AR-216`, `TASK-AR-218`, `TASK-AR-217` 결과 통합 rehearsal(1차 판정)
- [ ] 2026-07-02: `TASK-AR-222` closeout 번들 반영(official guidance + 1~16 증적)
- [ ] 2026-07-02: `TASK-AR-223` closeout 통합 판정 번들(hold 경로 + 오버레이 + migration + 강제 규칙) 확정
- [ ] 2026-07-09: v0.1.8 재심 보류/연기 2차 판정
 - [ ] 2026-07-16: v0.1.8 최종 판정

### 2026-06-18 보류 판정(이력)

- `TASK-AR-210`의 block/allow matrix lock 필요
- `TASK-AR-204`에서 `TASK-AR-213` 증빙을 release-preflight로 강제
- `TASK-AR-205` 오프라인 게이트 미달이면 HOLD
- `TASK-AR-206`~`TASK-AR-208` reviewer/교정/A2A 누락은 HOLD

### 2026-06-25/2026-06-30 fallback 판정(이력)

- `TASK-AR-214` 질의/정의 계약 미흡 시: `TASK-AR-210`으로 미해결 항목 재이관
- `TASK-AR-215` 오버레이 연결고리 누락/불일치 시 release-preflight HOLD
- 새 프로젝트 1건 이상 런치에서 `context packet` 미동기화 시 HOLD

### 2026-07-02 v0.1.8 후보 통과 기준

- `TASK-AR-216` 판정 이관 상태(`release-state`)와 `TASK-AR-210`이 정합
- `TASK-AR-205` 도메인별 90% 이상 오프라인 게이트
- `TASK-AR-221`에서 요구한 `query contract`/`offline eval`/`live reviewer`/`correction`/`A2A` 항목의 증빙 번들 존재
- `TASK-AR-219` official guidance 템플릿 문구와 실제 증거 로그의 동일성 확인
- `TASK-AR-220` migration 근거와 `TASK-AR-204`/`213`/`218` 차단 경로 정합
- `TASK-AR-222` closeout 번들의 `release-state`, `hold_for_query_contract`, `hold_for_overlay`, `hold_for_data`, `decision_deadline` 정합

### 2026-07-09 / 2026-07-16 재심 기준

- `TASK-AR-217`에서 남은 미충족 사유의 `release-state` 보강 플랜 확인
- 미보완 시 `hold_for_query_contract` 또는 `hold_for_overlay` 이동
- 보완된 항목만 재평가해 `TASK-AR-210` 최종 승인 경로로 복귀

## Risk Register

- risk: 오버레이 누락
  - owner: lead-engineer
  - mitigation: `agent_context_packet.py` 경고를 `TASK-AR-204` 실차단으로 승격
  - review_cycle: 매 세션 시작

- risk: migration evidence 분류 오인
  - owner: doc-steward
  - mitigation: `TASK-AR-209` 5분류와 `TASK-AR-213` 승인 키(`approved_by/expiry/justification`)를 고정
  - review_cycle: 매 판정 전

- risk: 문서 stale
  - owner: independent-auditor
  - mitigation: `updated_at` 갱신 확인 및 stale 감지 시 `hold_for_overlay`
  - review_cycle: 주간

- risk: 강제 규칙 약화
  - owner: owner
  - mitigation: `TASK-AR-204`/`TASK-AR-221`의 warn→block 정책을 자동 검증 스크립트로 강제
  - review_cycle: 매 릴리스 gate 전

- risk: RSI 발산/저가치 task churn
  - owner: drift-guard
  - mitigation: `TASK-AR-244`에서 proposal cap, dedupe, source evidence, budget, kill switch, self-weakening gate block를 강제
  - review_cycle: 매 planning loop cycle 전

- risk: version/release 정합 drift
  - owner: version-steward
  - mitigation: `TASK-AR-240`에서 version string, release state, owner approval, tag plan, release evidence를 대조
  - review_cycle: C-mode promotion 전 및 매 release gate 전

- risk: 병렬 터미널 작업 충돌
  - owner: worktree-dispatcher
  - mitigation: `TASK-AR-246`에서 task claim + per-task git worktree + orchestrator merge protocol을 강제하고, `TASK-AR-251`~`TASK-AR-256`에서 pane event replay + orchestrator-approved SSoT write gate를 추가 강제
  - review_cycle: 매 parallel dispatch 전 및 Stop hook

## Definition of Releasable

- Definition: 공통 런타임 변경 + 오버레이 변경이 컨텍스트 라우터 및 gate로 연결
- Gate:
  - `TASK-AR-210` 보류/승인 사유가 완성되어야 함
  - local release evidence and external GitHub publish evidence must remain separate unless remote PR/tag/CI proof is linked
  - `TASK-AR-204`/`209`/`212`/`213` 상태가 block 조건 없이 정합
  - `AGENTIC_KNOWLEDGE_EVAL_PLAN.md` 실행 순서와 증빙이 일치
  - RSI C-mode는 `TASK-AR-240`/`243`/`244` 통과 전에는 auto-apply 금지
  - 병렬 worker는 `TASK-AR-246` claim/worktree gate 통과 전에는 shared checkout에서 실행 금지
