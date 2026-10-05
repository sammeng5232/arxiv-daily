#!/usr/bin/env bash
# Check mail.conf is fully filled (masks secrets), then send the test email.
cd "$(dirname "$0")/.."

echo "=== mail.conf status ==="
if python3 - <<'EOF'
conf = {}
for line in open('mail.conf'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        conf[k.strip()] = v.strip()
missing = []
for k in ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASS', 'MAIL_FROM', 'MAIL_TO']:
    v = conf.get(k, '')
    if not v or 'FILL_ME' in v:
        print(f'  {k}: MISSING')
        missing.append(k)
    elif 'PASS' in k:
        print(f'  {k}: set ({len(v)} chars, hidden)')
    else:
        print(f'  {k}: {v}')
import sys
sys.exit(1 if missing else 0)
EOF
then
  echo
  echo "=== sending test email ==="
  bash mail-test.sh
else
  echo "NOT sending - fill the missing fields first."
  exit 1
fi
