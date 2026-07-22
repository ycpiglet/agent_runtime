---
type: role-review
task_id: TASK-AR-601
claim_id: CLAIM-REVIEW-TASK-AR-601-skeptic-closeout
role: skeptic
verdict: pass
reviewed_commit: aa3d9a5
w4b_commit: 95a89ed
reviewed_at: 2026-07-19T11:40:51+09:00
supersedes: reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC.md
resolves_findings:
  - SKEPTIC-601-001
  - SKEPTIC-601-002
  - SKEPTIC-601-003
verification_commands:
  - "git show --format=fuller aa3d9a5"
  - "git show --stat 95a89ed"
  - "Release overlay fixtures with markers true, 'true', 1, and '1' under AR_ROLE_ROUTING=1; enumerate final claim count and nested IDs"
  - "Inject OSError from role_routing.atomic_io.write_json_atomic; enumerate deterministic claim/handoff/log artifacts afterward"
  - "Create a directory at the deterministic overlay handoff path, release the primary claim, and inspect primary status plus overlay JSON/log"
  - "Exercise committed config true plus AR_ROLE_ROUTING=0 and committed config false plus AR_ROLE_ROUTING=1"
  - "py -3.10 -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q -p no:cacheprovider"
  - "py -3.10 scripts/regen_host_lock_if_needed.py --check"
  - "git diff --exit-code 652f46f..aa3d9a5 -- tests/fixtures/host/agent_runtime.lock.json"
  - "git diff --check 652f46f..aa3d9a5"
findings: []
---

# TASK-AR-601 Skeptic Hardening Recheck

## 판정

PASS. hardening commit `aa3d9a5`는 이전 skeptic 검토의 세 finding을 모두
닫았습니다. 이전과 동일한 failure-injection 및 malformed-marker 재현을 반복했고,
nested overlay, orphan artifact, kill-switch 우선순위 결함이 더 이상 발생하지
않았습니다. W4b commit `95a89ed`의 승인 결론과 독립 측정값이 일치합니다.

이 문서는
`reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC.md`의 FAIL 판정을
supersede합니다. 원본 FAIL 문서는 hardening 전 결함의 역사적 증거로 유지됩니다.

## Finding 재검증

### SKEPTIC-601-001 — CLOSED

정상 overlay claim의 marker만 바꾸어 release한 결과입니다.

| marker | primary release | overlay release | 최종 claim 수 | nested claim |
| --- | ---: | ---: | ---: | --- |
| `true` | 0 | 0 | 2 | 없음 |
| `"true"` | 0 | 0 | 2 | 없음 |
| `1` | 0 | 0 | 2 | 없음 |
| `"1"` | 0 | 0 | 2 | 없음 |

`cmd_release`의 보수적인 `is_overlay` 판정이 boolean, 숫자, 알려진 문자열
marker를 정규화하고 기타 비-null 객체는 fail-closed overlay로 취급합니다.
이전 재현에서 생성됐던 `CLAIM-REVIEW-REVIEW-*` ID는 한 건도 나타나지
않았습니다.

### SKEPTIC-601-002 — CLOSED

claim JSON publish에 동일한 `OSError("injected-json-failure")`를 주입한 뒤
deterministic prefix의 파일을 열거했습니다.

```json
{
  "exception": "injected-json-failure",
  "remaining_artifacts": []
}
```

handoff와 log는 publish 성공 후 추적되고, 이후 단계 실패 시 역순 rollback됩니다.
또한 기존의 JSON-path directory no-op 대신 실제 handoff artifact 경로에 디렉터리를
만들어 release seam을 실패시켰습니다.

```json
{
  "release_rc": 0,
  "primary_status": "released",
  "overlay_json_exists": false,
  "overlay_log_exists": false,
  "handoff_collision_is_dir": true
}
```

따라서 실제 artifact publish fault가 발생해도 완료된 primary release는 보존되고,
불완전 overlay JSON/log는 노출되지 않습니다.

### SKEPTIC-601-003 — CLOSED

config와 환경의 충돌 우선순위를 실제 생성 결과로 확인했습니다.

| committed config | environment | enabled | 생성 수 |
| --- | --- | --- | ---: |
| `true` | `AR_ROLE_ROUTING=0` | false | 0 |
| `false` | `AR_ROLE_ROUTING=1` | true | 1 |
| `true` | 환경값 없음 | true | 1 |
| `false` | 환경값 없음 | false | 0 |
| config 없음 | 환경값 없음 | false | 0 |

명시적 환경값이 committed config보다 우선하므로 `0`은 실제 kill switch,
`1`은 실제 emergency override로 동작합니다. 환경값이 없을 때만 config로
fallback합니다.

## 전체 검증 결과

| 항목 | 결과 |
| --- | --- |
| Focused routing/dispatcher suite | `73 passed in 25.34s` |
| Host lock | current |
| Lock non-drift | `652f46f..aa3d9a5`에서 변경 없음 |
| Diff quality | whitespace 오류 없음 |
| Truthy marker nested overlays | 4/4 모두 0 |
| JSON failure orphan artifacts | 0 |
| 실제 release artifact fault | primary release 보존 |
| Config/env precedence | OFF/ON 양방향 통과 |

## 잔여 위험

- rollback 중 filesystem 자체가 `unlink`를 거부하면 cleanup은 best-effort이므로
  sidecar가 남을 수 있습니다. 다만 claim JSON은 publish되지 않으며 이는 현재
  atomic I/O 계층이 보장할 수 있는 합리적인 경계입니다.
- 빈 환경값은 명시적 OFF가 아니라 unset으로 간주되어 config로 fallback합니다.
  운영 kill switch는 검증된 값 `0`을 사용해야 합니다.
- 생성 host의 role-routing 제품화는 기록된 T3 live-checkout 범위 밖입니다.

위 잔여 위험은 현재 acceptance criterion을 차단하지 않습니다.

## 범위 준수

코드, claim, release 상태, `reviews/INDEX.md`, 커밋은 변경하지 않았습니다.
이 skeptic recheck 문서만 추가했습니다.
