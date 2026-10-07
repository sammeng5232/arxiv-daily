#!/usr/bin/env python3
"""Day-theme synthesis for one category: one extra LLM call over the day's papers.

Usage: themes.py <day_dir> <category> [max_pages]
Selects papers tagged with <category> (and within the page cap) that have
reports; prints a short markdown paragraph (no heading) on stdout.
Prints nothing when fewer than 2 papers qualify.
"""
import glob
import json
import os
import re
import subprocess
import sys

MODELS = ("glm-5.3", "glm-5.3-1", "glm-5.3-2")
CLAUDE_BIN = os.path.expanduser("~/.local/npm-prefix/bin/claude")
TIMEOUT_SECS = 900

PROMPT_TEMPLATE = """You are the editor of a daily research briefing on newly announced papers in a given arXiv category (today: {category}). Below is a listing of today's papers with one-line summaries and tags. Write ONE flowing paragraph (3-6 sentences, no heading, no bullet points) that identifies the themes of the day: which questions or techniques come up repeatedly, and how the papers relate to each other. Be concrete and reference papers by arXiv id where it helps. Output only the paragraph.

=== PAPER LISTING ===
{listing}
"""


def run_claude(prompt, model):
    env = dict(os.environ)
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    env["PATH"] = os.path.expanduser("~/.local/npm-prefix/bin:") + env.get("PATH", "")
    try:
        p = subprocess.run(
            [CLAUDE_BIN, "-p", "--model", model, "--output-format", "text"],
            input=prompt.encode("utf-8", "replace"),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=TIMEOUT_SECS, env=env,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    out = p.stdout.decode("utf-8", "replace").strip()
    err = p.stderr.decode("utf-8", "replace")
    noise = [l for l in err.splitlines() if l.strip() and "unrecognized_model" not in l
             and "Warning: no stdin" not in l]
    if p.returncode != 0:
        return None, f"exit={p.returncode} err={' | '.join(noise[-3:])}"
    if len(out) < 100:
        return None, f"output too short ({len(out)} chars)"
    return out, ("warn: " + " | ".join(noise[-2:]) if noise else "")


def main():
    day_dir, category = sys.argv[1], sys.argv[2]
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    papers = []
    for mp in sorted(glob.glob(os.path.join(day_dir, "*.meta.json"))):
        m = json.load(open(mp))
        if category not in m.get("categories", []):
            continue
        if max_pages and m.get("pages") and m["pages"] > max_pages:
            continue
        rp = os.path.join(day_dir, "reports", f"{m['id']}.md")
        if not os.path.exists(rp):
            continue
        rep = open(rp, encoding="utf-8").read()
        m2 = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
        tldr = re.sub(r"\s+", " ", m2.group(1)).strip() if m2 else "(no TL;DR)"
        tags = re.findall(r"#(\w[\w-]*)", rep)
        line = f"- {m['title']} (arXiv:{m['id']}): {tldr}"
        if tags:
            line += f" [{', '.join(tags[:6])}]"
        papers.append(line)

    if len(papers) < 2:
        print(f"[themes] {category}: only {len(papers)} report(s) - skipping theme synthesis",
              file=sys.stderr)
        return 0

    prompt = PROMPT_TEMPLATE.format(category=category, listing="\n".join(papers))
    for model in MODELS:
        out, info = run_claude(prompt, model)
        if out:
            print(out)
            print(f"[themes] {category}: OK via {model} ({len(out)} chars) {info}", file=sys.stderr)
            return 0
        print(f"[themes] {category}: model {model} failed: {info}", file=sys.stderr)
    print(f"[themes] {category}: all models failed - continuing without themes", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
