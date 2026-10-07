#!/usr/bin/env bash
# arxiv-daily: one cron run for ONE category. Usage: run.sh [category]
# Categories: econ.TH, cs.GT, cs.DM, math.CO (math.CO skips papers > 15 pages).
# Day artifacts (papers/<DATE>/) are shared across categories: a paper
# cross-listed into two categories is downloaded and reported once, and both
# category digests reuse the same report. Processing state is per category
# (state/<category>.db), so each category retries its own failures.
# Safe to run repeatedly (flock + per-category state + sent marker).
# Usually invoked by run-all.sh, which loops over all categories.
set -u
CATEGORY="${1:-econ.TH}"
case "$CATEGORY" in
    math.CO) MAX_PAGES=15 ;;
    *)       MAX_PAGES=0  ;;
esac

HD="$(cd "$(dirname "$0")" && pwd)"
export ARXIV_DAILY_HOME="$HD"
DATE="$(date +%F)"
DAY_DIR="$HD/papers/$DATE"           # shared across categories
STATE_DB="$HD/state/$CATEGORY.db"    # per-category seen/retry state
LOG_DIR="$HD/logs"
mkdir -p "$DAY_DIR/reports" "$HD/state" "$LOG_DIR" "$HD/locks"
LOG="$LOG_DIR/$DATE.log"
exec > >(tee -a "$LOG") 2>&1

# one run at a time (waits up to 2h for a concurrent run to finish)
exec 9>"$HD/locks/run.lock"
flock -w 7200 9 || { echo "[run:$CATEGORY] lock wait timed out - exiting"; exit 0; }

echo "[run:$CATEGORY] ===== arxiv-daily $DATE start (max_pages=$MAX_PAGES) ====="
[ -f "$HD/mail.conf" ] || { echo "[run:$CATEGORY] FATAL: mail.conf missing"; exit 1; }

# 1. fetch new papers for this category
TMPJSON="/tmp/arxiv-papers-${CATEGORY//\./-}-$$.json"
echo "[run:$CATEGORY] fetching new papers..."
if python3 "$HD/fetch_papers.py" --date-dir "$DAY_DIR" --category "$CATEGORY" \
        --state-file "$STATE_DB" --max-pages "$MAX_PAGES" > "$TMPJSON"; then
    :
else
    RC=$?
    if [ "$RC" -eq 2 ]; then
        echo "[run:$CATEGORY] suspicious empty fetch - sending canary"
        python3 "$HD/health.py" canary "$CATEGORY" || true
        echo "[]" > "$TMPJSON"
    else
        echo "[run:$CATEGORY] FATAL: fetch failed with rc=$RC"
        exit 1
    fi
fi
COUNT=$(python3 -c "import json; print(len(json.load(open('$TMPJSON'))))" 2>/dev/null || echo 0)
echo "[run:$CATEGORY] $COUNT paper(s) to report"

# 2. per-paper: extract text + LLM report (reuse existing report for cross-lists)
OK=0; FAIL=0
i=0
while [ "$i" -lt "$COUNT" ]; do
    PID=$(python3 -c "import json; print(json.load(open('$TMPJSON'))[$i]['id'])")
    PDF="$DAY_DIR/$PID.pdf"; TXT="$DAY_DIR/$PID.txt"; REPORT="$DAY_DIR/reports/$PID.md"
    echo "[run:$CATEGORY] ----- $PID ($((i+1))/$COUNT) -----"
    if [ -s "$REPORT" ]; then
        echo "[run:$CATEGORY] report already exists (cross-listed paper) - reusing"
        python3 "$HD/state.py" --db "$STATE_DB" mark ok "$PID"
        OK=$((OK+1))
    else
        if [ ! -s "$TXT" ]; then
            python3 "$HD/extract_text.py" "$PDF" "$TXT" \
                || echo "[run:$CATEGORY] text extraction failed (report will use abstract only)"
            [ -f "$TXT" ] || : > "$TXT"
        fi
        if python3 "$HD/report.py" "$DAY_DIR/$PID.meta.json" "$TXT" "$REPORT"; then
            python3 "$HD/state.py" --db "$STATE_DB" mark ok "$PID"
            OK=$((OK+1))
        else
            python3 "$HD/state.py" --db "$STATE_DB" mark fail "$PID"
            FAIL=$((FAIL+1))
        fi
    fi
    i=$((i+1))
done
rm -f "$TMPJSON"

# 3. day themes (one extra LLM call over this category's papers)
if [ "$COUNT" -gt 0 ]; then
    THEMES="$DAY_DIR/reports/_themes-$CATEGORY.md"
    python3 "$HD/themes.py" "$DAY_DIR" "$CATEGORY" "$MAX_PAGES" > "$THEMES" || true
    [ -s "$THEMES" ] || rm -f "$THEMES"
fi

# 4. digest + email (once per category per day; re-sent only if new papers arrived)
python3 "$HD/build_digest.py" "$DAY_DIR" "$DATE" "$CATEGORY" "$MAX_PAGES"
DIGEST="$DAY_DIR/reports/_digest-$CATEGORY.md"
SENT_MARKER="$DAY_DIR/reports/_sent-$CATEGORY"
NPAPERS=$(grep -o 'announced today (new + cross-lists): \*\*[0-9]*\*\*' "$DIGEST" 2>/dev/null \
    | grep -o '[0-9]\+' | head -1)
NPAPERS="${NPAPERS:-0}"
if [ "$((OK+FAIL))" -gt 0 ] || { [ ! -e "$SENT_MARKER" ] && [ "$NPAPERS" -gt 0 ]; }; then
    if python3 "$HD/send_mail.py" --digest "$DATE" "$DIGEST" --category "$CATEGORY" \
            --attach-list "$DAY_DIR/reports/_digest-$CATEGORY.files"; then
        touch "$SENT_MARKER"
    else
        echo "[run:$CATEGORY] WARNING: email sending failed"
    fi
else
    echo "[run:$CATEGORY] nothing new to email (processed=$((OK+FAIL)) announced=$NPAPERS)"
fi

echo "RUN-DONE ts=$(date +%FT%T) category=$CATEGORY date=$DATE fetched=$COUNT ok=$OK fail=$FAIL"
echo "[run:$CATEGORY] ===== done ($OK ok, $FAIL fail) ====="
exit 0
