# SAFETY-GATE

## 목적

`agent_orchestrator.py`, `auto_runner.py`의 자동/반자동 실행 시 오케스트레이터 판단을 강제하는 정책 파일입니다.

## 기본 정책

- 기본 상태: `ALLOWED`
- 안전 규칙 위반 시: `BLOCK` 또는 `WARN`
- 경합/예외: `DEFER`

## 정책 항목

1. 긴급 정지(긴급 파일/플래그)
   - `.agent_emergency_stop` 또는 `.agent_pause` 존재 시 즉시 `BLOCK`
2. 호출 타입(호출자/타겟/모델) 허용
   - 허용되지 않은 실행 경로는 `BLOCK`
3. 금지 키워드
   - 위험 키워드가 감지되면 `BLOCK`
4. 비용/리스크 구간 초과
   - 과도한 재시도/루프는 `WARN`
5. 감사 증적 필요
   - 주요 Spawn/Call/Kill 판단은 증적 파일에 기록

## 판정 메타데이터

증적(`agents/runtime/evidence/safety.jsonl`)에는 최소 다음이 기록됩니다.

- ts: ISO8601 timestamp
- policy_version
- action: spawn | call | kill
- decision: ALLOWED | WARN | BLOCK | DEFER
- reason
- role
- context

## 동작 규칙 요약

- `BLOCK`: 실행/호출 즉시 중단
- `WARN`: 실행은 가능하되 증적을 남겨 후속 리뷰 대상
- `DEFER`: 의사결정을 미루고 운영자 승인 또는 상위 정책 대기
- `ALLOWED`: 증적 후 통과