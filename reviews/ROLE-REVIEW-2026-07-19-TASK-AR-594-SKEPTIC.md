---
type: role-review
task_id: TASK-AR-594
claim_id: CLAIM-REVIEW-TASK-AR-594-skeptic-closeout
role: skeptic
verdict: fail
reviewed_commit: 402c189
reviewed_at: 2026-07-19T10:55:13+09:00
verification_commands:
  - "git show --format=fuller 402c189 -- scripts/taskset_dispatcher.py src/agent_runtime/templates/project/scripts/taskset_dispatcher.py tests/test_taskset_dispatcher.py"
  - "gh issue view 289 --json number,title,body,state,url,labels"
  - "gh search code TASKSET-TASK216-KPI-PROFILE-CONDITIONS --limit 20 --json repository,path,url,textMatches"
  - "gh api repos/ycpiglet/autofolio/contents/agents/project/initiatives/TASKSET-TASK216-KPI-PROFILE-CONDITIONS.md --jq .content"
  - "Fetch the downstream canonical record, parse its frontmatter/body, and print meta.tasks plus taskset_dispatcher._ordered_task_ids(body)"
  - "py -3.10 -m pytest tests/test_taskset_dispatcher.py tests/test_role_routing_wiring.py -q -p no:cacheprovider"
  - "py -3.10 scripts/regen_host_lock_if_needed.py --check"
  - "Get-FileHash -Algorithm SHA256 scripts/taskset_dispatcher.py and src/agent_runtime/templates/project/scripts/taskset_dispatcher.py"
  - "git diff --check 402c189^ 402c189"
findings:
  - id: SKEPTIC-594-001
    severity: critical
    summary: "The parser ignores the actual downstream canonical order, so GitHub #289 remains reproducible after commit 402c189."
---

# TASK-AR-594 Skeptic Role Review

## 판정

FAIL. 통합 커밋 `402c189`은 합성된 영어 `## Tasks` fixture에서는 순서를
보존하지만, GitHub #289를 발생시킨 실제 Autofolio canonical record에서는
순서를 전혀 읽지 못합니다. 보고된 결함의 원본 입력에 대한 회귀 검증이
누락됐고, 핵심 acceptance criterion은 충족되지 않았습니다.

## 차단 Finding

### SKEPTIC-594-001 — 실제 canonical 형식의 순서를 무시함 (Critical)

공개된 downstream 원본
`ycpiglet/autofolio:agents/project/initiatives/TASKSET-TASK216-KPI-PROFILE-CONDITIONS.md`
에는 순서가 다음 두 위치에 명시돼 있습니다.

```yaml
tasks:
  - TASK-219
  - TASK-220
  - TASK-217
```

- frontmatter의 `tasks` 배열
- body의 `## 포함 태스크` 섹션 아래 동일한 `tasks` 배열

그러나 새 `_canonical_task_order`는 frontmatter를 파싱한 뒤 `meta`의
`tasks`를 버리고 body만 `_ordered_task_ids`에 전달합니다.
`_ordered_task_ids`는 `Tasks`, `Task Order`, `Ordered Tasks`,
`Execution Order` 네 개의 영어 제목만 허용하므로 실제 `## 포함 태스크`
섹션도 무시합니다.

실제 downstream 파일을 GitHub API로 읽어 현재 통합 코드를 적용한 측정값은
다음과 같습니다.

```text
frontmatter_tasks= ['TASK-219', 'TASK-220', 'TASK-217']
parsed_body_order= []
```

따라서 `_tasks_for`는 `canonical_order`가 비어 있다고 판단해 변경 전과
동일한 `task_set_sort_key` fallback을 반환합니다. #289의 증거에 따르면 이
fallback의 첫 항목은 `TASK-217`이므로 요구 순서
`TASK-219 -> TASK-220 -> TASK-217`이 여전히 적용되지 않습니다.

## 증거 강도 검토

| 항목 | 측정 결과 | 판정 |
| --- | --- | --- |
| 실제 downstream canonical record 발견 | GitHub code search와 contents API로 원본 파일 및 정확한 순서 확인 | FAIL 원인 확정 |
| 실제 원본에 새 parser 적용 | frontmatter에는 3개 ID가 있으나 body parser 결과는 빈 목록 | FAIL |
| focused suite | `53 passed in 13.93s` | 테스트 자체는 PASS |
| fixture 충실도 | 실제 `tasks:` frontmatter/한국어 섹션 대신 새 `## Tasks` 표를 생성 | FAIL |
| live/template parity | 양쪽 SHA-256 모두 `1470C5B4CD8EFFB30E6FCF92819509EC7248ED70A3DDFBEF82402AF0C3453ADF` | PASS |
| host lock | `agent_runtime.lock.json is up to date` | PASS |
| commit whitespace | `git diff --check 402c189^ 402c189` exit 0 | PASS |

기존 W4b 및 independent-auditor 증거는 “downstream 원본 파일이 checkout에
없다”는 이유로 합성 fixture를 사용했지만, 원본은 공개 GitHub 저장소에서
조회 가능했습니다. 그 fixture가 입력 계약을 영어 표로 바꿔 버려 실제
회귀를 숨겼습니다. 테스트 통과, 미러 동등성, lock freshness는 구현 배포의
기계적 무결성만 입증하며 보고된 결함 해결을 입증하지 못합니다.

## 필요한 보정과 재검증

1. canonical frontmatter의 `tasks` 배열을 우선순위 있는 정본으로 읽고,
   유효한 문자열 목록·중복·다른 taskset ID를 방어적으로 처리해야 합니다.
2. body fallback이 필요하다면 실제 생성 계약의 `tasks:` 형식과 지역화된
   제목을 임의 열거가 아닌 구조적으로 처리해야 합니다.
3. Autofolio 원본 record를 최소한으로 복제한 regression fixture로
   `_tasks_for` 전체 순서와 `plan.next_task_id == TASK-219`를 검증해야 합니다.
4. 수정 후 focused suite, live/template parity, host lock, 실제 host update-plan
   및 plan 명령을 다시 실행해야 합니다.

## 범위 준수

코드, 테스트, claim 상태, `reviews/INDEX.md`, 커밋은 변경하지 않았습니다.
지정된 skeptic overlay review 문서만 추가했습니다.
