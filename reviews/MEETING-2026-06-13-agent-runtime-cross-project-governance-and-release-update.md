# MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update

## Bottom Line

`agent_runtime`의 다음 공개 일자는 `v0.1.6` 2026-06-13 후보와 `v0.1.7` 2026-06-18 후보 모두 `Hold` 유지입니다. 블로커가 해소되지 않으면 `v0.1.7`은 2026-06-25로 버퍼 이동합니다.

## Signal

- 사용 시나리오 목표: 공용 런타임을 유지한 채 프로젝트별 Vision/ROADMAP/ORG/LINKS/팀 정보를 `agents/project/*` 오버레이로 주입.
- 현재 상태: `TASK-AR-210`은 gate 템플릿 고정 단계, `TASK-AR-211`은 오버레이 계약 작성 단계, `TASK-AR-201/204/209/212`는 구현 전환 단계.
- 태스크 우선순위: `TASK-AR-210` → `TASK-AR-211` → `TASK-AR-201` → `TASK-AR-204` → `TASK-AR-209/212` 순.
- 정량 요구(진행 기준): `TASK-AR-205` 오프라인 평가에서 임계치 미달(`<90%`)은 즉시 게이트 블로커로 간주.

## Insight

- 다중 프로젝트 적용을 안정화하려면 공통 스킬/훅은 “변경 불가 기본코어”로 고정하고, 프로젝트 고유 정보는 오버레이에서만 변경해야 합니다.
- `tag_manual` 이식 누락 이슈는 “의도적 제외/이식 누락/기능 변경”을 동일 카테고리로 합치지 말고, `TASK-AR-209`의 5분류(`kept/changed/deprecated/dropped/missing`)와 `TASK-AR-212`의 승인 근거 체계로 분리해야 합니다.
- `warn` 기반 통제가 `block` 규칙으로 전환되지 않으면 운영에서 퇴행이 빠르게 발생하므로, release-preflight/CI에서 자동 차단으로 연결해야 합니다.

## Decision

1. 공용 runtime/overlay 모델 확정: `TASK-AR-211`을 통해 프로젝트별 오버레이 파일 키를 강제한다.
2. 정확도 개선의 핵심: 정확성 개선은 `콘텐츠(정답셋)+트레이스(결정 경로)+리뷰(적대적 검토)` 합성 루프로 정량화한다.
3. 버전 업데이트 판단: 현재는 `Hold`; 다음 업데이트 가능 판정은 `TASK-AR-210`이 Owner 승인 템플릿(`Owner/decision_date/impact/next_action`)을 완성한 뒤 수행.

## Official Guidance 반영 점검

- Anthropic MCP/Claude Code는 tool/resource 경계, 인증·transport 제한, 런타임 출력관리 규칙을 문서/런타임 양쪽에서 enforce해야 함.
- OpenAI Agents SDK는 trace grading/agent eval/structured validation을 반복적 품질 루프로 권장.
- Codex 운영 모범은 실행 로그+승인 흐름+사람 검토 단계를 보안 흐름과 함께 운영할 것을 전제.

## Action Log

- AGENTIC_KNOWLEDGE_EVAL_PLAN.md의 release gate section과 source-of-truth 연동 포인트를 갱신한다.
- BACKLOG.md의 다음 세션 우선순위를 `TASK-AR-211` 선행으로 조정한다.
- STATUS.md의 Handoff Checklist에 오버레이 계약 단계와 블로커 정합 루프를 추가한다.
