#!/usr/bin/env python3
"""Fetch today's new papers for one arXiv category (new + cross-lists).

- Primary source: the category RSS feed (the current day's announcement).
- Fallback: arxiv.org/list/<cat>/new (live earlier than RSS; authoritative).
  The listing page is ALSO consulted when RSS yields nothing new, so a stale
  (non-empty but outdated) RSS feed can never hide today's announcement.
- Enrichment: Atom API (id_list batches) for clean metadata (v1 date, authors,
  categories, abstract) + PDF page count via pypdf.
- State: per-category seen db (state/<cat>.db). Failed papers are retried on
  later runs up to state.MAX_ATTEMPTS, then abandoned. Papers longer than
  --max-pages are marked 'skip' (math.CO > 15 pages by convention).
- Day artifacts are SHARED across categories (papers/<DATE>/<id>.*): a paper
  cross-listed into two categories is downloaded and reported once, and its
  report is reused by both category digests.

Output: JSON list of paper dicts on stdout (for run.sh to consume).
Exit codes: 0 ok (possibly 0 papers), 2 = suspicious empty fetch (both
sources unusable -> run.sh sends a canary email on weekdays).
"""
import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests
from pypdf import PdfReader

import state

ARX = "{http://arxiv.org/schemas/atom}"
ATOM = "{http://www.w3.org/2005/Atom}"
API_URL = "https://export.arxiv.org/api/query"
PDF_URL = "https://arxiv.org/pdf/{id}"
UA = {"User-Agent": "Perpetuum/1.0 (autonomous research engine; "
                    "https://github.com/sammeng5232/perpetuum)"}
MAX_PAPERS = 25          # hard cap per run (per category; rest -> catch-up run)
MAX_AGE_DAYS = 14        # v1 must be within N days (filters replacements)

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    print(f"[fetch] {msg}", file=sys.stderr, flush=True)


def rss_url(cat):
    return f"https://export.arxiv.org/rss/{cat}"


def listing_url(cat):
    return f"https://arxiv.org/list/{cat}/new?show=2000"


def default_state_db(cat):
    return os.path.join(HOME_DIR, "state", f"{cat}.db")


def id_from_url(url):
    m = re.search(r"abs/([^/]+/)?(\d{4}\.\d{4,5})(v\d+)?$", url or "")
    return m.group(2) if m else None


def _get(url, params=None, timeout=60, stream=False, tries=3):
    """GET with retry/backoff: arXiv throttles bursts with 429s and slow reads."""
    last_err = None
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout,
                             stream=stream)
            if r.status_code == 429 or r.status_code >= 500:
                last_err = RuntimeError(f"HTTP {r.status_code}")
            else:
                r.raise_for_status()
                return r
        except (requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError) as e:
            last_err = e
        if attempt < tries:
            wait = 30 * attempt
            log(f"{last_err} from {url.split('?')[0]} - backing off {wait}s "
                f"(attempt {attempt}/{tries})")
            time.sleep(wait)
    raise last_err


def rss_paper_ids(cat):
    """IDs (new + cross-lists + replacements) from the category RSS feed."""
    r = _get(rss_url(cat), timeout=60)
    root = ET.fromstring(r.content)
    ids, seen = [], set()
    for item in root.findall("./channel/item"):
        pid = id_from_url(item.findtext("link") or "")
        if pid and pid not in seen:
            seen.add(pid)
            ids.append(pid)
    return ids


def listing_ids(cat):
    """Scrape arxiv.org/list/<cat>/new -> (new+cross IDs, total IDs on page)."""
    r = _get(listing_url(cat), timeout=120)  # show=2000 pages can be slow
    total = set(re.findall(r"arXiv:(\d{4}\.\d{4,5})", r.text))
    cut = r.text.split("Replacement submissions")[0]  # new + cross only
    ids, seen = [], set()
    for pid in re.findall(r"arXiv:(\d{4}\.\d{4,5})", cut):
        if pid not in seen:
            seen.add(pid)
            ids.append(pid)
    return ids, len(total)


def api_enrich(ids):
    """Fetch clean metadata for ids via the Atom API (batches of 20)."""
    meta = {}
    for i in range(0, len(ids), 20):
        batch = ids[i:i + 20]
        r = _get(API_URL, params={"id_list": ",".join(batch),
                                  "max_results": len(batch)}, timeout=60)
        root = ET.fromstring(r.content)
        for e in root.findall(f"{ATOM}entry"):
            pid = id_from_url(e.findtext(f"{ATOM}id") or "")
            if not pid:
                continue
            cats, pc = [], e.find(f"{ARX}primary_category")
            primary = pc.get("term") if pc is not None else None
            if primary:
                cats.append(primary)
            for c in e.findall(f"{ATOM}category"):
                t = c.get("term")
                if t and t not in cats:
                    cats.append(t)
            meta[pid] = {
                "id": pid,
                "title": re.sub(r"\s+", " ", e.findtext(f"{ATOM}title") or "").strip(),
                "authors": [a.findtext(f"{ATOM}name") for a in e.findall(f"{ATOM}author")],
                "published": e.findtext(f"{ATOM}published") or "",
                "primary_category": primary,
                "categories": cats,
                "abs_url": e.findtext(f"{ATOM}id") or "",
                "abstract": re.sub(r"\s+", " ", e.findtext(f"{ATOM}summary") or "").strip(),
            }
        time.sleep(3)
    return meta


