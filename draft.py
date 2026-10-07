#!/usr/bin/env python3
"""Turn a research idea into a LaTeX draft scaffold with explicit gaps.

Usage: draft.py <date> <idea_id>

Reads ideas/<date>.json, takes the idea's source papers (their report sections
+ metadata) as context, and produces drafts/<date>/<idea_id>/main.tex via two
glm calls (outline -> full draft). Compiles with pdflatex when available
(two passes; one automatic fix round on compile errors).

The draft is an honest SCAFFOLD: model setup and conjectures are formal, proof
attempts are sketched, and every unproven step is marked [GAP: ...] and listed
in a Gap Log on page 1. It never pretends the math is complete.
"""
import glob
import json
import os
import re
import subprocess
import sys

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
IDEAS_DIR = os.path.join(HOME_DIR, "ideas")
MODELS = ("glm-5.3", "glm-5.3-1", "glm-5.3-2")
CLAUDE_BIN = os.path.expanduser("~/.local/npm-prefix/bin/claude")
TIMEOUT_SECS = 1500

OUTLINE_PROMPT = """You are a researcher planning a paper. You have ONE research idea and the source material it builds on.

Produce a paper plan in markdown:
1. Title (working) + 3-sentence abstract of the intended contribution
2. Model section plan: the formal environment (players/objects, information, timing), notation table
3. 2-4 main conjectures, numbered, each with: formal statement sketch, proof strategy naming the tool, and what the [GAP: ...] steps will be
4. Related work: which papers from the source material to position against
5. Which existing results can be cited as-is (lemma imports)

Be concrete about notation. This plan will be expanded into LaTeX next.

HARD LENGTH CONSTRAINT: the entire plan must stay under 700 words. A terse plan, not prose.

=== IDEA ===
{idea}

=== SOURCE MATERIAL ===
{sources}
"""

DRAFT_PROMPT = """You are writing a LaTeX research draft from the plan below. Write the COMPLETE main.tex document.

HARD CONSTRAINTS:
- \\documentclass{{article}}; packages ONLY: amsmath, amssymb, amsthm (no natbib/biblatex/graphicx/xcolor)
- theorem environments: definition, conjecture, lemma, proposition, remark
- Every conjecture is followed by \\begin{{proof}}[Proof attempt] ... \\end{{proof}} sketching the attack
- EVERY unproven or hand-waved step is marked inline as \\textbf{{[GAP: what is missing]}} - never silently assert an unproven claim
- A section "Gap Log" right after the abstract: itemized list of every GAP with a confidence label (high/medium/low that it is fillable) - count them honestly
- References: \\begin{{thebibliography}}{{99}} with ONLY papers mentioned in the source material or idea; NEVER invent references; if unsure of a bibliographic detail, write the title and "(reference details to verify)"
- 5-7 pages, English, clean notation, no filler
- HARD LENGTH CONSTRAINT: total output must stay under 20,000 characters of LaTeX. If the plan is too big, compress proof sketches, never cut the Gap Log.

Output ONLY the LaTeX source, no commentary, no markdown fences.

=== PLAN ===
{outline}

=== IDEA (for fidelity) ===
{idea}

=== SOURCE MATERIAL (for citing and importing) ===
{sources}
"""

FIX_PROMPT = """The LaTeX document below failed to compile. Fix ALL errors. Keep the content identical; only fix syntax, environments, math mode, and bracket mismatches. Re-emit the COMPLETE fixed document, LaTeX only, no commentary. Keep the total output under 20,000 characters.

=== COMPILE ERRORS ===
{errors}

=== DOCUMENT ===
{tex}
"""


def log(msg):
    print(f"[draft] {msg}", file=sys.stderr, flush=True)


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
    if len(out) < 200:
        return None, f"output too short ({len(out)} chars)"
    return out, ""


def run_llm(prompt):
    for model in MODELS:
        out, info = run_claude(prompt, model)
        if out:
            return out
        log(f"model {model} failed: {info}")
    return None


