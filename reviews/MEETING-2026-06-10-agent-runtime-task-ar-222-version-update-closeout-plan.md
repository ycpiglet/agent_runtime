# MEETING: TASK-AR-222 v0.1.8 판정 closeout 기획

일시: 2026-06-10
채널: 멀티 프로젝트 런타임 거버넌스 정합
관련 태스크: TASK-AR-221, TASK-AR-219, TASK-AR-220, TASK-AR-216, TASK-AR-217, TASK-AR-210

## 결정

- v0.1.8 판정은 2026-07-02(1차) → 2026-07-09(2차) → 2026-07-16(최종 freeze)로 유지한다.
- 판정 문구(`READY`/`hold_for_*`/`request_for_v0.1.8`)는 `BACKLOG`/`ROADMAP`/`STATUS`/`TASK-AR-210`에서 동일해야 한다.
- `TASK-AR-222`를 생성해 요구사항 1~16 + 공식 권고 + tag_manual 이식 근거를 단일 closeout 번들로 묶는다.

## 추가 요구 반영

- 스킬·룰·오버레이·평가 체인 1개라도 빠지면 자동 block.
- `query contract` 미달은 `clarify_required` 또는 `reviewer_review`로 강제 이관.
- 오프라인 90% 미달/분석 부재는 `hold_for_data`로 즉시 hold.
- 오버레이 누락은 `hold_for_overlay`로 즉시 hold.
- 라이브 reviewer/footer/교정/A2A가 모두 남지 않으면 release-ready 전이 금지.

## 실행 순서(확정)

1. `TASK-AR-221` 정합 항목(1~16) 증적 정합
2. `TASK-AR-219` 공식 권고 반영 템플릿 확정
3. `TASK-AR-220` tag_manual 이식 근거 재정렬/근거 충족
4. `TASK-AR-216` release-state 이관 템플릿 확정
5. `TASK-AR-218` migration hardening 승인 키 미완 보완
6. `TASK-AR-217` release rehearsal 증적 수집
7. `TASK-AR-222` closeout 번들 최종화
8. `TASK-AR-210` 판정 템플릿 반영 및 ready 판단

## 리스크

- 규칙 경고만 남겨 두면 2~3개 판정 주기 내 강제성이 무너질 수 있음.
- 오프라인 데이터셋이 쿼리 계약과 연결되지 않으면 90% 수치 신뢰성이 낮아진다.
- `tag_manual` 이식 누락이 누적되면 새 프로젝트 전개 시 동일 결함이 반복될 수 있다.

## 산출

- TASK-AR-222 closeout 템플릿 생성
- migration 증거( `MIGRATION-COMPAT-MAP.yml`)와 release gate 간 일치 확인
