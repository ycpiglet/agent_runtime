---
type: review
id: REVIEW-2026-06-14-knowledge-stack-followups-closeout
audience: owner
status: watch
signal: watch
score: 84
priority: High
tags: [closeout, knowledge-graph, lock-merge-driver, ingest, console, ui, review]
recorded_at: 2026-06-14T18:05:00+09:00
---

# REVIEW 2026-06-14 — Knowledge-stack follow-ups closeout (A/B/C)

## Bottom Line

- Summary: knowledge-stack wave의 RETRO forward action들과 #5를 모두 구현·머지했다 — **A** fixture-lock 자동화(#149), **B** review/meeting reference 엣지(#150), **C** 콘솔 knowledge-graph 시각화 뷰(#151, CI 통과 시 auto-merge).
- Result: A=keep-ours 머지 드라이버+post-merge 훅(데드락 회피), B=ingest 본문 스캔으로 edges 442→1432·고립 narrative 427→155, C=`/api/knowledge-graph` + SVG kind-clustered 뷰(Playwright 실렌더 검증). 모든 PR green CI·게이트 EXIT=0.
- Boundary: C는 콘솔 비템플릿이라 fixture lock 무변경. A/B는 lock 재생성 동반. #151은 본 레코드 작성 시점 CI 대기.

## Signal

| 항목 | PR | 핵심 | 검증 |
| --- | --- | --- | --- |
| A fixture-lock 자동화 | #149 | `true` keep-ours 드라이버 + `.githooks/post-merge` 재생성 | 6 tests + 실머지 e2e(exit0/마커0/정확 lock) |
| B reference 엣지 | #150 | ingest_reviews 본문 스캔 → references 엣지 | 43 knowledge tests; edges 442→1432 |
| C 콘솔 그래프 뷰 | #151 | degree-ranked bounded 서브그래프 + SVG 클러스터 렌더 | 250 ui tests; Playwright 실렌더 |

## Insight

- A는 "당연한" 설계(드라이버가 lock 재생성)가 3번 실패하고서야 옳은 구조(충돌 억제+post-merge)에 도달 — merge driver는 머지 결과를 못 보고, 내부 git 호출은 데드락한다(COMPOUND-2026-06-14-004).
- B의 효과가 C를 더 유용하게 만들었다: reference 엣지가 그래프 연결성을 3배로 늘려, C의 시각화에 실제 구조(task↔taskset↔review)가 드러난다.
- C는 기존 dependency-graph 뷰를 아날로그로 삼아 위험을 낮췄다(검증된 SVG 패턴 재사용, 폴링 부하 회피 위해 on-demand 엔드포인트).

## Action

| # | 항목 | 상태 |
| --- | --- | --- |
| 1 | RETRO #1 fixture-lock 자동화 | 완료(#149) |
| 2 | RETRO #2 ingest reference 엣지 | 완료(#150) |
| 3 | #5 콘솔 그래프 뷰 | 완료(#151, auto-merge 대기) |
| 4 | merge-driver 데드락 교훈 기록 | COMPOUND-2026-06-14-004 |

## Risk

- A의 드라이버/훅은 로컬 머지에만 적용 — GitHub 서버측 머지는 미사용이라 PR DIRTY는 로컬 재머지로만 해소(문서화됨).
- C의 그래프 빌드는 on-demand로 git/파일 스캔(~1-2s) — 대형 레포에서 느려질 수 있어 top-N(기본 140) 캡으로 제한.
- C 초기 hash-route 로드 시 서버가 죽어 있으면 stale 에러가 고정될 수 있음(테스트 중 관찰) — 정상 서버에선 재현 안 됨, 사이드바 클릭이 재-fetch.

## Decision

- Decision: A/B/C를 채택하고, A의 "merge driver는 self-contained·non-blocking, 머지 결과 가공은 post-merge에서" 규칙을 표준으로 한다.
- Decision: 본 REVIEW와 COMPOUND-004를 owner-docs에 등재한다.

## Next

- #151 green 확인 후 auto-merge.
- 후속(선택): C 그래프 뷰에 검색/필터·focus 딥링크 연동, ingest reference의 dangling-watch 정리.
