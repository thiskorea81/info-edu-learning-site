#!/bin/bash
set -euo pipefail

cd /home/student/Documents/study/std01

PROMPT="$(cat scripts/daily_problem_prompt.txt)"

claude -p "$PROMPT" \
  --dangerously-skip-permissions \
  --output-format text
