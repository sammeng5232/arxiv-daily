#!/usr/bin/env python3
"""Processing state (seen.db): which papers are done / failed / retriable.

Format (TSV): id <TAB> status <TAB> attempts <TAB> last_date
Legacy format (bare id per line) is read as status=ok, attempts=1.

Usage:
  state.py mark ok|fail <arxiv-id>   # record a report attempt result
  state.py stats                     # print one-line summary
"""
import datetime
import os
import sys

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(HOME_DIR, "seen.db")
MAX_ATTEMPTS = 3  # 1 initial try + 2 retries


def _today():
    return datetime.date.today().isoformat()


def load():
    state = {}
    if os.path.exists(PATH):
        for line in open(PATH):
            line = line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) == 1:
                state[parts[0]] = {"status": "ok", "attempts": 1, "date": ""}
            else:
                try:
                    state[parts[0]] = {"status": parts[1], "attempts": int(parts[2]), "date": parts[3]}
                except (ValueError, IndexError):
                    state[parts[0]] = {"status": "ok", "attempts": 1, "date": ""}
    return state


def save(state):
    tmp = PATH + ".tmp"
    with open(tmp, "w") as f:
        for pid, e in state.items():
            f.write(f"{pid}\t{e['status']}\t{e['attempts']}\t{e['date']}\n")
    os.replace(tmp, PATH)


def is_done(entry):
    """True if a paper should NOT be (re)processed."""
    return entry["status"] == "ok" or entry["attempts"] >= MAX_ATTEMPTS


def mark(pid, ok):
    state = load()
    prev = state.get(pid, {"status": "fail", "attempts": 0, "date": ""})
    e = {"status": "ok" if ok else "fail", "attempts": prev["attempts"] + 1, "date": _today()}
    state[pid] = e
    save(state)
    return e


def stats():
    st = load()
    ok = sum(1 for v in st.values() if v["status"] == "ok")
    retriable = sum(1 for v in st.values() if v["status"] == "fail" and v["attempts"] < MAX_ATTEMPTS)
    exhausted = sum(1 for v in st.values() if v["status"] == "fail" and v["attempts"] >= MAX_ATTEMPTS)
    return len(st), ok, retriable, exhausted


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "mark":
        e = mark(sys.argv[3], sys.argv[2] == "ok")
        print(f"[state] {sys.argv[3]} -> {e['status']} (attempt {e['attempts']}/{MAX_ATTEMPTS})")
    elif len(sys.argv) >= 2 and sys.argv[1] == "stats":
        total, ok, retriable, exhausted = stats()
        print(f"[state] total={total} ok={ok} retriable={retriable} exhausted={exhausted}")
    else:
        print(__doc__)
        sys.exit(2)