def _report_section(rep, name, limit):
    m = re.search(rf"##\s*{re.escape(name)}\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()[:limit]


def source_material(pids):
    """Report sections + metadata for the idea's source papers."""
    parts = []
    for pid in pids:
        found = False
        for mp in glob.glob(os.path.join(HOME_DIR, "papers", "*", f"{pid}.meta.json")):
            m = json.load(open(mp))
            day_dir = os.path.dirname(mp)
            rp = os.path.join(day_dir, "reports", f"{pid}.md")
            rep = open(rp, encoding="utf-8").read() if os.path.exists(rp) else ""
            parts.append(
                f"### SOURCE PAPER {pid}: {m['title']}\n"
                f"Authors: {', '.join(m.get('authors', [])[:8])}\n"
                f"Abstract: {m.get('abstract', '')[:1200]}\n"
                f"Setup: {_report_section(rep, 'Model and Setup', 1800)}\n"
                f"Main results: {_report_section(rep, 'Main Results', 1800)}\n"
                f"Methods: {_report_section(rep, 'Methodology', 1200)}\n"
                f"Relation to literature: {_report_section(rep, 'Relation to Literature', 900)}")
            found = True
            break
        if not found:
            parts.append(f"### SOURCE PAPER {pid}: (metadata not found)")
    return "\n\n".join(parts)


def compile_tex(texdir, rounds=2):
    """pdflatex rounds; returns (ok, error_excerpt)."""
    if subprocess.run(["bash", "-lc", "command -v pdflatex"], capture_output=True).returncode != 0:
        return False, "pdflatex not installed"
    for _ in range(rounds):
        r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "main.tex"],
                           cwd=texdir, capture_output=True, timeout=180)
    pdf = os.path.join(texdir, "main.pdf")
    if os.path.exists(pdf):
        return True, ""
    errs = []
    logp = os.path.join(texdir, "main.log")
    if os.path.exists(logp):
        for l in open(logp, errors="replace"):
            if l.startswith("!"):
                errs.append(l.strip())
    return False, "\n".join(errs[:15]) or "unknown pdflatex failure"


def clean_texdir(texdir):
    for ext in (".aux", ".log", ".out", ".toc"):
        p = os.path.join(texdir, "main" + ext)
        if os.path.exists(p):
            os.remove(p)


def main():
    if len(sys.argv) < 3:
        print("usage: draft.py <date> <idea_id>")
        return 1
    date, idea_id = sys.argv[1], sys.argv[2]
    ideas = json.load(open(os.path.join(IDEAS_DIR, f"{date}.json")))
    idea = next((i for i in ideas if i.get("id") == idea_id), None)
    if not idea:
        log(f"idea {idea_id} not found in ideas/{date}.json")
        return 1

    outdir = os.path.join(HOME_DIR, "drafts", date, idea_id)
    os.makedirs(outdir, exist_ok=True)
    texpath = os.path.join(outdir, "main.tex")
    if os.path.exists(texpath):
        log(f"{idea_id}: main.tex already exists - skipping")
        return 0

    sources = source_material(idea.get("source_papers", []))
    idea_txt = json.dumps(idea, indent=2)

    log(f"{idea_id}: planning ({idea['title'][:60]}...)")
    outline = run_llm(OUTLINE_PROMPT.format(idea=idea_txt, sources=sources))
    if not outline:
        log(f"{idea_id}: outline generation failed")
        return 1
    with open(os.path.join(outdir, "outline.md"), "w", encoding="utf-8") as f:
        f.write(outline + "\n")

    log(f"{idea_id}: writing full draft")
    tex = run_llm(DRAFT_PROMPT.format(outline=outline, idea=idea_txt, sources=sources))
    if not tex:
        log(f"{idea_id}: draft generation failed")
        return 1
    tex = re.sub(r"^```(latex)?", "", tex.strip())
    tex = re.sub(r"```$", "", tex.strip())

    ok, errs = False, ""
    for attempt in range(3):
        with open(texpath, "w", encoding="utf-8") as f:
            f.write(tex + "\n")
        log(f"{idea_id}: compiling (attempt {attempt + 1})")
        ok, errs = compile_tex(outdir)
        if ok:
            break
        log(f"{idea_id}: compile failed:\n{errs[:500]}")
        if attempt == 2:
            break
        fixed = run_llm(FIX_PROMPT.format(errors=errs, tex=tex))
        if not fixed:
            break
        tex = re.sub(r"^```(latex)?", "", fixed.strip())
        tex = re.sub(r"```$", "", tex.strip())

    clean_texdir(outdir)
    gaps = tex.count("[GAP")
    if ok:
        log(f"{idea_id}: DRAFT-OK gaps={gaps} pdf={os.path.join(outdir, 'main.pdf')}")
        print(f"DRAFT-OK {idea_id} gaps={gaps}")
        return 0
    else:
        log(f"{idea_id}: DRAFT-TEXONLY gaps={gaps} (compile failed; tex saved)")
        print(f"DRAFT-TEXONLY {idea_id} gaps={gaps}")
        return 0  # tex still useful; email will attach it


if __name__ == "__main__":
    sys.exit(main())
