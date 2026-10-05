#!/usr/bin/env python3
"""Build the daily briefing markdown for one arXiv category.

Usage: build_digest.py <day_dir> <date> <category> [max_pages]

Selects papers in <day_dir> whose meta.json lists <category> among the
paper's arXiv categories (new + cross-lists), optionally excluding papers
longer than max_pages. Reports are read from <day_dir>/reports/<id>.md
(shared across categories: cross-listed papers reuse the same report).
Retry notes come from state/<category>.db.

Writes:
  <day_dir>/reports/_digest-<category>.md    (email body)
  <day_dir>/reports/_digest-<category>.files (PDF paths, one per line)
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import state

HOME = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))


def main():
    day_dir, date, category = sys.argv[1], sys.argv[2], sys.argv[3]
    max_pages = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    state_db = os.path.join(HOME, "state", f"{category}.db")
    seen = state.load(state_db) if os.path.exists(state_db) else {}

    metas = []
    for mp in sorted(glob.glob(os.path.join(day_dir, "*.meta.json"))):
        m = json.load(open(mp))
        if category in m.get("categories", []):
            metas.append(m)
    if max_pages:
        metas = [m for m in metas if not (m.get("pages") and m["pages"] > max_pages)]

    toc, full, pdfs = [], [], []
    n_ok = n_fail = 0
    for m in metas:
        pid = m["id"]
        rp = os.path.join(day_dir, "reports", f"{pid}.md")
        auth = ", ".join(m.get("authors", [])[:6])
        if len(m.get("authors", [])) > 6:
            auth += " et al."
        pdf = os.path.join(day_dir, f"{pid}.pdf")
        if os.path.exists(pdf):
            pdfs.append(pdf)
        if os.path.exists(rp):
            n_ok += 1
            rep = open(rp, encoding="utf-8").read()
            m2 = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
            tldr = re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else "(no TL;DR)"
            toc.append(f"**{m['title']}** - {auth} "
                       f"([arXiv:{pid}]({m.get('abs_url', '')}))\n\n> {tldr}")
            full.append(rep.rstrip())
        else:
            n_fail += 1
            e = seen.get(pid, {"status": "fail", "attempts": 0})
            note = ("will retry on a later run" if e["attempts"] < state.MAX_ATTEMPTS
                    else "retries exhausted")
            toc.append(f"**{m['title']}** - {auth} (arXiv:{pid})\n\n"
                       f"> *report generation failed ({note})*")
            full.append(f"# {m['title']}\n\nReport generation failed; PDF available on the server.")

    parts = [f"# arXiv {category} daily briefing - {date}", "",
             f"Papers announced today (new + cross-lists): **{len(metas)}**. "
             f"Reports generated: **{n_ok}**." + (f" Failures: {n_fail}." if n_fail else "")
             + (f" (papers over {max_pages} pages excluded)" if max_pages else ""),
             "", "## Overview", ""]
    parts.extend(toc)

    themes_path = os.path.join(day_dir, "reports", f"_themes-{category}.md")
    if os.path.exists(themes_path) and n_ok >= 2:
        raw = open(themes_path, encoding="utf-8").read().strip()
        body = "\n".join(l for l in raw.splitlines()
                         if not l.lstrip().startswith("#")).strip()
        if body:
            parts += ["", "## Today's themes", body]

    parts.append("\n---\n")
    parts.append("# Full reports")
    parts.extend(full)

    out = os.path.join(day_dir, "reports", f"_digest-{category}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts) + "\n")
    files_out = os.path.join(day_dir, "reports", f"_digest-{category}.files")
    with open(files_out, "w") as f:
        f.write("\n".join(pdfs) + ("\n" if pdfs else ""))
    print(f"[digest] {category}: wrote {out} ({os.path.getsize(out)} bytes, "
          f"{n_ok} reports, {n_fail} failed)")


if __name__ == "__main__":
    main()
