#!/usr/bin/env bash
# End-to-end test of arxiv-daily pipeline on one real paper (2610.03157)
set -e
cd "$(dirname "$0")/.."
TD=papers/test-2026-10-05
mkdir -p "$TD/reports"

echo "=== 1. fetch + PDF download + metadata ==="
python3 fetch_papers.py --date-dir "$TD" --category econ.TH \
    --state-file /tmp/arxiv-test-state.db --test-id 2610.03157 > /tmp/test.json
python3 - <<'EOF'
import json
d = json.load(open('/tmp/test.json'))
print('PAPER :', d[0]['title'])
print('AUTHORS:', ', '.join(d[0]['authors'][:6]))
print('CATS  :', d[0]['primary_category'], '|', ', '.join(d[0]['categories']))
EOF

echo "=== 2. PDF text extraction ==="
python3 extract_text.py "$TD/2610.03157.pdf" "$TD/2610.03157.txt"

echo "=== 3. LLM report via claude -p (this can take a few minutes) ==="
time python3 report.py "$TD/2610.03157.meta.json" "$TD/2610.03157.txt" "$TD/reports/2610.03157.md"

echo "=== 4. report preview (first 60 lines) ==="
head -60 "$TD/reports/2610.03157.md"
echo
echo "=== files ==="
ls -la "$TD"
