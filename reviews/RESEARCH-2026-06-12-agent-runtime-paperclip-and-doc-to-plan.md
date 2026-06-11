# RESEARCH-2026-06-12 — Paperclip 분석 및 문서→플랜 파이프라인 기획

- Bottom Line: Owner가 지목한 오픈소스 **Paperclip**(github.com/paperclipai/paperclip, paperclip.ing, MIT)은 "AI 에이전트를 회사처럼 운영"하는 오케스트레이터로 agent_runtime과 비전이 거의 동일하다. 기능 전수 매핑 결과 agent_runtime이 이미 보유한 영역(거버넌스·증거·게이트)과 Paperclip이 앞선 영역(에이전트별 예산 하드 스톱, heartbeat 스케줄링, 멀티 컴퍼니, 계정/API 키)을 식별했고, 채택분과 Owner의 신규 비전(pitch deck→자동 task 등록)을 `TASKSET-AR-DOC-TO-PLAN`(TASK-AR-366~368)으로 등록한다.
- Signal: Paperclip 핵심 사양 — Node.js+React, 임베디드 Postgres, self-hosted, "If it can receive a heartbeat, it's hired"(Claude Code/Codex/Cursor/커스텀 CLI 호환), org chart·예산·거버넌스·goal alignment·atomic task checkout·감사 로그·company export/import·플러그인(out-of-process worker)·멀티테넌시.
- Insight: 양쪽의 차별점이 명확하다. agent_runtime = **증거·게이트·측정 가능한 자가 개선**(RSI, eval, casebook)이 강함. Paperclip = **운영 경제학**(예산 하드 스톱, 비용 이벤트, heartbeat 수명주기)과 **제품화**(계정, 멀티 컴퍼니, 플러그인)가 강함. 따라서 모방이 아니라 보완 채택이 옳다.
- Decision: ① 문서→플랜 파이프라인(Owner 신규 비전)을 P1로 등록, ② Paperclip 갭 분석을 분석 태스크로 등록, ③ 실측 지표 캡처·다중 정렬 기준을 P1로 등록, ④ 계정/커뮤니티/랭킹은 Idea Vault 확장(IV-006 갱신 + IV-012 신설).

## 1. Paperclip 기능 인벤토리 → agent_runtime 매핑

| Paperclip 기능 | agent_runtime 현황 | 판정 |
| --- | --- | --- |
| Org Chart (역할·직급·보고 라인·권한·예산) | TEAMS/ORG/roles 문서 + 조직도 뷰 계획(AR-324) | 보유/진행 — 권한·예산 축만 추가 채택 |
| Goal Alignment (task→회사 미션 추적) | goal/taskset/milestone 체계 + Roadmap(AR-325) | 보유 |
| Atomic task checkout (실행 잠금, 중복 작업 방지) | task_claims + race-safe claiming(AR-314 planned) | 동형 — AR-314가 잠금 강화 |
| **에이전트별 월 예산 + 하드 스톱** ("limit 도달 시 정지") | est_tokens만 존재, 실측·강제 없음 | **채택 → AR-368** (실측 캡처가 전제) |
| **비용 추적** (company/agent/project/goal/provider/model 별 + 경고 임계값) | 없음 (AR-339 대시보드 계획에 일부) | **채택 → AR-368** |
| **Heartbeat 실행** (예약 wakeup, 예산 체크, 워크스페이스 해석, 스킬 로딩, 구조화 로그) | 세션 단위 실행 + cron 예약(AR-335 계획) | 부분 채택 — heartbeat 수명주기 규약은 AR-367 분석 |
| Routines (cron/webhook/API 트리거 반복 작업) | AR-335 캘린더/예약 계획과 동형 | 보유(계획) |
| Workspaces (git worktree, operator branch, dev server) | taskset_dispatcher worktree 체계 | 보유 |
| Persistent agent state (heartbeat 간 컨텍스트 유지) | NEXT-SESSION-POINTER + 핸드오프 | 동형 |
| Runtime skill injection | skills/ + 스킬 패키징(AR-316 planned) | 보유(계획) |
| Governance & Approvals (board 워크플로, pause/resume/terminate) | owner gates + Planner 승인(AR-317) | 보유 — terminate/pause 제어만 UI 채택 후보 |
| 감사 로그 (full tool-call tracing, immutable) | pane_events + A2A 메시지 로그(AR-311 완료) | 보유 |
| Company export/import (시크릿 스크럽, 충돌 처리) | AR-333 내보내기/가져오기 계획과 동형 | 보유(계획) — 시크릿 스크럽 요건만 추가 |
| **멀티 컴퍼니/테넌시 (완전 데이터 격리)** | 멀티 호스트 프로젝트(AR-341 스위처) — 격리 약함 | 부분 채택 → AR-367 분석 |
| **계정/Identity (board 사용자, agent API 키, JWT)** | 없음 (로컬 단일 사용자 원칙) | **Idea Vault** IV-006 확장 |
| Plugin system (out-of-process workers) | AR-341 위젯 확장 포인트(선언적) | 부분 — 프로세스 분리 모델은 AR-367 분석 |
| 시크릿 관리 (암호화 저장, export 시 스크럽) | 로컬 설정 파일 원칙(AR-365) | 채택 요건으로 흡수 |

