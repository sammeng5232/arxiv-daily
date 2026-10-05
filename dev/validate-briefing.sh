#!/usr/bin/env bash
# Validate the new single-briefing format: rebuild today's digest from existing
# reports (no LLM calls) and send it.
set -e
cd "$(dirname "$0")/.."
python3 -m py_compile send_mail.py run.sh 2>/dev/null || python3 -m py_compile send_mail.py
echo SYNTAX-OK

DATE=$(date +%F)
DAY_DIR="papers/$DATE"
DIGEST="$DAY_DIR/reports/_digest.md"

OK=$(ls "$DAY_DIR"/reports/*.md 2>/dev/null | grep -v _digest | wc -l)
python3 - "$DAY_DIR" "$DATE" "$OK" 0 > "$DIGEST" <<'PYEOF'
import glob, json, os, re, sys
day_dir, date, ok, fail = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
metas = sorted(glob.glob(os.path.join(day_dir, "*.meta.json")))
parts = [f"# arXiv econ.TH daily briefing - {date}", "",
         f"Papers announced today (new + cross-lists): **{ok + fail}**. "
         f"Reports generated: **{ok}**." + (f" Failures: {fail}." if fail else ""), "",
         "## Overview", ""]
toc, full = [], []
for mp in metas:
    m = json.load(open(mp))
    pid = m["id"]
    rp = os.path.join(day_dir, "reports", f"{pid}.md")
    auth = ", ".join(m.get("authors", [])[:6]) + (" et al." if len(m.get("authors", [])) > 6 else "")
    if os.path.exists(rp):
        rep = open(rp, encoding="utf-8").read()
        m2 = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
        tldr = re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else "(no TL;DR)"
        toc.append(f"**{m['title']}** - {auth} ([arXiv:{pid}]({m.get('abs_url','')}))\n\n> {tldr}")
        full.append(rep.rstrip())
    else:
        toc.append(f"**{m['title']}** - {auth} (arXiv:{pid})\n\n> *report generation failed - PDF on server*")
        full.append(f"# {m['title']}\n\nReport generation failed; PDF available on the server.")
parts.extend(toc)
parts.append("\n---\n")
parts.append("# Full reports")
parts.extend(full)
print("\n\n".join(parts))
PYEOF

echo "=== digest stats ==="
wc -c "$DIGEST"
head -12 "$DIGEST"
echo "..."
echo "=== sending ==="
python3 send_mail.py --digest "$DATE" "$DIGEST" --attach-dir "$DAY_DIR"
