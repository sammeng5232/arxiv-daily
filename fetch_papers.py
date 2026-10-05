#!/usr/bin/env python3
"""Fetch today's new econ.TH papers from arXiv (new + cross-lists).

- Primary source: RSS feed of econ.TH (the current day's announcement).
- Fallback: arxiv.org/list/econ.TH/new (live earlier than RSS; authoritative).
  The listing page is ALSO consulted when RSS yields nothing new, so a stale
  (non-empty but outdated) RSS feed can never hide today's announcement.
- Enrichment: Atom API (id_list batch) for clean metadata (v1 date, authors, categories).
- Dedup/retry state: seen.db via state.py - failed papers are retried on later
  runs up to state.MAX_ATTEMPTS total attempts, then abandoned.
- Downloads PDFs into papers/<DATE>/<id>.pdf and writes <id>.meta.json.

Output: JSON list of paper dicts on stdout (for run.sh to consume).
Exit codes: 0 ok (possibly 0 papers), 2 = suspicious empty fetch (both sources
unusable -> run.sh sends a canary email on weekdays).
"""
import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

import state

ARX = "{http://arxiv.org/schemas/atom}"
ATOM = "{http://www.w3.org/2005/Atom}"

RSS_URL = "https://export.arxiv.org/rss/econ.TH"
LISTING_URL = "https://arxiv.org/list/econ.TH/new"
API_URL = "https://export.arxiv.org/api/query"
PDF_URL = "https://arxiv.org/pdf/{id}"
UA = {"User-Agent": "arxiv-daily/1.0 (automated research digest; https://github.com/sammeng5232/arxiv-daily)"}
MAX_PAPERS = 25          # hard cap per run
MAX_AGE_DAYS = 14        # v1 must be within N days (filters replacements of old papers)

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    print(f"[fetch] {msg}", file=sys.stderr, flush=True)


def id_from_url(url):
    m = re.search(r"abs/([0-9]{4}\.[0-9]{4,5})(v[0-9]+)?", url)
    return m.group(1) if m else None


def listing_ids():
    """Scrape arxiv.org/list/econ.TH/new (authoritative, live earlier than RSS).
    Returns (new_cross_ids, total_ids_on_page). Keeps New submissions +
    Cross-listings, excludes Replacement submissions. total_ids_on_page counts
    ALL ids on the page (incl. replacements) and is used as a health signal:
    a healthy page always contains some ids."""
    r = requests.get(LISTING_URL, headers=UA, timeout=60)
    r.raise_for_status()
    total = re.findall(r"arXiv:(\d{4}\.\d{4,5})", r.text)
    cut = r.text.split("Replacement submissions")[0]
    ids, seen = [], set()
    for pid in re.findall(r"arXiv:(\d{4}\.\d{4,5})", cut):
        if pid not in seen:
            seen.add(pid)
            ids.append(pid)
    return ids, len(set(total))


def rss_paper_ids():
    """Return arXiv ids from the current econ.TH RSS announcement (replacements skipped)."""
    r = requests.get(RSS_URL, headers=UA, timeout=60)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        if not link:
            continue
        # Replacements are prefixed in arXiv RSS titles
        if re.match(r"^\s*(replacement|updated|\*\*replaced\*\*)", title, re.I):
            continue
        pid = id_from_url(link)
        if pid:
            out.append(pid)
    return out


def api_enrich(ids):
    """Batch query Atom API. Returns {id: meta_dict}."""
    meta = {}
    for chunk_start in range(0, len(ids), 20):
        chunk = ids[chunk_start:chunk_start + 20]
        url = API_URL + "?id_list=" + ",".join(chunk) + f"&max_results={len(chunk)}"
        for attempt in range(3):
            try:
                r = requests.get(url, headers=UA, timeout=60)
                r.raise_for_status()
                break
            except Exception as e:
                log(f"API attempt {attempt+1} failed: {e}")
                time.sleep(5 * (attempt + 1))
        else:
            continue
        root = ET.fromstring(r.content)
        for e in root.iter(f"{ATOM}entry"):
            eid = (e.findtext(f"{ATOM}id") or "").strip()
            pid = id_from_url(eid) or eid.split("/abs/")[-1].split("v")[0]
            authors = [a.findtext(f"{ATOM}name") for a in e.findall(f"{ATOM}author") if a.findtext(f"{ATOM}name")]
            cats = [c.get("term") for c in e.findall(f"{ATOM}category") if c.get("term")]
            prim = e.find(f"{ARX}primary_category")
            summary = re.sub(r"\s+", " ", (e.findtext(f"{ATOM}summary") or "").strip())
            meta[pid] = {
                "id": pid,
                "title": re.sub(r"\s+", " ", (e.findtext(f"{ATOM}title") or "").strip()),
                "authors": authors,
                "published": (e.findtext(f"{ATOM}published") or "").strip(),
                "updated": (e.findtext(f"{ATOM}updated") or "").strip(),
                "categories": cats,
                "primary_category": prim.get("term") if prim is not None else (cats[0] if cats else ""),
                "abstract": summary,
                "abs_url": f"https://arxiv.org/abs/{pid}",
            }
        time.sleep(3)  # arXiv API politeness
    return meta


