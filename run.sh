#!/usr/bin/env bash
# arxiv-daily: fetch new econ.TH papers, generate LLM reports, email one daily briefing.
# Designed to run under cron (no tty, minimal env). Lock-protected.
# fetch exit code 2 (= both sources suspiciously empty) triggers a throttled
# canary email on weekdays via health.py.
set -u
HD="$(cd "$(dirname "$0")" && pwd)"
export ARXIV_DAILY_HOME="$HD"
export PATH="$HOME/.local/npm-prefix/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
DATE="$(date +%F)"
DAY_DIR="$HD/papers/$DATE"
LOG_DIR="$HD/logs"
mkdir -p "$DAY_DIR" "$LOG_DIR" "$HD/locks"

# --- prevent overlapping runs (14:00 + 21:00 catch-up) ---
exec 9>"$HD/locks/run.lock"
flock -n 9 || { echo "[$(date '+%F %T')] another run in progress, exiting"; exit 0; }

exec > >(tee -a "$LOG_DIR/$DATE.log") 2>&1
echo "================ arxiv-daily run $(date '+%F %T') ================"

# --- 1. fetch new papers (JSON list on stdout; rc 2 = suspicious empty) ---
PAPERS_JSON="$(python3 "$HD/fetch_papers.py" --date-dir "$DAY_DIR")"; FETCH_RC=$?
COUNT="$(printf '%s' "$PAPERS_JSON" | python3 -c 'import json,sys
try:
    print(len(json.load(sys.stdin)))
except Exception:
    print(-1)')"
if [ "$COUNT" = "-1" ]; then
  echo "[run] FETCH CRASHED (unparseable output) - aborting"
  DOW=$(date +%u)
  if [ "$DOW" -le 5 ]; then python3 "$HD/health.py" canary; fi
  exit 1
fi
echo "[run] new papers today: $COUNT"
if [ "$COUNT" = "0" ]; then
  if [ "$FETCH_RC" = "2" ]; then
    DOW=$(date +%u)
    if [ "$DOW" -le 5 ]; then
      echo "[run] WARNING: both fetch sources empty/unusable on a weekday - sending canary"
      python3 "$HD/health.py" canary
    else
      echo "[run] both fetch sources empty (weekend - no canary)"
    fi
  else
    echo "[run] nothing to do."
  fi
  exit 0
fi

# --- 2. per paper: extract text, generate report ---
mkdir -p "$DAY_DIR/reports"
OK=0; FAIL=0; FAILED_LIST=""
while IFS= read -r paper_json; do
  PID="$(printf '%s' "$paper_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
  TITLE="$(printf '%s' "$paper_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["title"])')"
  echo "---- paper $PID : $TITLE"

  TXT="$DAY_DIR/$PID.txt"
  if [ ! -s "$TXT" ]; then
    python3 "$HD/extract_text.py" "$DAY_DIR/$PID.pdf" "$TXT" || true
  fi

  REPORT="$DAY_DIR/reports/$PID.md"
  if python3 "$HD/report.py" "$DAY_DIR/$PID.meta.json" "$TXT" "$REPORT"; then
    OK=$((OK+1))
    python3 "$HD/state.py" mark ok "$PID"
  else
    FAIL=$((FAIL+1)); FAILED_LIST="$FAILED_LIST $PID"
    python3 "$HD/state.py" mark fail "$PID"
    echo "[run] REPORT FAILED for $PID (marked for retry if attempts remain)"
  fi
done < <(printf '%s' "$PAPERS_JSON" | python3 -c '
import json, sys
for p in json.load(sys.stdin):
    print(json.dumps(p))')

# --- 3. day-theme synthesis (one extra LLM call, only when >= 2 reports) ---
THEMES="$DAY_DIR/reports/_themes.md"
python3 "$HD/themes.py" "$DAY_DIR" > "$THEMES" || true
[ -s "$THEMES" ] || rm -f "$THEMES"

# --- 4. build + send the single daily briefing ---
python3 "$HD/build_digest.py" "$DAY_DIR" "$DATE" "$OK" "$FAIL"
python3 "$HD/send_mail.py" --digest "$DATE" "$DAY_DIR/reports/_digest.md" --attach-dir "$DAY_DIR" \
  && echo "[run] daily briefing mailed" || echo "[run] DAILY BRIEFING MAIL not sent (rc=$?)"

echo "[run] done. ok=$OK fail=$FAIL${FAILED_LIST:+ failed:$FAILED_LIST}"
exit 0
