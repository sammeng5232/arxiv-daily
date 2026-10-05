#!/usr/bin/env bash
# arxiv-daily: run every configured category sequentially, one email each.
# Invoked by cron at 14:00 (main) and 21:00 (catch-up) on weekdays.
# Override the category list with ARXIV_DAILY_CATEGORIES="a b c".
set -u
HD="$(cd "$(dirname "$0")" && pwd)"
CATEGORIES="${ARXIV_DAILY_CATEGORIES:-econ.TH cs.GT cs.DM math.CO}"
RC=0
for CAT in $CATEGORIES; do
    echo ""
    echo "################ category: $CAT ################"
    if ! bash "$HD/run.sh" "$CAT"; then
        echo "[run-all] WARNING: $CAT run failed"
        RC=1
    fi
done
exit $RC
