#!/usr/bin/env bash
# Send one real report email to verify SMTP settings in mail.conf.
cd "$(dirname "$0")/.."
TD=papers/test-2026-10-05
python3 send_mail.py --paper "$TD/2610.03157.meta.json" "$TD/reports/2610.03157.md"
