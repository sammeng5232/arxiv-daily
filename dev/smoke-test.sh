#!/usr/bin/env bash
# Smoke tests for the arxiv-daily pipeline (safe: no emails, no LLM calls,
# no writes to real state). Run after any deploy: bash dev/smoke-test.sh
set -e
cd "$(dirname "$0")/.."
export ARXIV_DAILY_HOME="$(pwd)"

echo "=== 1. syntax check ==="
python3 -m py_compile fetch_papers.py extract_text.py report.py send_mail.py \
    state.py health.py themes.py build_digest.py ideas.py draft.py
bash -n run.sh run-all.sh run-ideas.sh install-cron.sh
echo "SYNTAX-OK"

echo
echo "=== 2. state.py: legacy compat + retry/skip accounting (isolated fixture) ==="
T=$(mktemp -d)
printf '2610.03146\n2610.03157\tok\t1\t\n' > "$T/legacy.db"
python3 state.py --db "$T/legacy.db" stats
python3 state.py --db "$T/legacy.db" mark fail 0000.99999
python3 state.py --db "$T/legacy.db" mark fail 0000.99999
python3 state.py --db "$T/legacy.db" mark fail 0000.99999
python3 state.py --db "$T/legacy.db" mark skip 0000.88888
python3 state.py --db "$T/legacy.db" stats
python3 -c "
import state
st = state.load('$T/legacy.db')
assert state.is_done(st['0000.99999']), 'exhausted must be done'
assert state.is_done(st['0000.88888']), 'skip must be done'
assert not state.is_done({'status': 'fail', 'attempts': 1, 'date': ''}), '1-attempt fail must retry'
assert len(st) == 4, 'legacy lines preserved + 2 new marks'
print('STATE-ASSERT-OK')
"
rm -rf "$T"

echo
echo "=== 3. per-category sources: RSS + listing page parse (no downloads) ==="
python3 - <<'EOF'
import fetch_papers as fp
for cat in ("econ.TH", "cs.GT", "cs.DM", "math.CO"):
    try:
        rss = fp.rss_paper_ids(cat)
        print(f"{cat}: rss_items={len(rss)}", end="  ")
    except Exception as e:
        print(f"{cat}: rss FAILED ({e})", end="  ")
    try:
        ids, total = fp.listing_ids(cat)
        print(f"listing_new+cross={len(ids)} total_on_page={total}")
    except Exception as e:
        print(f"listing FAILED ({e})")
EOF

echo
echo "=== 3b. fetch dry run, econ.TH into temp dir (isolated state) ==="
T=$(mktemp -d)
python3 fetch_papers.py --date-dir "$T/day" --category econ.TH \
    --state-file "$T/state.db" > "$T/out.json" || RC=$?
echo "fetch rc=${RC:-0} (0 expected; 2 = suspicious-empty)"
python3 -c "import json; print('papers returned:', len(json.load(open('$T/out.json'))))"
rm -rf "$T"

echo
echo "=== 4. health.py: heartbeat + canary dry-runs ==="
python3 health.py heartbeat --dry-run | head -14
echo "---"
python3 health.py canary cs.GT --dry-run | head -8

echo
echo "=== 5. build_digest.py: category filter + math.CO page cap (isolated copy) ==="
DATE=$(date +%F)
if [ -d "papers/$DATE" ] && ls papers/"$DATE"/*.meta.json >/dev/null 2>&1; then
  T=$(mktemp -d)
  cp papers/"$DATE"/*.meta.json "$T/"
  mkdir -p "$T/reports"
  cp papers/"$DATE"/reports/*.md "$T/reports/" 2>/dev/null || true
  python3 -c "
import json
m = {'id': '0000.00001', 'title': 'A Very Long Combinatorics Paper', 'authors': ['A. Author'],
     'published': '$DATE', 'primary_category': 'math.CO', 'categories': ['math.CO'],
     'abs_url': 'https://arxiv.org/abs/0000.00001', 'pages': 45}
json.dump(m, open('$T/0000.00001.meta.json', 'w'), indent=2)
"
  echo "--- econ.TH digest (today's real papers) ---"
  python3 build_digest.py "$T" "$DATE" econ.TH 0
  head -5 "$T/reports/_digest-econ.TH.md"
  echo "--- math.CO digest, cap 30 (fake 45-page paper must NOT appear) ---"
  python3 build_digest.py "$T" "$DATE" math.CO 30
  if grep -q "0000.00001" "$T/reports/_digest-math.CO.md"; then
      echo "PAGE-CAP-ASSERT-FAILED"; exit 1
  else
      echo "PAGE-CAP-ASSERT-OK (45-page paper excluded)"
  fi
  echo "--- math.CO digest, no cap (fake paper appears, failed note) ---"
  python3 build_digest.py "$T" "$DATE" math.CO 0
  grep -c "0000.00001" "$T/reports/_digest-math.CO.md" || true
  rm -rf "$T"
else
  echo "(no papers/$DATE metas yet - skipping)"
fi

echo
echo "=== 6. ideas.py: JSON parsing + batch mixing + pick logic (no LLM) ==="
python3 - <<'EOF'
import ideas

# robust JSON array parsing
t1 = '```json\n[{"a": 1}, {"b": 2},]\n```'
assert ideas.parse_json_array(t1) == [{"a": 1}, {"b": 2}], "fenced+trailing-comma parse"
t2 = 'preamble text [ {"x": "y"} ] trailing'
assert ideas.parse_json_array(t2) == [{"x": "y"}], "embedded parse"
assert ideas.parse_json_array("no array here") is None
print("PARSE-JSON-OK")

# mixed batches: round-robin across categories
ds = [ {"id": f"e{i}", "cats": "econ.TH", "digest": ""} for i in range(4) ] + \
     [ {"id": f"m{i}", "cats": "math.CO", "digest": ""} for i in range(2) ]
b = ideas.mixed_batches(ds)
first_ids = [d["id"] for d in b[0]]
assert first_ids[:2] == ["e0", "m0"], f"round-robin order wrong: {first_ids}"
assert len(b[0]) == 10 or len(b[0]) == 6
print("MIXED-BATCH-OK")

# finalize: id assignment, collision penalty, ranking
fake = [
    {"title": "A", "problem": "p", "quality": 9, "novelty": "collision", "source_papers": ["1"]},
    {"title": "B", "problem": "p", "quality": 7, "novelty": "novel", "source_papers": ["1", "2"]},
]
out = ideas.finalize(fake, "2026-10-05")
assert out[0]["id"] == "20261005-01" and out[0]["title"] == "B", "ranking/penalty wrong"
assert out[0]["final"] == 8 and out[1]["final"] == 3, f"scores {out[0]['final']}, {out[1]['final']}"
print("FINALIZE-OK")
EOF

echo
echo "SMOKE TESTS DONE"
