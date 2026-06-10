# SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario

## Bottom Line

오버레이 패킷은 단일 문서가 아니라 `vision/roadmap/org/teams/links/communication`의 연결고리로 운영해야 한다.

## Signal

- 서로 다른 프로젝트를 `agents/project` 오버레이 교체만으로 전환할 수 있어야 함.
- 커뮤니케이션 로그(`MEETING`/`RESEARCH`/`CALL`)는 오버레이 패킷의 변경 근거로 인정.
- 링크 누락은 즉시 `high-risk` 라우팅으로 분류.

## Insight

- `TASK-AR-215`에서 가장 위험한 포인트는 `context_packet`가 `TASK-AR-204`와 불일치할 때이다.
- 오버레이 변경이 없을수록 문제는 적지만, 변경이 있어도 검증 체인(문서, 리뷰, owner)이 남으면 안정적으로 이관 가능.

## Decision

1. `agents/project/LINKS.md`를 오버레이 패킷의 인덱스 포인트로 사용.
2. 크로스 프로젝트 시뮬레이션에서 문맥 라우팅의 누락·불일치 항목을 자동 점검.
3. 미완전한 오버레이는 `TASK-AR-210` 블로커 항목에 반영.