def download_pdf(pid, dest):
    r = _get(PDF_URL.format(id=pid), timeout=180, stream=True)
    ctype = r.headers.get("Content-Type") or ""
    if "pdf" not in ctype:
        r.close()
        raise RuntimeError(f"not a PDF (content-type {ctype})")
    tmp = dest + ".part"
    with open(tmp, "wb") as f:
        for chunk in r.iter_content(65536):
            f.write(chunk)
    os.replace(tmp, dest)
    return os.path.getsize(dest)


def count_pages(pdf_path):
    try:
        return len(PdfReader(pdf_path).pages)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date-dir", required=True)
    ap.add_argument("--category", default="econ.TH")
    ap.add_argument("--state-file", default=None,
                    help="per-category seen db (default state/<category>.db)")
    ap.add_argument("--max-pages", type=int, default=0,
                    help="skip papers longer than this many pages (0 = no limit)")
    ap.add_argument("--test-id", help="force-process this arXiv id (bypasses sources & state)")
    args = ap.parse_args()
    cat = args.category
    state_db = args.state_file or default_state_db(cat)

    os.makedirs(args.date_dir, exist_ok=True)
    os.makedirs(os.path.join(args.date_dir, "reports"), exist_ok=True)
    st = state.load(state_db)

    def is_done(pid):
        e = st.get(pid)
        return e is not None and state.is_done(e)

    if args.test_id:
        ids, src = [args.test_id], "test"
    else:
        # --- source 1: RSS ---
        try:
            rss_ids = rss_paper_ids(cat)
        except Exception as e:
            log(f"RSS fetch failed: {e}")
            rss_ids = []
        unseen_rss = [i for i in rss_ids if not is_done(i)]

        # --- source 2: listing page ---
        l_ids, l_total, l_error = [], 0, None
        try:
            l_ids, l_total = listing_ids(cat)
        except Exception as e:
            l_error = e
            log(f"listing page fetch failed: {e}")

        if l_total == 0 and l_error is None:
            log("listing page fetched but contains no arXiv ids at all - suspicious (markup change?)")

        suspicious = l_error is not None or l_total == 0
        if suspicious and not unseen_rss:
            log("no usable source: RSS has nothing new and listing page unusable -> canary")
            print("[]")
            sys.exit(2)

        if unseen_rss:
            ids, src = unseen_rss, "rss"
        else:
            ids, src = [i for i in l_ids if not is_done(i)], "listing-page"
            if not ids and (rss_ids or l_ids):
                log("all candidate papers already processed (or retries exhausted)")
            elif not ids:
                log("quiet day: no new papers announced")

        # --- retry queue (failures with attempts left) ---
        for pid, e in sorted(st.items()):
            if e["status"] == "fail" and e["attempts"] < state.MAX_ATTEMPTS and pid not in ids:
                ids.append(pid)
                src += "+retry"
                log(f"retry-queue: adding {pid} (attempt {e['attempts'] + 1}/{state.MAX_ATTEMPTS})")

    if not ids:
        print("[]")
        return 0
    log(f"[{cat}] source={src}: {len(ids)} paper(s) to process: {', '.join(ids[:10])}")

    meta = api_enrich(ids)
    now = time.time()
    papers = []
    for pid in ids:
        m = meta.get(pid)
        if not m:
            log(f"{pid}: no API metadata, skipping")
            continue
        is_retry = pid in st and st[pid]["status"] == "fail"
        if not args.test_id and not is_retry:
            try:
                pub_ts = time.mktime(time.strptime(m["published"][:10], "%Y-%m-%d"))
            except Exception:
                pub_ts = now
            if (now - pub_ts) / 86400 > MAX_AGE_DAYS:
                log(f"{pid}: v1 published {m['published'][:10]} (> {MAX_AGE_DAYS}d, "
                    f"likely replacement) - skip")
                continue
        pdf_path = os.path.join(args.date_dir, f"{pid}.pdf")
        if not os.path.exists(pdf_path):
            try:
                size = download_pdf(pid, pdf_path)
                log(f"{pid}: downloaded PDF ({size} bytes)")
                time.sleep(3)
            except Exception as e:
                log(f"{pid}: PDF download FAILED: {e}")
                continue
        else:
            log(f"{pid}: PDF already on disk")
        pages = count_pages(pdf_path)
        if pages:
            m["pages"] = pages
        meta_path = os.path.join(args.date_dir, f"{pid}.meta.json")
        with open(meta_path, "w") as f:
            json.dump(m, f, indent=2)
        if args.max_pages and pages and pages > args.max_pages:
            log(f"{pid}: {pages} pages > {args.max_pages} - skipping ({cat} page cap)")
            state.mark(state_db, pid, "skip")
            continue
        m["pdf_path"] = pdf_path
        m["meta_path"] = meta_path
        papers.append(m)
        if len(papers) >= MAX_PAPERS:
            log(f"reached MAX_PAPERS={MAX_PAPERS}, stopping "
                f"(remaining picked up by the catch-up run)")
            break

    print(json.dumps(papers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
