#!/usr/bin/env python3
"""Health monitoring: weekly heartbeat email + empty-fetch canary.

Usage:
  health.py heartbeat [--dry-run]
  health.py canary <category> [--dry-run]

- heartbeat: Monday 09:00 cron; reports last successful run per category,
  7-day paper counts, per-category state, and disk usage.
- canary: sent by run.sh when a category's fetch found no usable source on a
  weekday; throttled to one email per category per 7 days.
"""
import datetime
import glob
import json
import os
import smtplib
import sys
from email.message import EmailMessage

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
CATEGORIES = ["econ.TH", "cs.GT", "cs.DM", "math.CO"]
CANARY_THROTTLE_DAYS = 7
STALE_AFTER_HOURS = 48


def _today():
    return datetime.date.today().isoformat()


def _weekday():
    return datetime.date.today().weekday() < 5


def load_conf():
    conf = {}
    cf = os.path.join(HOME_DIR, "mail.conf")
    if os.path.exists(cf):
        for line in open(cf):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def send_mail(subject, body, dry=False):
    conf = load_conf()
    frm = conf.get("MAIL_FROM", conf.get("SMTP_USER", "arxiv-daily@scrp"))
    to = conf.get("MAIL_TO", "")
    if not to or conf.get("SMTP_PASS", "FILL_ME") == "FILL_ME":
        print("[health] mail not configured - printing instead")
        dry = True
    if dry:
        print(f"--- DRY RUN ---\nSubject: {subject}\n\n{body}")
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = frm
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(conf["SMTP_HOST"], int(conf.get("SMTP_PORT", "587")), timeout=60) as s:
        s.starttls()
        s.login(conf["SMTP_USER"], conf["SMTP_PASS"].replace(" ", ""))
        s.send_message(msg)
    print(f"[health] sent: {subject}")


def last_runs():
    """Last RUN-DONE marker per category, from logs/*.log."""
    runs = {}
    for lg in sorted(glob.glob(os.path.join(HOME_DIR, "logs", "*.log"))):
        try:
            lines = open(lg, errors="replace").read().splitlines()
        except OSError:
            continue
        for line in lines:
            if "RUN-DONE" in line:
                d = dict(kv.split("=", 1) for kv in line.split() if "=" in kv)
                cat = d.get("category")
                if cat:
                    runs[cat] = d
    return runs


def stats_7d():
    """(papers, reports) announced in the last 7 day-dirs."""
    cutoff = datetime.date.today() - datetime.timedelta(days=7)
    papers = reports = 0
    for dd in glob.glob(os.path.join(HOME_DIR, "papers", "*")):
        base = os.path.basename(dd)
        try:
            d = datetime.date.fromisoformat(base)
        except ValueError:
            continue
        if d < cutoff:
            continue
        papers += len(glob.glob(os.path.join(dd, "*.meta.json")))
        for rp in glob.glob(os.path.join(dd, "reports", "*.md")):
            if not os.path.basename(rp).startswith("_"):
                reports += 1
    return papers, reports


def dir_size_mb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total / 1e6


def heartbeat(dry=False):
    today = _today()
    runs = last_runs()
    now = datetime.datetime.now()
    stale = []
    lines = []
    for cat in CATEGORIES:
        r = runs.get(cat)
        if not r:
            lines.append(f"- {cat}: never ran")
            stale.append(cat)
            continue
        try:
            ts = datetime.datetime.strptime(r.get("ts", ""), "%Y-%m-%dT%H:%M:%S")
            age_h = (now - ts).total_seconds() / 3600
        except ValueError:
            age_h = 999
        if age_h > STALE_AFTER_HOURS:
            stale.append(cat)
        lines.append(f"- {cat}: last run {r.get('ts', '?')} "
                     f"(fetched {r.get('fetched', '?')}, ok {r.get('ok', '?')}, "
                     f"fail {r.get('fail', '?')})")
    status = "OK" if not stale else f"STALE ({', '.join(stale)} has no run in {STALE_AFTER_HOURS}h)"

    papers, reports = stats_7d()
    state_lines = []
    for db in sorted(glob.glob(os.path.join(HOME_DIR, "state", "*.db"))):
        cat = os.path.basename(db)[:-3]
        try:
            import state as st
            total, ok, skip, retriable, exhausted = st.stats(db)
            state_lines.append(f"- {cat}: {ok} reported, {skip} skipped, "
                               f"{retriable} pending retry, {exhausted} exhausted (of {total})")
        except Exception as e:
            state_lines.append(f"- {cat}: state unreadable ({e})")

    body = (f"# arXiv pipeline heartbeat - {today}\n\n"
            f"- Status: {status}\n"
            f"- Last successful runs:\n" + "\n".join(lines) + "\n"
            f"- Papers announced in last 7 days: {papers} (reports generated: {reports})\n"
            f"- State per category:\n" + "\n".join(state_lines) + "\n"
            f"- Disk: {HOME_DIR} uses {dir_size_mb(HOME_DIR):.1f} MB\n\n"
            "This is an automated weekly heartbeat. No action is needed if everything "
            "looks normal.\n")
    send_mail(f"[arXiv daily] Heartbeat {today} - pipeline {status}", body, dry=dry)


def canary(category, dry=False):
    today = _today()
    if not _weekday():
        print("[health] weekend - empty fetch is expected, no canary")
        return
    throttle = os.path.join(HOME_DIR, "locks", f".last-canary-{category}")
    if os.path.exists(throttle):
        age_d = (datetime.datetime.now() - datetime.datetime.fromtimestamp(
            os.path.getmtime(throttle))).days
        if age_d < CANARY_THROTTLE_DAYS:
            print(f"[health] canary for {category} throttled (sent {age_d}d ago)")
            return
    body = (f"# Empty fetch warning - {category} - {today}\n\n"
            f"Today's {category} run found no usable source (both the RSS feed and "
            f"the listing page returned nothing) on a weekday.\n\n"
            "Possible causes: arXiv announcement delay, network issues from the server, "
            "or an arXiv markup change breaking the scraper.\n\n"
            "What to do:\n"
            f"1. Check today's log: tail -50 ~/arxiv-daily/logs/{today}.log\n"
            f"2. Retry manually: bash ~/arxiv-daily/run.sh {category}\n"
            "3. If it persists, inspect fetch_papers.py against the current arXiv markup.\n\n"
            "The 21:00 catch-up run will retry automatically.\n")
    send_mail(f"[arXiv {category}] WARNING {today} - empty fetch on a weekday", body, dry=dry)
    if not dry:
        os.makedirs(os.path.dirname(throttle), exist_ok=True)
        open(throttle, "w").write(today)


def main():
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    if args and args[0] == "heartbeat":
        heartbeat(dry)
    elif args and args[0] == "canary":
        if len(args) < 2:
            print("usage: health.py canary <category> [--dry-run]")
            return 1
        canary(args[1], dry)
    else:
        print("usage: health.py heartbeat [--dry-run] | health.py canary <category> [--dry-run]")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
