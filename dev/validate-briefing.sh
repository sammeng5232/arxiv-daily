#!/usr/bin/env bash
# Rebuild and re-send today's digest for one category (no LLM calls; reuses
# existing reports). Usage: dev/validate-briefing.sh [category]
set -e
cd "$(dirname "$0")/.."
CAT="${1:-econ.TH}"
case "$CAT" in
    math.CO) MAXP=30 ;;
    *)       MAXP=0  ;;
esac

DATE=$(date +%F)
DAY_DIR="papers/$DATE"
DIGEST="$DAY_DIR/reports/_digest-$CAT.md"

python3 build_digest.py "$DAY_DIR" "$DATE" "$CAT" "$MAXP"
echo "=== digest stats ==="
wc -c "$DIGEST"
head -12 "$DIGEST"
echo "..."
echo "=== sending ==="
python3 send_mail.py --digest "$DATE" "$DIGEST" --category "$CAT" \
    --attach-list "$DAY_DIR/reports/_digest-$CAT.files"
