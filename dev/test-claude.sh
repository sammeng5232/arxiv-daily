#!/usr/bin/env bash
# Verify claude headless mode works with explicit models via the SCRP gateway
export PATH="$HOME/.local/npm-prefix/bin:$PATH"
for m in glm-5.3 glm-5.3-1 glm-5.3-2; do
  echo "=== model: $m ==="
  out=$(timeout 90 claude -p --model "$m" "Reply with exactly: MODEL-OK-$m" < /dev/null 2>&1)
  rc=$?
  echo "exit=$rc"
  echo "$out" | head -5
  echo
done
