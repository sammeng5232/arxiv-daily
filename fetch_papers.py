#!/usr/bin/env python3
"""Fetch today's new econ.TH papers from arXiv (new + cross-lists).

- Primary source: RSS feed of econ.TH (reflects the current day's announcement).
- Enrichment: Atom API (id_list batch) for clean metadata (v1 date, authors, categories).
- Dedup: seen.db (one arXiv ID per line). A paper is processed exactly once.
- Downloads PDFs into papers/<DATE>/<id>.pdf and writes <id>.meta.json.

Output: JSON list of paper dicts on stdout (for run.sh to consume).
Exit codes: 0 ok (possibly 0 papers), 1 fatal error, 2 nothing new (shortcut).
"""
import argparse
import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import requests

DC = "{http://purl.org/dc/elements/1.1/}"
ARX = "{http://arxiv.org/schemas/atom}"
ATOM = "{http://www.w3.org/2005/Atom}"

RSS_URL = "https://export.arxiv.org/rss/econ.TH"
API_URL = "https://export.arxiv.org/api/query"
PDF_URL = "https://arxiv.org/pdf/{id}"
UA = {"User-Agent": "arxiv-daily/1.0 (automated research digest; https://github.com/sammeng5232/arxiv-daily)"}
MAX_PAPERS = 25          # hard cap per run
MAX_AGE_DAYS = 14        # v1 must be within N days (filters replacements of old papers)
TEXT_TOO_BIG = 200_000   # chars

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))


def log(msg):
    print(f"[fetch] {msg}", file=sys.stderr, flush=True)


def seen_ids():
    p = os.path.join(HOME_DIR, "seen.db")
    if not os.path.exists(p):
        return set()
    with open(p) as f:
        return {line.strip() for line in f if line.strip()}


def mark_seen(pid):
    with open(os.path.join(HOME_DIR, "seen.db"), "a") as f:
        f.write(pid + "\n")


def id_from_url(url):
    m = re.search(r"abs/([0-9]{4}\.[0-9]{4,5})(v[0-9]+)?", url)
    return m.group(1) if m else None


def listing_ids():
    """Fallback: scrape arxiv.org/list/econ.TH/new (authoritative, live earlier than RSS).
    Keeps New submissions + Cross-listings, excludes Replacement submissions."""
    r = requests.get("https://arxiv.org/list/econ.TH/new", headers=UA, timeout=60)
    r.raise_for_status()
    cut = r.text.split("Replacement submissions")[0]
    ids, seen = [], set()
    for pid in re.findall(r"arXiv:(\d{4}\.\d{4,5})", cut):
        if pid not in seen:
            seen.add(pid)
            ids.append(pid)
    return ids


def rss_paper_ids():
    """Return list of (id, rss_title, rss_desc, rss_authors) from today's econ.TH RSS."""
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


def strip_html(s):
    return re.sub(r"<[^>]+>", " ", s or "")


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
    ap.add_argument("--test-id", help="force-process this arXiv id (bypasses RSS & seen.db)")
    args = ap.parse_args()

    os.makedirs(args.date_dir, exist_ok=True)
    seen = seen_ids()

    if args.test_id:
        ids = [args.test_id]
    else:
        try:
            ids = rss_paper_ids()
            src = "rss"
        except Exception as e:
            log(f"RSS fetch failed: {e}")
            ids, src = [], "rss-error"
        if not ids:
            log("RSS has no items - falling back to listing page arxiv.org/list/econ.TH/new")
            try:
                ids = listing_ids()
                src = "listing-page"
            except Exception as e:
                log(f"listing page fetch failed: {e}")
        if not ids:
            log("no new papers found (rss + listing page) - nothing to do")
            print("[]")
            return 0
        log(f"source={src}: {len(ids)} candidate ids: {', '.join(ids[:10])}")
        ids = [i for i in ids if i not in seen]
        if not ids:
            log("all RSS items already processed")
            print("[]")
            return 0

    meta = api_enrich(ids)
    now = time.time()
    papers = []
    for pid in ids:
        m = meta.get(pid)
        if not m:
            log(f"{pid}: no API metadata, skipping")
            continue
        if not args.test_id:
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
