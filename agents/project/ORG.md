# Organization (Host Overlay)

## Ownership

- product_owner: owner
- decision_owner: lead-engineer
- escalation_owner: managing-partner
- review_owner: independent-auditor

## Team Structure

- engineering_team:
  - ceo
  - lead-engineer
  - backend
  - qa
  - doc-steward
  - independent-auditor
  - owner

## Authority and Access

- role: owner
  level: secret
  boundary: 변경 승인, 공개 게이트 최종 사인오프
- role: lead-engineer
  level: confidential
  boundary: TASK 패키징, gate 근거 정합
- role: doc-steward
  level: internal
  boundary: 오버레이/리뷰/감사 증적 운영

## Escalation Policy

- escalation_condition: 오버레이 누락, 규칙 충돌, 오답률 90% 미달, 정의 미확정
- response_deadline: 1 business day
- emergency_owner: owner
