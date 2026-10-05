#!/usr/bin/env python3
"""Per-category processing state: which papers are done / failed / skipped.

One TSV database per arXiv category: state/<category>.db
Format per line: id <TAB> status <TAB> attempts <TAB> last_date
status: ok (report exists) | fail (will retry) | skip (intentionally not
processed, e.g. math.CO page cap)
Legacy format (bare id per line) is read as status=ok, attempts=1.

Usage:
  state.py --db <path> mark ok|fail|skip <arxiv-id>
  state.py --db <path> stats
"""
import argparse
import datetime
import os

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
MAX_ATTEMPTS = 3  # 1 initial try + 2 retries (fail status only)


def _today():
    return datetime.date.today().isoformat()


def load(path):
    st = {}
    if path and os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 1:  # legacy: bare id
                st[parts[0]] = {"status": "ok", "attempts": 1, "date": ""}
                continue
            try:
                st[parts[0]] = {"status": parts[1], "attempts": int(parts[2]), "date": parts[3]}
            except (ValueError, IndexError):
                st[parts[0]] = {"status": "ok", "attempts": 1, "date": ""}
    return st


def save(path, st):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        for pid, e in st.items():
            f.write(f"{pid}\t{e['status']}\t{e['attempts']}\t{e['date']}\n")
    os.replace(tmp, path)


def is_done(entry):
    """True if a paper should NOT be (re)processed by this category."""
    return entry["status"] in ("ok", "skip") or entry["attempts"] >= MAX_ATTEMPTS


def mark(path, pid, status):
    """Record an outcome for pid: ok | fail | skip."""
    if status not in ("ok", "fail", "skip"):
        raise ValueError(f"bad status: {status}")
    st = load(path)
    prev = st.get(pid, {"status": "fail", "attempts": 0, "date": ""})
    st[pid] = {"status": status, "attempts": prev["attempts"] + 1, "date": _today()}
    save(path, st)
    return st[pid]


def stats(path):
    """(total, ok, skip, retriable, exhausted) for one category db."""
    st = load(path)
    ok = sum(1 for v in st.values() if v["status"] == "ok")
    skip = sum(1 for v in st.values() if v["status"] == "skip")
    retriable = sum(1 for v in st.values() if v["status"] == "fail" and v["attempts"] < MAX_ATTEMPTS)
    exhausted = sum(1 for v in st.values() if v["status"] == "fail" and v["attempts"] >= MAX_ATTEMPTS)
    return len(st), ok, skip, retriable, exhausted


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mark")
    m.add_argument("status", choices=["ok", "fail", "skip"])
    m.add_argument("pid")
    sub.add_parser("stats")
    args = ap.parse_args()
    if args.cmd == "mark":
        e = mark(args.db, args.pid, args.status)
        print(f"[state] {args.pid} -> {e['status']} (attempt {e['attempts']})")
    else:
        total, ok, skip, retriable, exhausted = stats(args.db)
        print(f"[state] {args.db}: total={total} ok={ok} skip={skip} "
              f"retriable={retriable} exhausted={exhausted}")
