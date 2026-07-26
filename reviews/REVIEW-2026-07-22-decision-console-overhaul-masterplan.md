---
title: Decision Console Overhaul Masterplan
date: 2026-07-22
signal: pass
score: 92
tags: [ui-ux, decision-console, overhaul, masterplan, initiative-planning, owner-request]
---

# Decision Console Overhaul Masterplan

## Bottom Line

Owner가 웹 콘솔을 두고 "정보가 산재되고, 비효율적이고, 직관적이지 않고,
불완전하다"고 판정했다. 17개 에이전트 병렬 딥리서치(내부 판독 6 + 외부 리서치 5
+ 축별 갭분석 4 + 종합)와 코드 스팟체크로 진단한 결과, 이 제품은
"에이전트를 검증하는 기계"로는 완성 단계이나 "Owner의 의사결정·이해·시간을
지키는 제품"으로는 **신뢰(신선도)·인터페이스(요구/이해 게이트)·측정(흐름·점유
지표)** 세 기둥이 비어 있고, 그 공백이 lead-engineer와 Owner의 이중 독박으로
흡수되고 있다. 본 문서는 대개편을 3개 Phase(각 initiative+taskset)로 분해한
정본 설계 기록이며, `scripts/work.py new`로 등록되는 세 taskset의 origin_ref이자
plan-assumption(T0) 앵커다.

## Signal

| 진단 축 | 현재 | 목표 | 근거 |
| --- | --- | --- | --- |
| 축1 빠른 현황 파악 | 구조 ~70% / 신뢰 ~40% | 스크롤 0으로 5초 판별 + 신선도 보장 | `ui_console_assets.py:264-303`, `ui_state.py:8118-8123` |
| 축2 흐름 인사이트 | 스키마 A / 실측 D / 전달 F | 흐름 지표 3종 자동 축적·push | actual_hours 18/259, rework 0/259 |
| 축3 요구/이해 게이트 | 인터뷰 30% · 퀴즈 0% | 요구 grill → 측정 검증 → 이해 퀴즈 → PR | 퀴즈 게이트 저장소 0건(코드 확인), `skills/grill/SKILL.md:4` |
| 구조 독박 | 측정 불가 + 화면이 왜곡 재생산 | 점유 측정 가능화 + 권한 티어링 | `AGENTS.md:107-108`, `backlog_board.py:553-593` |

검증된 사실: 이해도 퀴즈/comprehension 게이트 = 저장소 0건. UI 서버 인증 없음
(127.0.0.1 바인드만 방어). SSE는 single-shot(코드 주석 B-03). grill은 비즈니스
전용 opt-in. W4a/W4b 독립검증은 `task_claim_dispatcher.py`에서 verifier!=worker
하드 게이트로 이미 존재.

## Insight

요구가 들어와 PR로 나가기까지 8단계에서 **가운데(검증)만 잠기고 양 끝이 열려**
있다. auto-merge가 ~1분 내 작동하므로 이해하지 못한 산출물이 교정 창 없이 머지될
수 있다. 그리고 개선 1순위는 화면이 아니라 **믿을 수 있는 데이터**다 — 위생 없는
흐름 타일은 거짓말을 하고, 캘리브레이션 없는 퀴즈 게이트는 도박이며, 신선도 없는
홈 개편은 "예쁜 낡은 화면"이다. 그래서 Phase 0(신뢰·데이터 위생)이 Phase 1(심장부:
홈 Decision Screenfit·요구/이해 게이트)과 Phase 2(구조 완성: 파일 분리·IA 재편·
권한 분해)의 전제가 된다.

## Decision

대개편을 다음 3개 Phase로 분해하여 각각 하나의 initiative + taskset으로 등록한다.
최종 목적지는 UI/UX/Design(홈 Decision Screenfit → IA 6허브 재편 → 디자인 시스템
정합)이며, Phase 0/1이 그 전제를 만든다.

- **Phase 0 — Quick Wins (1–2주)** · `TASKSET-AR-CONSOLE-OVERHAUL-P0`
  신뢰 복구, 홈 위계 1차, 프론트 위생, 데이터 위생, 전달 씨앗, 계약 봉합, 축3 씨앗.
  결정 비종속 · 즉시 착수 가능(worker-ready 유닛 포함).
