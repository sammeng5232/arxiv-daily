#!/usr/bin/env bash
# Smoke tests for the arxiv-daily pipeline (safe: no emails, no LLM calls,
# no writes to real state). Run after any deploy: bash dev/smoke-test.sh
set -e
cd "$(dirname "$0")/.."
export ARXIV_DAILY_HOME="$(pwd)"

echo "=== 1. syntax check ==="
python3 -m py_compile fetch_papers.py extract_text.py report.py send_mail.py \
    state.py health.py themes.py build_digest.py
echo "SYNTAX-OK"

echo
echo "=== 2. state.py: legacy compat + retry accounting (isolated fixture) ==="
T=$(mktemp -d)
printf '2610.03146\n2610.03157\n' > "$T/seen.db"
ARXIV_DAILY_HOME="$T" python3 state.py stats
ARXIV_DAILY_HOME="$T" python3 state.py mark fail 0000.99999
ARXIV_DAILY_HOME="$T" python3 state.py stats
ARXIV_DAILY_HOME="$T" python3 state.py mark fail 0000.99999
ARXIV_DAILY_HOME="$T" python3 state.py mark fail 0000.99999
ARXIV_DAILY_HOME="$T" python3 state.py stats
echo "--- fixture seen.db ---"
cat "$T/seen.db"
rm -rf "$T"

echo
echo "=== 3. fetch_papers.py: dry run against live sources (no downloads) ==="
DRY_DIR=$(mktemp -d)
python3 fetch_papers.py --date-dir "$DRY_DIR" > /tmp/fetch-out.json
RC=$?
echo "fetch rc=$RC (0 expected; 2 would mean suspicious-empty)"
python3 -c 'import json; d = json.load(open("/tmp/fetch-out.json")); print("papers returned:", len(d))'
rm -rf "$DRY_DIR" /tmp/fetch-out.json

echo
echo "=== 4. health.py: heartbeat + canary dry-runs ==="
python3 health.py heartbeat --dry-run | head -12
echo "---"
python3 health.py canary --dry-run | head -8

echo
echo "=== 5. build_digest.py: isolated rebuild (no email, real files untouched) ==="
DATE=$(date +%F)
if [ -d "papers/$DATE" ]; then
  T=$(mktemp -d)
  cp papers/"$DATE"/*.meta.json "$T/" 2>/dev/null || true
  mkdir -p "$T/reports"
  cp papers/"$DATE"/reports/*.md "$T/reports/" 2>/dev/null || true
  N=$(ls "$T"/reports/*.md 2>/dev/null | grep -v _digest | grep -v _themes | wc -l)
  python3 build_digest.py "$T" "$DATE" "$N" 0 || true
  echo "--- digest head ---"
  head -14 "$T/reports/_digest.md"
  rm -rf "$T"
else
  echo "(no papers/$DATE directory yet - skipping)"
fi

echo
echo "SMOKE TESTS DONE"
