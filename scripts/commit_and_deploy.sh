#!/bin/bash
# 커밋 + 로컬 배포(백엔드 재시작 + 반영 확인)를 한 번에 처리하는 스크립트.
#
# 사용법:
#   scripts/commit_and_deploy.sh "커밋 메시지" 파일1 [파일2 ...]
#
# 예:
#   scripts/commit_and_deploy.sh "디논 03단원 추가" \
#     data/materials/디논0301.json data/questions/디논0301.json
#
# git add -A를 쓰지 않고 지정한 파일만 스테이징한다(무관한 변경 실수 커밋 방지).
# 원격 push는 하지 않는다 — study-daily-push.timer가 매일 09:00에 자동으로 push한다.
set -euo pipefail

cd /home/student/Documents/study/std01

if [ "$#" -lt 2 ]; then
  echo "사용법: $0 \"커밋 메시지\" 파일1 [파일2 ...]" >&2
  exit 1
fi

MSG="$1"
shift
FILES=("$@")

echo "=== $(date '+%F %T') 커밋 시작 ==="
git add -- "${FILES[@]}"
git status --short -- "${FILES[@]}"
git commit -m "$MSG

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"

echo "=== $(date '+%F %T') 백엔드 재시작(배포) ==="
systemctl --user restart study-backend.service
sleep 2
systemctl --user is-active --quiet study-backend.service || {
  echo "배포 실패: study-backend.service가 실행 중이 아닙니다." >&2
  exit 1
}

echo "=== $(date '+%F %T') 반영 확인 ==="
if ! curl -sf "http://127.0.0.1:8000/api/standards" -o /dev/null; then
  echo "배포 확인 실패: /api/standards 응답 없음" >&2
  exit 1
fi

echo "=== $(date '+%F %T') 완료: 커밋 + 로컬 배포 성공 (push는 매일 09:00 자동 실행) ==="
