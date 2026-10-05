#!/usr/bin/env bash
# Verify claude headless mode works with explicit models via SCRP proxy
export PATH="$HOME/.local/npm-prefix/bin:$PATH"
for m in scrp-assistant scrp-assistant-flash; do
  echo "=== model: $m ==="
  out=$(timeout 90 claude -p --model "$m" "Reply with exactly: MODEL-OK-$m" < /dev/null 2>&1)
  rc=$?
  echo "exit=$rc"
  echo "$out" | head -5
  echo
done
