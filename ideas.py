#!/usr/bin/env python3
"""Associative research-idea generation over the day's papers.

Stage 1 of the evening research layer (after the 21:00 catch-up):
  1. Digest every paper with a report (TL;DR + setup + results + methodology)
  2. Batched glm calls (10 papers per call, categories mixed for
     cross-pollination) generate research ideas the papers INSPIRE but do not
     state, each via an explicit association operator and quality gates
  3. Cheap novelty sweep: arXiv keyword search per idea + one glm verdict pass
  4. Score, rank, persist to ideas/<date>.json and the ideas.db index

Usage:
  ideas.py <date>                  # generate + persist (idempotent per date)
  ideas.py <date> --dry-run        # print, don't persist
  ideas.py <date> --pick auto      # print top idea-ids to draft (see PICK rule)
  ideas.py --weekly                # Saturday retrospective memo (emails it)
"""
import datetime
import glob
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_papers  # reuse _get (retry/backoff) + UA

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
IDEAS_DIR = os.path.join(HOME_DIR, "ideas")
DRAFTS_DIR = os.path.join(HOME_DIR, "drafts")
DB = os.path.join(HOME_DIR, "ideas.db")
MODELS = ("glm-5.3", "glm-5.3-1", "glm-5.3-2")
CLAUDE_BIN = os.path.expanduser("~/.local/npm-prefix/bin/claude")
TIMEOUT_SECS = 900
BATCH_SIZE = 10

GEN_PROMPT = """You are a creative but rigorous researcher spanning economic theory, theoretical computer science, and combinatorics. Below are digests of {n} newly announced arXiv papers.

Your job: propose NEW research problems that are INSPIRED BY these papers but NOT stated in them - the problems a sharp reader would think of after reading, that the authors have NOT written down or solved.

Each idea must use exactly one association operator:
- technique-transfer: paper B's technique applied to paper A's setting (cross-paper ideas are especially valuable)
- flip-assumption: invert a key modeling assumption and re-ask the paper's question
- domain-shift: transplant the paper's mechanism to a different domain
- dimension-change: finite->infinite, static->dynamic, small->asymptotic, specific distribution->distribution-free
- inverse-problem: flip the direction (characterize optimal -> characterize implementable; possibility -> impossibility)
- add-friction: introduce one realistic friction into the paper's clean benchmark and ask what survives

QUALITY GATES - every idea must satisfy ALL of these:
1. builds_on: name the specific lemma, mechanism, or technique of the source paper(s) it builds on
2. tractability: name the existing mathematical tool that would plausibly carry the proof, and why
3. minimal_result: one sentence stating the weakest result that would still be publishable
4. NOT a trivial parameter bump (changing N=2 to N=3 with no structural insight)
5. NOT already answered in the source paper(s)
6. would survive a referee asking "what is new here?"

Aim for 2-5 ideas per batch. Prefer fewer, sharper ideas over many shallow ones.

HARD LENGTH CONSTRAINT: keep the total JSON output under 5000 characters. Terse fields, no padding.

Output STRICT JSON only - no markdown fences, no commentary. An array of objects:
[{{"operator": "...", "title": "short title", "source_papers": ["arxiv-id", ...], "problem": "precise problem statement, 3-6 sentences", "builds_on": "...", "tractability": "...", "minimal_result": "...", "difficulty": "weekend|month|semester", "keywords": ["kw1", "kw2"], "quality": 1-10}}]

=== TODAY'S PAPERS ===
{digests}
"""

NOVELTY_PROMPT = """You are checking research ideas for collisions against existing papers. For each idea below, its search keywords were run against the arXiv API; the candidate matches (id, title, abstract snippet) follow each idea.

Judge each idea:
- "novel": no candidate describes substantially the same contribution
- "adjacent": a candidate is closely related but the idea's specific question seems distinct
- "collision": a candidate already does substantially what the idea proposes

Output STRICT JSON only: an array of objects {{"i": idea-number, "verdict": "novel|adjacent|collision", "note": "one line, cite candidate id when not novel"}}. Keep the total output under 3000 characters.

{blocks}
"""


def log(msg):
    print(f"[ideas] {msg}", file=sys.stderr, flush=True)


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
    if len(out) < 50:
        return None, f"output too short ({len(out)} chars)"
    return out, ("warn: " + " | ".join(noise[-2:]) if noise else "")


