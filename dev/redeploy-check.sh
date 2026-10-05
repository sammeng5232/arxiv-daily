#!/usr/bin/env bash
# Redeploy check: syntax + HTML renderer smoke test + fetch fallback test
set -e
cd "$(dirname "$0")/.."
python3 -m py_compile fetch_papers.py report.py send_mail.py
echo "SYNTAX-OK"

echo "=== HTML renderer smoke test ==="
python3 - <<'EOF'
import send_mail
h = send_mail.md_to_html(open('papers/test-2026-10-05/reports/2610.03157.md').read())
print('HTML-OK', len(h), 'bytes')
assert '<h2>' in h and '<strong>' in h and '<code>' in h
print('has headings/bold/code: yes')
EOF

echo "=== listing-page fallback test (dry: just list ids, no downloads) ==="
python3 - <<'EOF'
import fetch_papers
ids, total = fetch_papers.listing_ids()
print('LISTING IDS:', ids, '| total ids on page (health signal):', total)
EOF
