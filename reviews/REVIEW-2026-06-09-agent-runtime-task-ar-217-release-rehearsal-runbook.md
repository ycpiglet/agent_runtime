# REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-runbook

## Bottom Line

`v0.1.8 release rehearsal`를 실행 가능한 순서로 고정하고, 각 단계별 증적을 바로 다음 판정으로 전달한다.

## Runbook

1. **판정 초기화**
   - `BACKLOG.md`의 07-02/07-09/07-16 일정과 `TASK-AR-216` 이관 상태를 확인
   - `release-state`가 `ready`가 아닌 항목이 있는지 빠르게 확인
2. **preflight**
   - `agent_runtime.cli release-preflight --source . --check`
   - `agent_runtime.cli release-preflight --source .tmp/release-bundle --check`
3. **오프라인 게이트**
   - `TASK-AR-205` 골든셋 실행
   - 도메인별 점수 90% 미달 시 실패 케이스 식별
4. **라이브·교정 루프**
   - 고위험 케이스에서 reviewer verdict, footer, correction_id 수집
   - A2A trace에서 request/review/decision chain 재구성 가능성 확인
5. **판정 정리**
   - 미충족 사유를 `hold_for_*`로 TASK-AR-210에 이관
   - 블로커/수정 항목을 다음 세션 우선순위에 즉시 반영
