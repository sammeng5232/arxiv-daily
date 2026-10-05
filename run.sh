#!/usr/bin/env bash
# arxiv-daily: fetch new econ.TH papers, generate LLM reports, email them.
# Designed to run under cron (no tty, minimal env). Lock-protected.
set -u
HD="$(cd "$(dirname "$0")" && pwd)"
export ARXIV_DAILY_HOME="$HD"
export PATH="$HOME/.local/npm-prefix/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
DATE="$(date +%F)"
DAY_DIR="$HD/papers/$DATE"
LOG_DIR="$HD/logs"
mkdir -p "$DAY_DIR" "$LOG_DIR"
mkdir -p "$HD/locks"

# --- prevent overlapping runs (14:00 + 21:00 catch-up) ---
exec 9>"$HD/locks/run.lock"
flock -n 9 || { echo "[$(date '+%F %T')] another run in progress, exiting"; exit 0; }

exec > >(tee -a "$LOG_DIR/$DATE.log") 2>&1
echo "================ arxiv-daily run $(date '+%F %T') ================"

# --- 1. fetch new papers (JSON list on stdout) ---
PAPERS_JSON="$(python3 "$HD/fetch_papers.py" --date-dir "$DAY_DIR")"
COUNT="$(printf '%s' "$PAPERS_JSON" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
echo "[run] new papers today: $COUNT"
if [ "$COUNT" = "0" ]; then
  echo "[run] nothing to do."
  exit 0
fi

# --- 2. per paper: extract text, generate report, email ---
mkdir -p "$DAY_DIR/reports"
OK=0; FAIL=0; FAILED_LIST=""
while IFS= read -r paper_json; do
  PID="$(printf '%s' "$paper_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
  TITLE="$(printf '%s' "$paper_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["title"])')"
  echo "---- paper $PID : $TITLE"

  TXT="$DAY_DIR/$PID.txt"
  if [ ! -s "$TXT" ]; then
    python3 "$HD/extract_text.py" "$DAY_DIR/$PID.pdf" "$TXT" || true
  fi

  REPORT="$DAY_DIR/reports/$PID.md"
  if python3 "$HD/report.py" "$DAY_DIR/$PID.meta.json" "$TXT" "$REPORT"; then
    OK=$((OK+1))
  else
    FAIL=$((FAIL+1)); FAILED_LIST="$FAILED_LIST $PID"
    echo "[run] REPORT FAILED for $PID (PDF kept, report skipped)"
  fi

  printf '%s\n' "$PID" >> "$HD/seen.db"   # mark processed exactly once
done < <(printf '%s' "$PAPERS_JSON" | python3 -c '
import json, sys
for p in json.load(sys.stdin):
    print(json.dumps(p))')

# --- 3. single daily email: overview + all full reports + all PDFs ---
DIGEST="$DAY_DIR/reports/_digest.md"
python3 - "$DAY_DIR" "$DATE" "$OK" "$FAIL" > "$DIGEST" <<'PYEOF'
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
python3 "$HD/send_mail.py" --digest "$DATE" "$DIGEST" --attach-dir "$DAY_DIR" \
  && echo "[run] daily briefing mailed" || echo "[run] DAILY BRIEFING MAIL not sent (rc=$?)"

echo "[run] done. ok=$OK fail=$FAIL${FAILED_LIST:+ failed:$FAILED_LIST}"
exit 0
