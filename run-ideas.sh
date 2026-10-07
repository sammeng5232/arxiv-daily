#!/usr/bin/env bash
# Evening research layer: associative ideas + LaTeX drafts.
# Weekdays 21:30, after the 21:00 catch-up (waits on its lock if still busy).
# One email: the day's 1-3 research drafts (PDF+tex attached) + runners-up.
set -u
HD="$(cd "$(dirname "$0")" && pwd)"
export ARXIV_DAILY_HOME="$HD"
DATE="$(date +%F)"
mkdir -p "$HD/logs"
LOG="$HD/logs/$DATE.log"
exec > >(tee -a "$LOG") 2>&1

exec 9>"$HD/locks/run.lock"
flock -w 32400 9 || { echo "[ideas] lock wait timed out (9h) - exiting"; exit 0; }

echo "[ideas] ===== research layer $DATE start ====="
[ -f "$HD/mail.conf" ] || { echo "[ideas] FATAL: mail.conf missing"; exit 1; }

# 1. idea generation (idempotent: reuses ideas/<date>.json if present)
if ! python3 "$HD/ideas.py" "$DATE"; then
    echo "[ideas] FATAL: idea generation failed"
    exit 1
fi

# 2. pick the day's top ideas + draft them (skips already-drafted)
for ID in $(python3 "$HD/ideas.py" "$DATE" --pick auto); do
    echo "[ideas] drafting $ID"
    python3 "$HD/draft.py" "$DATE" "$ID" || echo "[ideas] draft $ID FAILED"
done

# 3. email drafts + runners-up (quiet when no drafts)
python3 "$HD/send_mail.py" --drafts "$DATE"

echo "IDEAS-DONE ts=$(date +%FT%T) date=$DATE"
echo "[ideas] ===== research layer done ====="
exit 0