def run_llm(prompt):
    """Try the model chain; return text or None."""
    for model in MODELS:
        out, info = run_claude(prompt, model)
        if out:
            if info:
                log(f"OK via {model} ({info})")
            return out
        log(f"model {model} failed: {info}")
    return None


def parse_json_array(text):
    """Robustly extract a JSON array from llm output."""
    t = text.strip()
    t = re.sub(r"^```(json)?", "", t).strip()
    t = re.sub(r"```$", "", t).strip()
    i, j = t.find("["), t.rfind("]")
    if i < 0 or j <= i:
        return None
    t = t[i:j + 1]
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        t2 = re.sub(r",\s*([\]}])", r"\1", t)  # trailing commas
        try:
            return json.loads(t2)
        except json.JSONDecodeError:
            return None


def _report_section(rep, name, limit):
    m = re.search(rf"##\s*{re.escape(name)}\s*\n(.*?)(?=\n##|\Z)", rep, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", m.group(1)).strip()[:limit]


def paper_digests(day_dir):
    """One digest per paper with a report; abstract-only fallback otherwise."""
    digests = []
    for mp in sorted(glob.glob(os.path.join(day_dir, "*.meta.json"))):
        m = json.load(open(mp))
        pid = m["id"]
        rp = os.path.join(day_dir, "reports", f"{pid}.md")
        if os.path.exists(rp):
            rep = open(rp, encoding="utf-8").read()
            body = (f"  TL;DR: {_report_section(rep, 'TL;DR', 600)}\n"
                    f"  Setup: {_report_section(rep, 'Model and Setup', 1000)}\n"
                    f"  Results: {_report_section(rep, 'Main Results', 1000)}\n"
                    f"  Methods: {_report_section(rep, 'Methodology', 700)}")
        elif m.get("abstract"):
            body = f"  (no report; abstract only) {m['abstract'][:900]}"
        else:
            continue
        digests.append({
            "id": pid,
            "cats": ",".join(m.get("categories", [])[:4]),
            "title": m["title"],
            "digest": f"[{pid}] {m['title']}\n  categories: {','.join(m.get('categories', [])[:4])}\n{body}",
        })
    return digests


def mixed_batches(digests):
    """Round-robin across categories so each batch mixes fields."""
    by_cat = {}
    for d in digests:
        primary = d["cats"].split(",")[0] if d["cats"] else "?"
        by_cat.setdefault(primary, []).append(d)
    pools = [list(p) for p in by_cat.values()]
    order = []
    while pools:
        for p in pools:
            order.append(p.pop(0))
        pools = [p for p in pools if p]
    return [order[i:i + BATCH_SIZE] for i in range(0, len(order), BATCH_SIZE)]


def _run_batch(batch):
    """One generation call over a batch. Returns list of idea dicts or None."""
    text = run_llm(GEN_PROMPT.format(
        n=len(batch), digests="\n\n".join(d["digest"] for d in batch)))
    if not text:
        return None
    arr = parse_json_array(text)
    if arr is None:
        return None
    valid_ids = {d["id"] for d in batch}
    out = []
    for it in arr:
        if not isinstance(it, dict) or "problem" not in it or "title" not in it:
            continue
        it["source_papers"] = [p for p in it.get("source_papers", []) if p in valid_ids] \
            or [batch[0]["id"]]
        it.setdefault("operator", "?")
        it.setdefault("difficulty", "?")
        it.setdefault("keywords", [])
        try:
            it["quality"] = max(1, min(10, int(it.get("quality", 5))))
        except (TypeError, ValueError):
            it["quality"] = 5
        out.append(it)
    return out


def generate_ideas(day_dir):
    digests = paper_digests(day_dir)
    if not digests:
        log("no papers with digests today")
        return []
    batches = mixed_batches(digests)
    ideas = []
    for bi, batch in enumerate(batches, 1):
        log(f"batch {bi}/{len(batches)}: {len(batch)} papers "
            f"({', '.join(d['id'] for d in batch)})")
        arr = _run_batch(batch)
        if arr is None and len(batch) > 5:
            # gateway hangs / oversized generations: retry as two half-batches
            log(f"batch {bi}: failed - retrying as two halves")
            mid = len(batch) // 2
            arr = []
            for half in (batch[:mid], batch[mid:]):
                sub = _run_batch(half)
                if sub:
                    arr.extend(sub)
                else:
                    log(f"half-batch of {len(half)} papers failed too")
        if arr:
            ideas.extend(arr)
            log(f"batch {bi}: {len(arr)} ideas")
    return ideas


def arxiv_search(keywords, max_results=8):
    """Keyword search via the Atom API. Returns [(id, title, snippet)]."""
    if not keywords:
        return []
    kws = [f'all:"{k}"' for k in keywords[:2] if k]
    if not kws:
        return []
    query = urllib.parse.quote(" AND ".join(kws))
    url = (f"https://export.arxiv.org/api/query?search_query={query}"
           f"&max_results={max_results}&sortBy=relevance")
    try:
        r = fetch_papers._get(url, timeout=60)
    except Exception as e:
        log(f"novelty search failed for {keywords}: {e}")
        return []
    out = []
    for e in r.text.split("<entry>")[1:]:
        mid = re.search(r"<id>http://arxiv.org/abs/([^<]+)</id>", e)
        mti = re.search(r"<title>(.*?)</title>", e, re.S)
        mab = re.search(r"<summary>(.*?)</summary>", e, re.S)
        if mid and mti:
            snip = re.sub(r"\s+", " ", (mab.group(1) if mab else ""))[:220]
            out.append((mid.group(1), re.sub(r"\s+", " ", mti.group(1)), snip))
    return out


def novelty_check(ideas):
    """Attach arXiv candidates to each idea, then one glm verdict pass."""
    for k, it in enumerate(ideas):
        it["_candidates"] = arxiv_search(it.get("keywords", []))
        time.sleep(3)
    blocks = []
    for k, it in enumerate(ideas):
        cands = "\n".join(f"    - {cid}: {ct} -- {cs}" for cid, ct, cs in it["_candidates"]) \
            or "    (no search results)"
        blocks.append(f"IDEA {k}: {it['title']}\n  problem: {it['problem'][:400]}\n"
                      f"  candidates:\n{cands}")
    if not blocks:
        return
    text = run_llm(NOVELTY_PROMPT.format(blocks="\n\n".join(blocks)))
    verdicts = parse_json_array(text) if text else None
    if not verdicts:
        log("novelty verdict pass failed - marking all 'unknown'")
        for it in ideas:
            it["novelty"] = "unknown"
        return
    for v in verdicts:
        try:
            i = int(v.get("i"))
            if 0 <= i < len(ideas):
                ideas[i]["novelty"] = v.get("verdict", "unknown")
                ideas[i]["novelty_note"] = v.get("note", "")
        except (TypeError, ValueError):
            continue
    for it in ideas:
        it.setdefault("novelty", "unknown")


def finalize(ideas, date):
    for it in ideas:
        penalty = {"collision": 6, "adjacent": 2}.get(it.get("novelty"), 0)
        bonus = 1 if len(it.get("source_papers", [])) > 1 else 0
        try:
            it["final"] = max(0, it.get("quality", 5) + bonus - penalty)
        except TypeError:
            it["final"] = 0
        it.pop("_candidates", None)
    ideas.sort(key=lambda i: i.get("final", 0), reverse=True)
    for k, it in enumerate(ideas, 1):  # ids in rank order: -01 is the day's best
        it["id"] = f"{date.replace('-', '')}-{k:02d}"
    return ideas


def save(date, ideas):
    os.makedirs(IDEAS_DIR, exist_ok=True)
    with open(os.path.join(IDEAS_DIR, f"{date}.json"), "w") as f:
        json.dump(ideas, f, indent=2)
    lines = [l for l in open(DB).read().splitlines()
             if not l.startswith(date + "\t")] if os.path.exists(DB) else []
    for it in ideas:
        lines.append("\t".join([date, it["id"], str(it.get("final", 0)),
                                str(it.get("quality", 0)), it.get("novelty", "?"),
                                it.get("operator", "?"), it.get("difficulty", "?"),
                                "0", it.get("title", "?")]))
    with open(DB, "w") as f:
        f.write("\n".join(lines) + "\n")


def load(date):
    p = os.path.join(IDEAS_DIR, f"{date}.json")
    return json.load(open(p)) if os.path.exists(p) else None


def pick(date, n="auto"):
    ideas = load(date) or []
    chosen = []
    for it in ideas:
        if it.get("novelty") == "collision":
            continue
        if os.path.exists(os.path.join(DRAFTS_DIR, date, it["id"], "main.tex")):
            continue  # already drafted
        chosen.append(it["id"])
    if n == "auto":
        limit = int(os.environ.get("DRAFTS_PER_DAY", "2"))
        strong = sum(1 for it in ideas if it.get("final", 0) >= 8
                     and it.get("novelty") != "collision")
        if strong >= 3:
            limit = max(limit, 3)
    else:
        limit = int(n)
    return chosen[:limit]


WEEKLY_PROMPT = """You are writing a weekly retrospective memo for a researcher who received {n_ideas} auto-generated research ideas and {n_drafts} LaTeX drafts from the past week's arXiv papers (economic theory, cs.GT, cs.DM, math.CO).

Stats: {stats}

All ideas (ranked): {listing}

Write a short markdown memo (## sections, no h1):
1. **Theme map**: group the week's ideas into 3-5 research themes; name each theme
2. **Best of the week**: the 3 most promising ideas and why (be honest - if none are exciting, say so)
3. **Pattern feedback**: what the idea generator over- or under-produces (operators, difficulty calibration, fields), phrased as 2-3 concrete taste questions the researcher can answer to recalibrate scoring

Keep the memo under 900 words. Output only the memo markdown.
"""


def weekly_memo():
    today = datetime.date.today()
    cutoff = (today - datetime.timedelta(days=7)).isoformat()
    all_ideas, days = [], []
    for p in sorted(glob.glob(os.path.join(IDEAS_DIR, "????-??-??.json"))):
        d = os.path.basename(p)[:-5]
        if d >= cutoff and d <= today.isoformat():
            for it in json.load(open(p)):
                it["_date"] = d
                all_ideas.append(it)
            days.append(d)
    if not all_ideas:
        log("no ideas this week - skipping memo")
        return 0
    drafted = [it for it in all_ideas
               if os.path.exists(os.path.join(DRAFTS_DIR, it.get("_date", ""), it["id"], "main.tex"))]
    ops = {}
    for it in all_ideas:
        ops[it.get("operator", "?")] = ops.get(it.get("operator", "?"), 0) + 1
    stats = (f"{len(days)} days, {len(all_ideas)} ideas, {len(drafted)} drafted; "
             f"operators: {ops}; "
             f"novelty: " + str({v: sum(1 for i in all_ideas if i.get('novelty') == v)
                                 for v in ('novel', 'adjacent', 'collision', 'unknown')}))
    listing = "\n".join(f"- [{it.get('final','?')}] {it.get('title','?')} "
                        f"({it.get('operator','?')}, {it.get('difficulty','?')}): "
                        f"{it.get('problem','')[:200]}" for it in all_ideas[:60])
    text = run_llm(WEEKLY_PROMPT.format(n_ideas=len(all_ideas), n_drafts=len(drafted),
                                         stats=stats, listing=listing))
    if not text:
        log("weekly memo generation failed")
        return 1
    mp = os.path.join(IDEAS_DIR, f"weekly-{today.isoformat()}.md")
    with open(mp, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    subject = f"[arXiv ideas] weekly memo {today.isoformat()} - {len(all_ideas)} ideas, {len(drafted)} drafts"
    r = subprocess.run(["python3", os.path.join(HOME_DIR, "send_mail.py"),
                        "--raw", subject, mp])
    return r.returncode


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    if args and args[0] == "--weekly":
        return weekly_memo()
    if not args:
        print("usage: ideas.py <date> [--dry-run] | ideas.py <date> --pick auto|N | ideas.py --weekly")
        return 1
    date = args[0]
    if "--pick" in args:
        n = args[args.index("--pick") + 1] if len(args) > args.index("--pick") + 1 else "auto"
        for pid in pick(date, n):
            print(pid)
        return 0

    existing = load(date)
    if existing is not None:
        log(f"ideas/{date}.json already exists ({len(existing)} ideas) - reusing")
        return 0
    day_dir = os.path.join(HOME_DIR, "papers", date)
    ideas = generate_ideas(day_dir)
    if not ideas:
        log("no ideas generated")
        if not dry:
            save(date, [])
        return 0
    log(f"generated {len(ideas)} raw ideas - running novelty sweep")
    novelty_check(ideas)
    ideas = finalize(ideas, date)
    for it in ideas:
        log(f"  [{it['final']:>2}] {it['novelty']:<10} {it['operator']:<18} "
            f"{it['difficulty']:<8} {it['title'][:70]}")
    if not dry:
        save(date, ideas)
        log(f"saved {len(ideas)} ideas -> ideas/{date}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
