---
title: Console Overhaul Owner Decisions (15) Resolved
date: 2026-07-26
signal: pass
score: 95
tags: [decision-record, console-overhaul, phase-1, quiz-gate, owner-decisions]
---

# Console Overhaul Owner Decisions (15) Resolved

## Bottom Line

마스터플랜(reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
§Owner Decisions)의 15개 결정이 Owner에 의해 확정되었다(#7만 구현 시점 보류).
#4·#5는 Owner가 참조 지시한 Geoffrey Litt(Notion)의 "Understanding is the new
bottleneck" 강연/스킬의 방법론을 반영해 확정했다. 본 문서가 Phase 1 등록의
origin_ref이자 결정 정본이다.

## Signal

| # | 결정 | 확정 내용 |
| --- | --- | --- |
| 1 | 정본 표면 | 웹 콘솔 = 1차 표면, 마크다운 보드 = 파생물(로직 단일화) |
| 2 | 프레즌스 | 계측(이벤트 로그) 먼저, 뷰 투자는 데이터 확인 후 |
| 3 | 비전 정산 | VISION.md를 의사결정 콘솔 비전으로 갱신 + 확장기 산출물 P2 문서 정산 |
| 4 | 퀴즈 강제 수준 | 기본 켜짐 + `--skip-quiz`(사유 기록 필수) loud escape. 프레이밍: 평가가 아닌 **속도 조절기(speed regulator)** — Litt |
| 5 | 퀴즈 발동/형식 | PR 단위 발동(diff<100줄·비핵심 경로는 스킵, `scripts/`·`.githooks/`·`AGENTS.md`는 무조건). **explainer 문서(배경→직관→서술형 diff→퀴즈)에 내장된 5문항 medium 난이도, gotcha 금지, 객관식+즉시 피드백, 선택지 순서 랜덤화**(정답 위치 패턴 게이밍 방지). 통과 4/5 + 오답 문항은 teach-back 후 재출제로 전량 소화 |
| 6 | 모델 계열 분리 | 검증자·퀴즈 출제자는 작업자와 **다른 모델 계열** 요구 |
| 7 | held-out 위치 | **보류** — W4c 구현 시점에 확정(레코드에 OWNER-DECIDES 유지) |
| 8 | /clarify 스킬 | grill(비즈니스)과 **별도 스킬로 병행 공존** |
| 9 | 승인 티어링 | 저위험(work close, green merge)은 council 위임(독립 근거 기록), 고위험은 Owner 전결 |
| 10 | 독박 종착점 | **측정을 넘어 실제 분업까지** — orchestrator 권한 분해(planner·integrator 실체화)를 P2 확정 항목으로 승격. 단 순서는 측정(1-9) 선행 |
| 11 | actual_hours 정의 | **실작업 시간**(claim wall-clock 아님) — 이벤트 로그(하트비트/tool-call 스팬) 기반 측정 설계 필요, P2 이벤트 로그 실체화와 연계 |
| 12 | 백필 모순 | 격리(P0 기구현 추인) |
| 13 | 인사이트 리듬 | **고정 주기 대신 임계 기반 발행**(Owner 제안): 완료 누적 N건(초기 10) 또는 결정 필요 신호 발생 시 발행 + 3주 침묵 가드(1줄 하트비트) |
| 14 | 프런트 스택 | 빌드리스 바닐라 + 물리 파일 분리 확정(Preact+htm은 신규 복잡 표면 시 재평가) |
| 15 | KR i18n | P1 병행(홈 재구성과 함께) — P0 이관 코스메틱(아이콘·토큰·다크·칸반)도 동일 패스에 포함 |

## Insight

Owner가 #4·#5의 참조로 지시한 원출처: **Geoffrey Litt(Notion 디자인 엔지니어),
"Understanding is the new bottleneck"**, AI Engineer World's Fair 2026 강연.

- 블로그(정본): https://www.geoffreylitt.com/2026/07/02/understanding-is-the-new-bottleneck
- 강연 영상: https://www.youtube.com/watch?v=WkBPX-oDMnA
- /explain-diff 스킬: https://gist.github.com/geoffreylitt/a29df1b5f9865506e8952488eac3d524
- 한국어 요약(유통 경로): https://news.hada.io/topic?id=31429

채택한 Litt 방법론: ① 퀴즈 단독이 아니라 **explainer 문서에 내장**(배경→직관→
서술형 diff→퀴즈 순 — explainer 자체가 teach-back 교재를 겸함), ② 5문항 medium,
gotcha 금지, 즉시 피드백, ③ "통과 전 코드를 남에게 보내지 않는다" = **pre-PR
위치**, ④ 퀴즈는 평가가 아니라 "AI 루프가 인간 이해 속도를 추월하지 못하게 하는
속도 조절기". 우리 변형: Litt의 자발 규율을 하네스의 기본 켜짐+loud escape로
기계화하고, gist 커뮤니티가 지적한 정답 위치 게이밍을 선택지 랜덤화로 보완하며,
출제자를 작업 세션과 분리된 타 모델 계열 인스턴스로 독립화(#6)한다.

## Action

| # | 액션 | 조건 |
| --- | --- | --- |
| 1 | Phase 1 taskset 등록(본 문서를 origin_ref로) | 즉시 |
| 2 | W4c 퀴즈 태스크에 #4·#5·#6 확정치를 수용 기준으로 명시 | 등록 시 |
| 3 | held-out 위치(#7)는 W4c 구현 착수 시 Owner 확정 | P1 중반 |

## Risks / Blockers

- 퀴즈/체크포인트는 Owner 접점을 늘리므로 #9 티어링과 **패키지 배포**가 전제 —
  분리 배포 시 Owner 병목 악화 위험.
- #11(실작업 시간)은 이벤트 로그 실체화(P2) 전까지 근사 측정만 가능 — closeout-
  automation 태스크는 측정 방식 설계를 선행 유닛으로 가져야 한다.

## Decision

15개 중 14개 확정, #7 보류(구현 시점 확정). 본 기록으로 Phase 1 등록을 개시한다.

## Next

- `python scripts/work.py new --input reg-phase1-v3.json` → 게이트 → PR → auto-merge.
- P2 등록은 P1 안착 후(#10 확정으로 orchestrator 분해가 P2 확정 항목).