def download_pdf(pid, dest):
    url = PDF_URL.format(id=pid)
    r = requests.get(url, headers=UA, timeout=180)
    r.raise_for_status()
    if not r.content[:5].startswith(b"%PDF"):
        raise RuntimeError(f"not a PDF: {r.content[:60]!r}")
    if len(r.content) < 10_000:
        raise RuntimeError(f"PDF suspiciously small: {len(r.content)} bytes")
    with open(dest, "wb") as f:
        f.write(r.content)
    return len(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date-dir", required=True, help="papers/<DATE> directory")
    ap.add_argument("--test-id", help="force-process this arXiv id (bypasses sources & state)")
    args = ap.parse_args()

    os.makedirs(args.date_dir, exist_ok=True)
    st = state.load()

    def is_done(pid):
        e = st.get(pid)
        return e is not None and state.is_done(e)

    if args.test_id:
        ids, src = [args.test_id], "test"
    else:
        # --- source 1: RSS ---
        try:
            rss_ids = rss_paper_ids()
        except Exception as e:
            log(f"RSS fetch failed: {e}")
            rss_ids = []
        unseen_rss = [i for i in rss_ids if not is_done(i)]

        # --- source 2: listing page (fallback when RSS empty/stale + health signal) ---
        l_ids, l_total, l_error = [], 0, None
        try:
            l_ids, l_total = listing_ids()
        except Exception as e:
            l_error = e
            log(f"listing page fetch failed: {e}")

        suspicious = l_error is not None or l_total == 0
        if l_total == 0 and l_error is None:
            log("listing page fetched but contains no arXiv ids at all - suspicious (markup change?)")

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
                log("quiet day: no new econ.TH papers announced")

        # --- retry queue: failed papers with attempts remaining come back ---
        for pid, e in sorted(st.items()):
            if e["status"] == "fail" and e["attempts"] < state.MAX_ATTEMPTS and pid not in ids:
                ids.append(pid)
                src += "+retry"
                log(f"retry-queue: adding {pid} (attempt {e['attempts'] + 1}/{state.MAX_ATTEMPTS})")

    if not ids:
        print("[]")
        return 0
    log(f"source={src}: {len(ids)} paper(s) to process: {', '.join(ids[:10])}")

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
                log(f"{pid}: v1 published {m['published'][:10]} (> {MAX_AGE_DAYS}d, likely replacement) - skip")
                continue
        pdf_path = os.path.join(args.date_dir, f"{pid}.pdf")
        if not os.path.exists(pdf_path):
            try:
                size = download_pdf(pid, pdf_path)
                log(f"{pid}: downloaded PDF ({size} bytes)")
                time.sleep(3)  # politeness between PDF downloads
            except Exception as e:
                log(f"{pid}: PDF download FAILED: {e}")
                continue
        else:
            log(f"{pid}: PDF already on disk")
        meta_path = os.path.join(args.date_dir, f"{pid}.meta.json")
        with open(meta_path, "w") as f:
            json.dump(m, f, indent=2)
        m["pdf_path"] = pdf_path
        m["meta_path"] = meta_path
        papers.append(m)
        if len(papers) >= MAX_PAPERS:
            log(f"reached MAX_PAPERS={MAX_PAPERS}, stopping")
            break

    print(json.dumps(papers))
    return 0


if __name__ == "__main__":
    sys.exit(main())
