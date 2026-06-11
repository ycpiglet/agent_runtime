---
id: TASK-AR-332
display_id: TASK-AR-332
task_uid: 171785e6-b825-45a2-a605-365109b375ba
registered_at: 2026-06-11T18:56:35+09:00
created_at: 2026-06-11T18:56:35+09:00
updated_at: 2026-06-11T18:56:35+09:00
title: 파일 첨부 — 업로드/다운로드/미리보기 + evidence 연동
status: planned
priority: P1
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-UI-PLATFORM-EXTENSIONS
tags:
  - ui-extensions
  - attachments
  - evidence
---

# TASK-AR-332 - 파일 첨부 — 업로드/다운로드/미리보기 + evidence 연동

## Goal

- 사진/문서를 task·메시지에 드래그드롭/붙여넣기로 첨부하고, 미리보기·다운로드할 수 있게 한다 (Notion/Slack/Jira 모델).

## Scope

- 업로드 엔드포인트 + 저장 경로(`agents/project/evidence/attachments/` 등) + 크기/타입 제한.
- 스크린샷 클립보드 붙여넣기, 이미지 라이트박스, md/텍스트 렌더 미리보기.
- 첨부를 evidence 레코드로 등록해 task closeout 증거 체계와 연동.

## Acceptance Criteria

- 첨부 업로드→task 상세 표시→다운로드 왕복이 동작하고 evidence 링크가 생성된다.

## Evidence Targets

- `src/agent_runtime/ui_console.py` 업로드 라우트, 저장 규칙 문서, 테스트
