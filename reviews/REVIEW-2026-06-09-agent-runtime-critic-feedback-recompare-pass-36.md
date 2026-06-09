# REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-36.md

## Bottom Line

`PASS-36`에서는 분산/멀티-메시지 운영 시나리오를 추가해 `message_queue` 경합을 한 단계 더 확장했다.

`parallel_recover_and_answer_multiple_messages_with_skewed_replay_delay` 를 통해 여러 메시지를 대상으로 stale claim 회수 + 재획득 + 답변 작성 + clock skew 경합을 병렬로 실행하고,
단일 메시지당 최소 1개 워커만 `answered` 전환을 달성하는지 검증했다.

또한 새 helper/테스트 경로에서의 실제 실행으로 `tests/test_template_message_queue.py`가 이전 대비 한 단계 확대되며, 전체 저장소 게이트도 재확인되었다.

## Signal

| 항목 | PASS-35 상태 | PASS-36 상태 | 근거 |
|---|---|---|---|
| 다중 메시지 병렬 stale recovery/claim 경합 | ✅ 확장 통과 | ✅ 추가 확장 통과 | 다중 메시지에서 시간 편차·지연 분포가 있는 worker 경쟁이 `answered` 결과로 정리됨 |
| 리플레이 지연 분포 내성 | ✅ 통과 | ✅ 보강 통과 | 각 worker에 `post_delay` 편차를 부여해 reply 작성/mark_answered 경로를 병렬로 검증 |
| 템플릿 self-contained 및 공개 게이트 | ✅ 유지 | ✅ 유지 | `pytest` 전체 및 publish/sanitize 게이트 재실행에서 clean 상태 유지 |
| 회귀 방어 신뢰도 | ✅ 강화 | ✅ 강화 | `tests/test_template_message_queue.py` 22개, `tests` 전체 149개 통과 |

## Insight

- 메시지 단위 병렬 경쟁에서 stale claim 처리 자체가 동시성의 핵심 병목임을 드러내고, 한 사이클 내 다중 메시지에 대한 회수-획득-응답 경로를 함께 확인했다.
- 이제 검증 범위가 단일 메시지 승자 보장에서 다중 메시지에서의 처리 분산성으로 넘어가, 실제 운영에서의 throughput/지연 편차 조건을 더 가까이 재현했다.
- 새 테스트에서 스큐 뒤처짐(now=1.0) 워커는 경합에 참여하되 승인 조건에서 탈락해야 함이 자연스럽게 확인되어, 시간 왜곡 조건에서의 안전성 의도를 보존한다.

## Decision

- `PASS-36`로 분산/원격 FS 경합 리스크의 적용 범위를 다중 메시지 경합+분산 지연까지 확장해 `claim/답변` 파이프라인 신뢰도를 강화했다.
- 다음 사이클(`PASS-37`)은 동일한 테스트 기반에서 메시지별 처리 지연 지표를 추적해, 고부하 하에서 특정 메시지의 `answered` 지연 분포와 starvation 가능성(완전 미응답 메시지)까지 정량화한다.

## Evidence (pass-36)

- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/test_template_message_queue.py -q`
  - `22 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests -q`
  - `149 passed`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli sanitize --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-check --root . --check`
  - `findings=0`
- ` $env:PYTHONPATH='src'; C:/Users/ycpig/AppData/Local/Programs/Python/Python310/python.exe -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source-pass36 --check`
  - `findings=0`

## Cross-Reference

- `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-35.md`
- `tests/test_template_message_queue.py`
