#!/usr/bin/env python3
"""Pipeline health: weekly heartbeat email + empty-fetch canary.

Usage:
  health.py heartbeat [--dry-run]   # Monday summary: pipeline status + 7-day stats
  health.py canary [--dry-run]      # warning: both fetch sources empty/unusable
                                     (throttled to 1 email per 7 days)
"""
import datetime
import glob
import os
import re
import sys
from email.message import EmailMessage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import send_mail
import state

HOME = os.path.dirname(os.path.abspath(__file__))
STALE_DAYS = 4        # heartbeat warns if last run is older than this
CANARY_FILE = os.path.join(HOME, "locks", ".last-canary")


def last_run():
    """Timestamp of the most recent '==== arxiv-daily run ...' line in any log."""
    logs = sorted(glob.glob(os.path.join(HOME, "logs", "*.log")))
    for lg in reversed(logs):
        try:
            content = open(lg, errors="replace").read()
        except OSError:
            continue
        m = re.findall(r"==== arxiv-daily run ([0-9-]+ [0-9:]+) ====", content)
        if m:
            return m[-1]
    return None


def stats_7d():
    today = datetime.date.today()
    papers = reports = 0
    for n in range(7):
        d = (today - datetime.timedelta(days=n)).isoformat()
        dd = os.path.join(HOME, "papers", d)
        if os.path.isdir(dd):
            papers += len(glob.glob(os.path.join(dd, "*.meta.json")))
            reports += len([p for p in glob.glob(os.path.join(dd, "reports", "*.md"))
                            if not os.path.basename(p).startswith("_")])
    return papers, reports


def send_md(subject, md, dry):
    conf = send_mail.load_conf()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = conf.get("MAIL_FROM", conf.get("SMTP_USER", "arxiv-daily"))
    msg["To"] = conf.get("MAIL_TO", "")
    msg.set_content(md)
    msg.add_alternative(send_mail.md_to_html(md), subtype="html")
    if dry:
        print(f"[health] DRY-RUN, would send: {subject}\n")
        print(md)
        return
    send_mail.send(conf, msg)
    print(f"[health] sent: {subject}")


def heartbeat(dry):
    today = datetime.date.today()
    lr = last_run()
    papers, reports = stats_7d()
    total, ok, retriable, exhausted = state.stats()
    stale = True
    if lr:
        try:
            lr_date = datetime.datetime.strptime(lr[:10], "%Y-%m-%d").date()
            stale = (today - lr_date).days > STALE_DAYS
        except ValueError:
            stale = True
    status = "WARNING - no recent runs detected" if (stale or not lr) else "OK"
    subject = f"[arXiv econ.TH] Heartbeat {today} - pipeline {status}"
    md = (f"# arXiv econ.TH pipeline heartbeat - {today}\n\n"
          f"- **Status:** {status}\n"
          f"- **Last run:** {lr or 'none found'}\n"
          f"- **Papers processed (last 7 days):** {papers} (reports generated: {reports})\n"
          f"- **All-time:** {ok} reported OK, {retriable} pending retry, "
          f"{exhausted} failed after retries\n\n"
          f"Sent automatically every Monday. No action needed if status is OK.\n")
    send_md(subject, md, dry)


def canary(dry):
    today = datetime.date.today()
    if os.path.exists(CANARY_FILE):
        try:
            last = datetime.date.fromisoformat(open(CANARY_FILE).read().strip())
            if (today - last).days < 7:
                print(f"[health] canary throttled (last sent {last})")
                return
        except ValueError:
            pass
    subject = f"[arXiv econ.TH] WARNING {today} - empty fetch on a weekday"
    md = (f"# Empty-fetch warning - {today}\n\n"
          f"Today's run found **no parseable items** from either the econ.TH RSS feed or "
          f"the arxiv.org listing page.\n\n"
          f"Possible causes: arXiv markup change, network issue from the server, or an "
          f"arXiv announcement holiday.\n\n"
          f"Check with:\n\n"
          f"    tail -30 {HOME}/logs/{today}.log\n"
          f"    bash {HOME}/run.sh\n\n"
          f"(This warning is throttled to at most one email per 7 days.)\n")
    send_md(subject, md, dry)
    if not dry:
        os.makedirs(os.path.dirname(CANARY_FILE), exist_ok=True)
        with open(CANARY_FILE, "w") as f:
            f.write(today.isoformat())


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    dry = "--dry-run" in sys.argv
    if cmd == "heartbeat":
        heartbeat(dry)
    elif cmd == "canary":
        canary(dry)
    else:
        print(__doc__)
        sys.exit(2)
