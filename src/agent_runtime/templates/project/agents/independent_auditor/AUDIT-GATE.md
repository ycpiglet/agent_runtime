# AUDIT-GATE — Independent Audit Gate

## Purpose

`agents/lead_engineer/tasks/TASK-*.md` 완료(완료)된 항목의 품질 및 협업 감사를 일관되게 수행하기 위한 최소 기준입니다.

## 필수 적용 조건

- TASK 상태가 `완료`이고 `priority`가 `Critical` 또는 `High`인 경우,
  `## Independent Audit` 섹션이 있어야 합니다.
- 독립 감사 게이트 기준과 연동되는 검수 판단은 아래 형식을 따라야 합니다.

## 독립 감사 섹션 템플릿

```text
## Independent Audit
판정: 통과 | 보류 | 재검토 필요
검토자: <name>
검토 시각: <ISO8601>
요약: <핵심 판단 이유>
실측 비용 (시간): <숫자>
실측 비용 (LLM 토큰): <숫자>
해소 조건: (보류/재검토일 경우만 필수)
```

## 판정 규칙

- `판정: 통과`는 기본적으로 다음이 충족된 경우 허용
  - 완료 근거가 메시지/이벤트/근거 문서에 추적되어 있음
  - 위험 판단이 완료 상태와 정합되는지 검증
- `판정: 보류` 또는 `재검토 필요`는 `해소 조건`이 비어 있지 않아야 함.

## 예외 및 완화

- `audit_exempt` frontmatter가 있는 레거시 TASK는 INFO 단서로 축소
  (강제차단이 아닌 이력성 가시화로 처리)

## 거부 사유 예시

- 판정 값이 `통과/보류/재검토 필요` 외의 값
- `High`/`Critical` 완료 TASK에서 Independent Audit 누락
- 보류/재검토인데 `해소 조건` 미기재
