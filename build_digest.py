#!/usr/bin/env python3
"""Build the daily briefing markdown.

Usage: build_digest.py <day_dir> <date> <ok> <fail>

Reads <day_dir>/*.meta.json, <day_dir>/reports/<id>.md, the optional
reports/_themes.md produced by themes.py, and seen.db (for retry notes on
failed papers). Writes <day_dir>/reports/_digest.md.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state

HOME = os.path.dirname(os.path.abspath(__file__))


def load_seen():
    return state.load()


def main():
    day_dir, date, ok, fail = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    seen = load_seen()
    parts = [f"# arXiv econ.TH daily briefing - {date}", "",
             f"Papers announced today (new + cross-lists): **{ok + fail}**. "
             f"Reports generated: **{ok}**." + (f" Failures: {fail}." if fail else ""), "",
             "## Overview", ""]
    toc, full = [], []
    for mp in sorted(glob.glob(os.path.join(day_dir, "*.meta.json"))):
        m = json.load(open(mp))
        pid = m["id"]
        rp = os.path.join(day_dir, "reports", f"{pid}.md")
        auth = ", ".join(m.get("authors", [])[:6]) + (" et al." if len(m.get("authors", [])) > 6 else "")
        if os.path.exists(rp):
            rep = open(rp, encoding="utf-8").read()
            m2 = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
            tldr = re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else "(no TL;DR)"
            toc.append(f"**{m['title']}** - {auth} ([arXiv:{pid}]({m.get('abs_url', '')}))\n\n> {tldr}")
            full.append(rep.rstrip())
        else:
            e = seen.get(pid, {"status": "fail", "attempts": 0})
            note = ("will retry on a later run" if e["attempts"] < state.MAX_ATTEMPTS
                    else "retries exhausted")
            toc.append(f"**{m['title']}** - {auth} (arXiv:{pid})\n\n> *report generation failed ({note})*")
            full.append(f"# {m['title']}\n\nReport generation failed; PDF available on the server.")
    parts.extend(toc)

    themes_path = os.path.join(day_dir, "reports", "_themes.md")
    if os.path.exists(themes_path) and len(full) >= 2:
        raw = open(themes_path, encoding="utf-8").read().strip()
        body = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#")).strip()
        if body:
            parts += ["", "## Today's themes", body]

    parts.append("\n---\n")
    parts.append("# Full reports")
    parts.extend(full)
    out = os.path.join(day_dir, "reports", "_digest.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    print(f"[digest] wrote {out} ({os.path.getsize(out)} bytes, {len(full)} reports)")


if __name__ == "__main__":
    main()
