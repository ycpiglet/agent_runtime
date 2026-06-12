---
type: review
id: REVIEW-2026-06-12-agent-runtime-release-plan-v019-v020
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [release, version-policy, cadence, autofolio, handoff]
---

# Release Plan v0.1.9 / v0.2.0 Review

## Bottom Line

- Summary: Owner가 "배포 준비 작업과 타이밍을 다음 세션 집행 가능하게 정리,
  타이밍 트리거/훅 자동화 가능 여부, 그리고 0.1.5→0.1.9식 급작스러운 버전
  점프 우려"를 요청해 릴리스 계획을 확정했다.
- Result: 빅뱅 1회 대신 **2단계 릴리스** — v0.1.9(현 main, 추가형 81커밋,
  지금 가능) → v0.2.0(codex work-schema/등록 CLI/identity merge 후, 호스트
  계약 변경 = minor bump). 케이던스 트리거는 알림 전용 자동화로
  TASK-AR-510 등록.
- Boundary: 태그/푸시 등 외부 발행은 기존 규약대로 Owner 승인 경유.
  v0.1.9에는 codex 미머지 브랜치를 포함하지 않는다.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| v0.1.8 선례 | pass | `RELEASE-DECISION-v0.1.8.yml` — readiness summary → council 4역할 투표 → preflight → tag |
| 미릴리스 변경 성격 | pass | v0.1.8..main 81커밋 = chore 25/docs 13/feat 9/fix 7; 템플릿 59파일 +8472/-144, 삭제 1건(의도된 레거시 제거)뿐 → 비파괴 = patch |
| 차기 파괴 변경 | watch | codex 미머지: WORK-SCHEMA.yml, 등록 CLI(work.py), identity 스키마 — 호스트 계약 변경 = v0.2.0 사유 |
| autofolio 핀 | pass | `agent_runtime.yml` ref=v0.1.8 (최신 릴리스 사용 중), unmanaged 분기 보호 확인 |
| 릴리스 도구 | pass | release_readiness_summary / council·execution gate / pending_release_guard / CLI release-preflight·publish-* 전부 실재 |

## Insight

- 버전 점프(0.1.5→0.1.8처럼 0.1.6/0.1.7 건너뜀)의 원인은 버전 산술이
  아니라 **케이던스 부재** — 변경이 쌓인 뒤 한 번에 릴리스해서 생긴 현상.
  해법은 번호 정책 + 릴리스 주기이지 번호 재조정이 아니다.
- 릴리스 실행 자체의 완전 자동화는 기존 거버넌스(외부 발행 Owner 승인,
  council 투표)와 충돌한다. AR-509(호스트 알림)와 동일한 패턴 —
  **감지·제안은 자동, 실행은 승인 경유** — 이 옳은 경계다.

## Decision

- Decision: 버전 정책 — patch(0.1.N): 추가형 템플릿/게이트/문서 변경.
  minor(0.x+1.0): 호스트-facing 스키마/계약 파괴 변경. 케이던스: taskset
  closeout wave(W6) 경계 또는 2주 중 먼저 오는 쪽에 patch 릴리스.
- Decision: v0.1.9 = 현 main 스냅샷(codex 미머지 제외). v0.2.0 = codex
  work-schema 계열 merge + replan(T1/T2) 후.
- Decision: 케이던스 트리거는 TASK-AR-510(release-lag watch — 마지막 태그
  이후 커밋 수/taskset closeout 감지 → 비차단 릴리스 제안 finding) 으로
  자동화한다. 릴리스 실행은 council/Owner 게이트 유지.
- Decision: autofolio 동기화는 v0.1.9 태그 직후 ref bump + update-plan →
  update. v0.2.0 때 unmanaged 분기(AGENTS.md, roles.yml, task.schema.json)
  재조정 점검을 런북에 포함한다.

## Next Steps — v0.1.9 릴리스 체크리스트 (다음 세션 집행 순서)

1. 사전 확인: `pytest tests -q` 전체 + `python scripts/owner_governance_gate.py` exit 0
   (known-flaky: test_template_message_queue.py skewed_replay_delay — 단독 재실행으로 판정).
2. 버전 bump: `pyproject.toml` 0.1.8 → 0.1.9 (+ 버전 참조 픽스처 동기:
   `python scripts/release_version_consistency_steward.py` 확인).
3. `python scripts/release_readiness_summary.py --out reviews/RELEASE-READINESS-SUMMARY-<date>-v0.1.9.json`.
4. readiness 리뷰 기록 작성 + council 투표 기록 `agents/project/release/RELEASE-DECISION-v0.1.9.yml`
   — W4b 원칙 적용: qa/independent-auditor 투표는 작업자와 다른 인스턴스가 수행.
5. `python scripts/release_council_gate.py` → `release_execution_gate` → `pending_release_guard` 통과.
6. `python -m agent_runtime.cli release-preflight` → `publish-check` → `publish-bundle` → `publish-tag-smoke`.
7. 태그/푸시: **Owner 승인 후** v0.1.9 태그 + push.
8. autofolio: `agent_runtime.yml` ref → v0.1.9 → `update-plan` → `update` → `doctor`.
9. (이후) codex merge 도착 → plan_assumption T1 체크 → replan → v0.2.0 사이클 반복.
