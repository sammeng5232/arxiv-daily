#!/usr/bin/env bash
# Install / refresh the arxiv-daily cron schedule (idempotent).
# Weekdays 14:00: run all four categories (one email per category).
# Weekdays 21:00: catch-up run (late announcements + retries; never duplicates).
# Mondays 09:00: heartbeat email.
set -e
HD="$(cd "$(dirname "$0")" && pwd)"
CRON_FILE="$HD/.crontab.current"
crontab -l 2>/dev/null | grep -v "arxiv-daily" > "$CRON_FILE" || true
{
    echo "# arxiv-daily: arXiv digests (econ.TH, cs.GT, cs.DM, math.CO) - one email per category per weekday"
    echo "0 14 * * 1-5 $HD/run-all.sh >> $HD/logs/cron.log 2>&1"
    echo "# arxiv-daily: catch-up run (late announcements, retries; no duplicate emails)"
    echo "0 21 * * 1-5 $HD/run-all.sh >> $HD/logs/cron.log 2>&1"
    echo "# arxiv-daily: weekly heartbeat email"
    echo "0 9 * * 1 python3 $HD/health.py heartbeat >> $HD/logs/cron.log 2>&1"
} >> "$CRON_FILE"
crontab "$CRON_FILE"
rm -f "$CRON_FILE"
echo "[cron] installed:"
crontab -l | grep "arxiv-daily"