- **Phase 1 — 핵심 구조 (1–2개월)** · `TASKSET-AR-CONSOLE-OVERHAUL-P1`
  attention 단일 정본화, 홈 Decision Screenfit 완성, renderAll 해체, /clarify+EARS,
  3자 추적성, W4c 퀴즈 게이트 승격, Owner 승인 티어링, FLOW-DIGEST+Ownership.
  일부 Owner 결정(§Owner Decisions 4·5·6·9·13)에 종속 · 유닛 보류.
- **Phase 2 — 장기·확장 (2개월+)** · `TASKSET-AR-CONSOLE-OVERHAUL-P2`
  프론트 파일 분리, IA 재프루닝 2.0+VISION 갱신, 이벤트 로그 실체화, 실패 패턴
  압축, 축3 패턴군 UI, orchestrator 3분할, 에이전트 상호검증 debate.
  결정(§Owner Decisions 1·2·3·10·14)에 종속 · 유닛 보류.

## Owner Decisions (등록 전 확정 불요, Phase 1/2 착수 전 확정 필요)

1. 웹 콘솔=1차 표면 / 마크다운 보드=파생물 역할 분리? (권고: 동의)
2. 프레즌스 뷰(Office Map·스프라이트) 지금 투자? (권고: 계측만, 뷰는 유보)
3. 확장기 산출물(gamification·idea vault) 존치/폐기 + VISION.md 갱신? (권고: 갱신)
4. 퀴즈 게이트 강제 수준 — loud escape vs 하드 차단? (권고: 기본 켜짐+--skip-quiz)
5. 발동 임계 — diff 100줄 + scripts/·.githooks/·AGENTS.md 강제 + est_hours? (권고: 채택)
6. 검증자/출제자 모델 계열 분리? (권고: 요구)
7. held-out 케이스 봉인 위치? (권고: 별도 디렉토리+게이트 주입)
8. /clarify를 grill과 별도 스킬로? (권고: 분리)
9. work close·green merge의 council 위임? (권고: 동의, 퀴즈와 패키지)
10. 독박 대응 종착점 — 측정까지 vs orchestrator 권한 분해까지? (권고: Phase2에서 재결정)
11. actual_hours 정의 — claim wall-clock/실작업/토큰? (권고: claim wall-clock)
12. 백필 모순 레코드 — 격리 vs 소급 정정? (권고: 격리)
13. 인사이트 리듬 — 주간 FLOW-DIGEST + 세션 delta? (권고: 채택)
14. 프런트 스택 — 빌드리스 바닐라+파일 분리 확정? (권고: 확정, Preact는 신규 표면 시 재평가)
15. KR i18n 완결 우선순위 — Phase 1 병행? (권고: 병행)

## Action

| # | 액션 | 담당/게이트 | Phase |
| --- | --- | --- | --- |
| 1 | Phase 0 taskset(TASK-AR-602~608) claim→구현→W4a/W4b | lead_engineer | P0 |
| 2 | §Owner Decisions 4·5·6·9·13 확정 후 Phase 1 착수 | Owner | P1 |
| 3 | §Owner Decisions 1·2·3·10·14 확정 후 Phase 2 착수 | Owner | P2 |

## Risks / Blockers

- Phase 1/2 태스크는 유닛이 보류 상태이며, §Owner Decisions 확정 전 claim하면
  의도와 다른 방향으로 진행될 위험이 있다 — 결정 확정 후 `work.py split`으로
  worker-ready 유닛을 생성한 뒤 claim한다.
- 신규 게이트(requirements-lint, W4c 퀴즈)는 마찰을 늘리므로, Owner 승인
  티어링(1-7)과 산출물 크기 비례화(2-5)를 패키지로 배포하지 않으면 Owner 병목이
  오히려 커질 수 있다.
- 프론트 물리 파일 분리(2-0) 전에 대규모 마크업 작업(2-1/2-4)을 모놀리스 위에서
  진행하면 diff/리뷰 비용이 급증한다 — 순서 의존을 지킬 것.

## Next

- `python scripts/work.py new --input <P0|P1|P2>.json`으로 3개 taskset 등록.
- `python scripts/work_item_classifier.py --check`, `python scripts/taskset_work_gate.py --check`,
  `python scripts/task_unit_readiness_gate.py --check` 통과 확인.
- Phase 0부터 W2 claim → W3 구현 → W4a/W4b 검증 순으로 진행.
