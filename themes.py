#!/usr/bin/env python3
"""Day-theme synthesis: one extra LLM call over the day's papers.

Usage: themes.py <day_dir>
Prints a short markdown paragraph (no heading) identifying themes, dialogues
and contrasts across the day's papers. Prints nothing when fewer than 2
papers have reports.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report

PROMPT_TEMPLATE = """You are writing the "Today's themes" section for a daily briefing on newly
announced economic-theory papers (arXiv econ.TH). Below are the day's papers, numbered,
each with its TL;DR and tags.

Write 3-6 sentences of plain markdown prose (NO heading, NO preamble, NO bullet list) that:
1. identifies common threads or themes across the papers,
2. points out any papers that directly dialogue with, complement, or compete with each other,
3. notes interesting methodological or substantive contrasts.

Refer to papers by number, e.g. [1], [2]. If the papers are genuinely unrelated, say so
briefly and characterize each in one phrase instead.

=== TODAY'S PAPERS ===
{listing}
"""


def main():
    day_dir = sys.argv[1]
    papers = []
    for mp in sorted(glob.glob(os.path.join(day_dir, "*.meta.json"))):
        m = json.load(open(mp))
        rp = os.path.join(day_dir, "reports", f"{m['id']}.md")
        if not os.path.exists(rp):
            continue
        rep = open(rp, encoding="utf-8").read()
        m2 = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
        t3 = re.search(r"##\s*Tags\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
        papers.append({
            "n": len(papers) + 1,
            "title": m["title"],
            "tldr": re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else "",
            "tags": re.sub(r"\s+", " ", t3.group(1)).strip() if t3 else "",
        })

    if len(papers) < 2:
        print("[themes] fewer than 2 reports - nothing to synthesize", file=sys.stderr)
        return 0

    listing = "\n\n".join(
        f"[{p['n']}] **{p['title']}** - {p['tldr']} {p['tags']}" for p in papers)
    prompt = PROMPT_TEMPLATE.format(listing=listing)

    for model in ("glm-5.3", "glm-5.3-1", "glm-5.3-2"):
        out, info = report.run_claude(prompt, model)
        if out and len(out) > 80:
            print(out.strip())
            return 0
        print(f"[themes] model {model} failed: {info}", file=sys.stderr)

    print("[themes] all models failed - omitting themes section", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
