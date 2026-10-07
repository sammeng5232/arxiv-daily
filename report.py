#!/usr/bin/env python3
"""Generate a markdown report for one paper via Claude Code headless (SCRP proxy).

Usage: report.py <meta.json> <paper.txt> <out.md>

- Builds a structured prompt from metadata + full text (truncated to fit context).
- Calls: claude -p --model glm-5.3  (stdin prompt, --output-format text)
 - Falls back to glm-5.3-1, then glm-5.3-2 on failure.
"""
import json
import os
import re
import subprocess
import sys

MAX_TEXT_CHARS = 160_000
TIMEOUT_SECS = 900
CLAUDE_BIN = os.path.expanduser("~/.local/npm-prefix/bin/claude")

PROMPT_TEMPLATE = """You are a research assistant writing a daily briefing report on a newly announced arXiv paper (primary category: {primary}; also listed in: {cats}).

Below you receive the paper's bibliographic metadata and its full extracted text (possibly truncated). Write a critical but fair report IN MARKDOWN with EXACTLY these sections, in this order:

# {title}

**Authors:** {authors}
**arXiv:** {id} ([abs page]({abs_url})) | **Primary category:** {primary} | **Also in:** {cats}
**v1 submitted:** {published}

## TL;DR
2-3 sentences: what the paper does and why it matters.

## Research Question
The precise question(s) the paper asks.

## Model and Setup
The formal environment: agents, information structure, timing, solution concept, key assumptions.

## Main Results
The core theorems/propositions in plain language, with intuition. Number them as in the paper where possible.

## Methodology
Techniques used (mechanism design, dynamic programming, lattice theory, axiomatics, experiments, etc.) and how they are combined.

## Relation to Literature
Positioning vs. the main strands it builds on or departs from.

## Comments
- **Strengths:** what is genuinely new or clever.
- **Weaknesses / concerns:** technical or conceptual issues, restrictive assumptions, external validity.
- **Suggestions:** questions a referee or a seminar audience would raise.

## Possible Publication Venues
2-4 realistic outlets for this paper, ranked. Choose venues appropriate to the paper's field, style and level, drawing e.g. from economic theory (Econometrica, AER, ReStud, JPE, QJE, JET, TE, AEJ:Micro, Games and Economic Behavior, Economic Theory, Journal of Mathematical Economics, Mathematics of Operations Research, Social Choice and Welfare, International Journal of Game Theory, plus field journals), theoretical computer science (EC, WINE, STOC, FOCS, SODA, CCC, ITCS, AAAI, IJCAI, NeurIPS, ICML, JACM, SIAM J. Comput., SIAM J. Discrete Math., Algorithmica), or combinatorics and discrete mathematics (JCTA, JCTB, Combinatorica, J. Comb. Des., Electron. J. Comb., Discrete Math., Order, Adv. Appl. Math.). For each venue: a fit label (strong fit / plausible / stretch) and a one-line rationale based on the paper's contribution, technical level, and scope.

## Tags
5-8 lowercase tags (e.g. #auctions #information-design #repeated-games).

Rules:
- Be specific and cite the paper's own notation/numbers where helpful.
- If the extracted text is garbled or incomplete, rely on the abstract and clearly say so.
- Do NOT invent results that are not in the text.
- Output ONLY the markdown report, no preamble.

=== METADATA ===
{abstract}

=== FULL TEXT (extracted from PDF) ===
{fulltext}
"""


def build_prompt(meta, text):
    truncated = ""
    if text and len(text.strip()) > 500:
        t = text.strip()
        if len(t) > MAX_TEXT_CHARS:
            t = t[:MAX_TEXT_CHARS] + "\n\n[...TRUNCATED for length...]"
        truncated = t
    else:
        truncated = "[PDF text extraction failed or empty - use the abstract above and say the text was unavailable.]"
    return PROMPT_TEMPLATE.format(
        title=meta.get("title", "?"),
        authors=", ".join(meta.get("authors", [])) or "?",
        id=meta.get("id", "?"),
        abs_url=meta.get("abs_url", ""),
        primary=meta.get("primary_category", "?"),
        cats=", ".join(c for c in meta.get("categories", []) if c != meta.get("primary_category")) or "-",
        published=meta.get("published", "?")[:10],
        abstract="Abstract: " + meta.get("abstract", "(none)"),
        fulltext=truncated,
    )


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
    noise = [l for l in err.splitlines() if l.strip() and "unrecognized_model" not in l and "Warning: no stdin" not in l]
    if p.returncode != 0:
        return None, f"exit={p.returncode} err={' | '.join(noise[-3:])}"
    if len(out) < 400:
        return None, f"output too short ({len(out)} chars)"
    return out, ("warn: " + " | ".join(noise[-2:]) if noise else "")


def main():
    meta_path, text_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    meta = json.load(open(meta_path))
    text = open(text_path, encoding="utf-8", errors="replace").read()
    prompt = build_prompt(meta, text)

    for model in ("glm-5.3", "glm-5.3-1", "glm-5.3-2"):
        out, info = run_claude(prompt, model)
        if out:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(out + "\n")
            print(f"REPORT-OK model={model} chars={len(out)} {info}")
            return 0
        print(f"[report] model {model} failed: {info}", file=sys.stderr)
    print("REPORT-FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
