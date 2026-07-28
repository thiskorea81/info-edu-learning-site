#!/bin/bash
# 다른 컴퓨터에서 push한 커밋을 주기적으로 pull하고,
# data/ 또는 backend/ 변경이 포함된 경우에만 study-backend.service를 재시작한다.
#
# study-auto-pull.timer(1시간마다)가 이 스크립트를 실행한다.
# 이 스크립트는 커밋을 만들지 않고 pull만 한다 — 로컬 커밋/push는
# 기존 commit_and_deploy.sh / daily_push.sh가 그대로 담당한다.
set -euo pipefail

cd /home/student/Documents/study/std01

echo "=== $(date '+%F %T') 자동 pull 시작 ==="

BEFORE=$(git rev-parse HEAD)

git fetch origin main --quiet

AHEAD=$(git rev-list HEAD..origin/main --count)
if [ "$AHEAD" -eq 0 ]; then
  echo "=== $(date '+%F %T') origin/main에 새 커밋 없음, 종료 ==="
  exit 0
fi

echo "origin/main에 새 커밋 ${AHEAD}개 발견, pull 시도"

if ! git pull --no-rebase origin main --quiet; then
  echo "pull 실패(충돌 가능성) — merge 중단" >&2
  git merge --abort 2>/dev/null || true
  echo "=== $(date '+%F %T') 자동 pull 실패 ===" >&2
  exit 1
fi

AFTER=$(git rev-parse HEAD)
CHANGED=$(git diff --name-only "$BEFORE" "$AFTER")
echo "변경된 파일:"
echo "$CHANGED"

if echo "$CHANGED" | grep -qE '^(data/|backend/)'; then
  echo "data/ 또는 backend/ 변경 포함 — study-backend.service 재시작"
  systemctl --user restart study-backend.service
  sleep 2
  if ! systemctl --user is-active --quiet study-backend.service; then
    echo "재시작 실패: study-backend.service가 실행 중이 아닙니다." >&2
    exit 1
  fi
  if curl -sf "http://127.0.0.1:8000/api/standards" -o /dev/null; then
    echo "반영 확인 완료"
  else
    echo "반영 확인 실패: /api/standards 응답 없음" >&2
    exit 1
  fi
else
  echo "data/·backend/ 변경 없음 — 재시작 생략"
fi

echo "=== $(date '+%F %T') 자동 pull 완료 ==="
