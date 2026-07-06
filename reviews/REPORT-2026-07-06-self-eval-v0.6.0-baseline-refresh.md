---
title: Self-Eval v0.6.0 Baseline Refresh + Host Pipeline Wiring
date: 2026-07-06
signal: pass
score: 78
tags: [self-eval, rsi-fitness, host-pipeline, gh-128, v0.6.0]
---

# Self-Eval v0.6.0 Baseline Refresh + Host Pipeline Wiring (GH #128)

## Bottom Line

- Owner가 #128 착수를 승인(2026-07-06)해 두 갭을 이행: **호스트 실사용 데이터 파이프라인 배선**(요청 4, 신규) + **held-out 베이스라인 v0.2.0→v0.6.0 현행화**(요청 1 실가동).
- v0.2.0→v0.6.0 advisory 델타: 계산 가능한 고정 지표 5종 중 **3 improved / 2 REGRESSED**(단, REGRESSED 2종은 누적 추정치라 해석 유보 — Insight 참조).
- v0.5.0..v0.6.0 윈도우 실측: first-pass proxy `0.767`, gate failure `0`, reopen `0`, feat 36/fix 21.
- RSI fitness gate는 council 결정대로 **advisory 유지**(신뢰 가능한 베이스라인 + R3 사인오프 전 비차단) — 이번 갱신이 그 전제(신뢰 베이스라인)를 만든다.

## Signal

| Fixed metric (v0.2.0 → v0.6.0) | Baseline | Current | Delta | Verdict |
| --- | ---: | ---: | ---: | --- |
| completed_tasks | 194 | 257 | +63 | improved |
| open_tasks | 25 | 0 | -25 | improved |
| verification_coverage_pct | 18.6 | 28.0 | +9.4 | improved |
| est_tokens_total | 814,600 | 1,121,100 | +306,500 | REGRESSED* |
| est_hours_total | 1,546.0 | 1,758.0 | +212.0 | REGRESSED* |

| Window metric (v0.5.0..v0.6.0) | Value |
| --- | ---: |
| commit_count / feat / fix | 90 / 36 / 21 |
| rework_count / rework_ratio | 21 / 0.233 |
| first_pass_rate_proxy | 0.767 |
| gate_failure_count / reverification / reopened | 0 / 0 / 0 |
| tokens_per_task, hours_per_task, owner_interventions | NOT COLLECTED (honest absence) |

## Insight

- \*`est_tokens_total`/`est_hours_total`은 **누적 추정치**라 태스크가 늘면 단조 증가한다 — 방향 판정(lower-is-better)이 스냅샷 총량엔 부적합. 차기 개선 후보: 총량 대신 `per-completed-task` 정규화로 전환.
- `first_try_test_pass_rate` 등 6개 고정 지표는 WORK-SCHEMA actuals 캡처 부재로 여전히 null — §6 instrumentation 부채가 fitness 판정의 실질 병목.
- 호스트 파이프라인은 `agents/host/eval/*.json`(`agent-runtime-host-eval/v1`)을 additive 인제스트하며, 부재는 무에러·이물/불량 파일은 `host_skipped`로 **소리내어** 보고(침묵 드롭 금지). autofolio 첫 파일럿 wave가 첫 실데이터 공급자가 된다.

## Action

- `scripts/self_eval_harness.py`: `load_host_snapshots()` + snapshot `hosts`/`host_skipped` + advisory gate 호스트 라인.
- `tests/test_self_eval_harness.py`: 부재 무에러 / 인제스트·보고 / 불량 파일 loud-skip 계약 3건 추가 (27 passed).
- `docs/AGENT_RUNTIME_EVAL_METRICS.md` §5b 신설(스키마·드롭 위치·인제스트 규약), `docs/host-context-read-location.md` wired-today 항목.
- `SELF-EVAL-BASELINE.json`을 v0.6.0 스냅샷으로 `--write` 갱신(갱신 전 v0.2.0 대비 --gate 델타를 본 리포트에 보존).

## Risk

- 누적 추정치 지표의 REGRESSED 판정은 오탐 성격 — 정규화 전까지 fitness 종합판정에 사용 금지.
- 호스트 데이터는 self-report라 오라클(테스트 검증) 아님 — 요청 2의 test-verified 원칙상 보조 신호로만.

## Decision

- 베이스라인은 이제 v0.6.0 — 다음 릴리스(v0.7.0)부터 N→N+1 비교가 릴리스 cadence와 정렬된다.
- fitness gate의 advisory→차단 전환은 별도 Owner/R3 결정 사안으로 유지.

## Next

- autofolio 파일럿 wave 지표 파일 수급 시 첫 host-eval 인제스트 실증.
- est_* 지표 per-task 정규화 + WORK-SCHEMA actuals 캡처(§6 부채) 후속.