문서/아이디어 인입(pitch deck→plan)은 Paperclip README에서 확인되지 않음 — **이 부분은 agent_runtime이 선점할 수 있는 차별 영역**.

## 2. 문서→플랜 파이프라인 (Owner 신규 비전, TASK-AR-366)

- 비전: pitch deck/기획서/아이디어 문서(PPT, PDF, HTML, Word, md)를 넣으면 → 스스로 분석 → plan 작성 → 실현 가능한 task로 분해 → taskset 자동 등록.
- 기존 자산 위에 정확히 얹힌다: 분해 규약은 PM-OPERATING-SYSTEM(AR-342~350)의 project→taskset→task→unit 계층과 unit readiness gate를 그대로 사용하고, 자동 등록은 B-mode planning gate(제안→Owner 승인) 경유로 안전하게.
- 단계: ① 파싱(PDF/PPTX/DOCX/HTML→md 정규화) ② 구조 분석(목표/기능/제약 추출) ③ plan 초안(milestone/taskset 제안) ④ task 분해(unit spec 수준) ⑤ planning 제안으로 제출 → 승인 시 레지스트리 등록.
- 게임화 연계: 인입된 "사업 문서"가 사업 단계 칭호(AR-363)의 입력이 될 수 있음 (pitch deck=garage, 첫 릴리스=startup …).

## 3. 실측 지표와 다중 평가/정렬 기준 (TASK-AR-368)

- Owner 요구: 우선순위·난이도·**예상/실제 토큰**·**예상/실제 작업 시간**·부서 등 다양한 기준으로 task/taskset 정렬·필터. "토큰 사용량은 적은데 사업 성숙도는 높다" 같은 다요소 평가.
- 현황: est_hours/est_tokens만 있고 actual_* 캡처가 없다. 부서(team) 필드는 AR-337 계획에 있음.
- 설계: task frontmatter에 `actual_tokens`, `actual_hours`, `team` 표준화 → 세션/클레임 로그에서 자동 집계 → AR-322 공통 필터·AR-339 대시보드에 노출. 효율 지표 = 성과(완료·게이트 통과) / 비용(토큰·시간) — AR-363 성장 시스템의 "효율 스탯"과 단일 정의 공유.

## 4. 계정/커뮤니티/랭킹 (Idea Vault)

- Owner 비전: 사용자 계정, 유저 간 소통, 레벨 랭킹(예: 저토큰·고성숙도 리더보드).
- 판정: 방향 유효하나 로컬 단일 사용자 원칙과 충돌 — 전제(계정 시스템, 서버, 프라이버시)가 큼. IV-006을 "계정+커뮤니티+랭킹"으로 확장하고 재검토 기한을 유지. Paperclip의 Identity 모델(board user, agent API key, JWT)이 부활 시 참조 설계가 된다.

## 5. 출처

- github.com/paperclipai/paperclip (README, MIT) · paperclip.ing · github.com/agencyenterprise/paperclip-ai (동명 별개 프로젝트 — 혼동 주의)

- Action Board: TASK-AR-366(문서→플랜), TASK-AR-367(Paperclip 갭 분석·채택 결정), TASK-AR-368(실측 지표+다중 정렬) 등록. IDEA-VAULT IV-006 갱신, IV-012 추가.
- Next: AR-367 분석 결과에 따라 예산 하드 스톱/heartbeat/멀티테넌시의 구현 태스크를 후속 등록.
