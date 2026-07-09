#!/bin/bash
set -euo pipefail

cd /home/student/Documents/study/std01

echo "=== $(date '+%F %T') push 시작 ==="
git push origin main
echo "=== $(date '+%F %T') push 완료 ==="
