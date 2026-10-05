#!/usr/bin/env bash
# Install/refresh the arxiv-daily cron entries (idempotent).
set -e
HD="$(cd "$(dirname "$0")" && pwd)"
CRON_TMP=$(mktemp)
crontab -l 2>/dev/null | grep -v "arxiv-daily" > "$CRON_TMP" || true
{
  echo "# arxiv-daily: arXiv category digest via Claude - weekdays 14:00 + 21:00 catch-up (server local time)"
  echo "0 14 * * 1-5 $HD/run.sh >> $HD/logs/cron.log 2>&1"
  echo "0 21 * * 1-5 $HD/run.sh >> $HD/logs/cron.log 2>&1"
} >> "$CRON_TMP"
crontab "$CRON_TMP"
rm -f "$CRON_TMP"
echo "--- installed crontab: ---"
crontab -l
