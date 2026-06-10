# MEETING (2026-06-09): TASK-AR-221 운영 정합 통합 및 릴리스 업데이트 정렬

## Bottom Line

- v0.1.8 공개는 2026-07-02(1차), 2026-07-09(2차), 2026-07-16(최종) 판정 루프로 진행한다.
- 1차 판정은 “공식 가이드 반영 + 오프라인 90% + reviewer/footer + correction/A2A + migration 이력”이 증거 번들로 남을 때만 `ready` 후보로 전환한다.
- `TASK-AR-221`를 중심으로 기존 `TASK-AR-219`/`TASK-AR-220`/`TASK-AR-216`/`TASK-AR-217`를 하나의 감시 체인으로 묶는다.

## Signal

- 기존 `TASK-AR-219`, `TASK-AR-220`, `TASK-AR-216`, `TASK-AR-217`, `TASK-AR-218`의 남은 리스크를 판정 체인에 넣기로 결정
- Claude/Codex/OpenAI 권고 항목에서 핵심은 traceability + query contract + approval boundary
- tag_manual 이식은 `scripts-source-only`, `scripts-runtime-extra`, `hooks-wrapper` 분류를 근거 기준으로 재정렬할 것에 합의

## Insight

- “정답 보유 데이터” 자체는 절대 정답이 아니고, 질문의 정의와 근거 체인 설계가 더 중요함.
- 실시간 출력을 멈추지 않는 것보다, reviewer/trace/correction 루프가 누락되었을 때 `block`이 안전.
- 멀티 프로젝트 사용 시 오버레이 파일이 부실하면 오탐/미탐이 급증하므로 오버레이 미완은 `hold_for_overlay`로 강제할 필요.

## Decision

1. `TASK-AR-221`을 신규 P0 통합 태스크로 즉시 등록하고 1차 실행 우선순위를 앞으로 당김.
2. `TASK-AR-219`는 2026-07-02/07-09/07-16 판정 문구 템플릿과 공식 가이드 근거를 고정.
3. `TASK-AR-220`에서 누락/의도적 제외/추가 항목을 task/state/owner/rationale로 재분류.
4. `TASK-AR-216` release-state, `TASK-AR-210` 게이트 템플릿, `TASK-AR-217` rehearsal 산출의 동기화를 다음 세션 첫 번째 산출로 둠.

## Action

- BACKLOG/ROADMAP/STATUS/AGENTIC_KNOWLEDGE_EVAL_PLAN 업데이트
- `TASK-AR-221`, `TASK-AR-219`, `TASK-AR-220` 사이 증빙 링크 체인 반영
- `TASK-AR-204` co-location 규칙에 모델 변경-스킬 변경 동기화 미반영 시 `block` 추가
- next session handoff는 위 순서대로 진행
