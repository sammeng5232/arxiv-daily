#!/usr/bin/env python3
"""Send report emails via authenticated SMTP (stdlib only).

Config file: mail.conf next to this script, KEY=VALUE lines:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, MAIL_FROM, MAIL_TO
(SMTP_PASS=FILL_ME disables sending -> exit 3)

Usage:
  send_mail.py --paper <meta.json> <report.md>   # one email, PDF attached
  send_mail.py --digest <date> <digest.md>       # summary email, no attachment
"""
import argparse
import html as html_mod
import json
import os
import re
import smtplib
import sys
from email.message import EmailMessage

HOME_DIR = os.environ.get("ARXIV_DAILY_HOME", os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(HOME_DIR, "mail.conf")


def _inline(s):
    s = html_mod.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", s)
    return s


def md_to_html(md):
    """Small markdown renderer (headings, lists, bold/italic, code, links, hr)."""
    out, list_open = [], False

    def close_list():
        nonlocal list_open
        if list_open:
            out.append("</ul>")
            list_open = False

    for raw in md.splitlines():
        line = raw.rstrip()
        st = line.strip()
        m = re.match(r"^(#{1,4})\s+(.*)$", st)
        if m:
            close_list()
            lvl = min(len(m.group(1)) + 1, 5)  # h1->h2 so gmail doesn't make it huge
            out.append(f"<h{lvl}>{_inline(m.group(2))}</h{lvl}>")
        elif re.match(r"^(-{3,}|\*{3,})$", st):
            close_list()
            out.append("<hr>")
        elif re.match(r"^[-*]\s+", st):
            if not list_open:
                out.append("<ul>")
                list_open = True
            item = re.sub(r"^[-*]\s+", "", st)
            out.append("<li>" + _inline(item) + "</li>")
        elif st.startswith(">"):
            close_list()
            out.append("<blockquote style='border-left:3px solid #bbb;margin:8px 0;"
                       "padding:4px 12px;color:#444;'>" + _inline(st.lstrip("> ").strip()) + "</blockquote>")
        elif not st:
            close_list()
        else:
            close_list()
            out.append(f"<p>{_inline(st)}</p>")
    close_list()
    body = "\n".join(out)
    return (
        '<html><body style="font-family:Georgia,serif;font-size:15px;line-height:1.55;'
        'color:#1a1a1a;max-width:780px;margin:0 auto;padding:8px 12px;">'
        '<style>h2{border-bottom:2px solid #d0d0d0;padding-bottom:4px;margin-top:28px;}'
        "h3{margin-top:22px;}code{background:#f4f4f4;padding:1px 5px;border-radius:3px;"
        'font-size:13px;}li{margin:4px 0;}</style>' + body + "</body></html>"
    )


def load_conf():
    conf = {}
    if os.path.exists(CONF):
        for line in open(CONF):
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def send(conf, msg):
    if conf.get("SMTP_PASS", "FILL_ME") == "FILL_ME" or conf.get("SMTP_USER", "FILL_ME") == "FILL_ME":
        print("[mail] SMTP credentials not configured (mail.conf) - NOT sending", file=sys.stderr)
        sys.exit(3)
    passwd = conf["SMTP_PASS"].replace(" ", "").replace("\t", "")
    if "gmail" in conf.get("SMTP_HOST", "") and len(passwd) != 16:
        print(f"[mail] Gmail app password must be 16 chars, got {len(passwd)} - "
              f"create one at https://myaccount.google.com/apppasswords", file=sys.stderr)
        sys.exit(4)
    try:
        with smtplib.SMTP(conf["SMTP_HOST"], int(conf.get("SMTP_PORT", "587")), timeout=60) as s:
            s.starttls()
            s.login(conf["SMTP_USER"], passwd)
            s.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        print("[mail] AUTH REJECTED: app password wrong, or 2-Step Verification / App Passwords "
              "not enabled on the Google account", file=sys.stderr)
        sys.exit(4)
    except smtplib.SMTPServerDisconnected:
        print("[mail] server dropped connection (often caused by malformed credentials or "
              "blocked SMTP) - check the 16-char app password", file=sys.stderr)
        sys.exit(4)
        s.send_message(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paper", nargs=2, metavar=("META", "REPORT"))
    ap.add_argument("--digest", nargs=2, metavar=("DATE", "DIGESTMD"))
    ap.add_argument("--attach-dir", help="attach all PDFs from this directory (total cap 20MB)")
    args = ap.parse_args()
    conf = load_conf()
    frm = conf.get("MAIL_FROM", conf.get("SMTP_USER", "arxiv-daily@scrp"))
    to = conf.get("MAIL_TO", "")
    if not to:
        print("[mail] MAIL_TO not set - NOT sending", file=sys.stderr)
        sys.exit(3)

    if args.paper:
        meta = json.load(open(args.paper[0]))
        report = open(args.paper[1], encoding="utf-8").read()
        title = meta.get("title", "Untitled")
        msg = EmailMessage()
        msg["Subject"] = f"[arXiv econ.TH] {meta['id']} - {title[:70]}"
        msg["From"] = frm
        msg["To"] = to
        msg.set_content(report)
        msg.add_alternative(md_to_html(report), subtype="html")
        pdf = meta.get("pdf_path") or os.path.join(os.path.dirname(args.paper[0]), f"{meta['id']}.pdf")
        if os.path.exists(pdf):
            with open(pdf, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                                   filename=f"{meta['id']}.pdf")
        send(conf, msg)
        print(f"[mail] SENT paper {meta['id']} to {to}")
        return 0

    if args.digest:
        date, dmd = args.digest
        body = open(dmd, encoding="utf-8").read()
        msg = EmailMessage()
        m = re.search(r"Papers announced today \(new \+ cross-lists\): \*\*(\d+)\*\*", body)
        n = m.group(1) if m else None
        msg["Subject"] = f"[arXiv econ.TH] {date} daily briefing" + (f" - {n} paper" + ("s" if n != "1" else "") if n else "")
        msg["From"] = frm
        msg["To"] = to
        msg.set_content(body)
        msg.add_alternative(md_to_html(body), subtype="html")
        if args.attach_dir and os.path.isdir(args.attach_dir):
            import glob as _glob
            total = 0
            pdfs = sorted(_glob.glob(os.path.join(args.attach_dir, "*.pdf")))
            for pdf in pdfs:
                with open(pdf, "rb") as f:
                    data = f.read()
                if total + len(data) > 20_000_000:
                    print(f"[mail] PDF attachment cap reached, skipping {os.path.basename(pdf)}")
                    continue
                msg.add_attachment(data, maintype="application", subtype="pdf",
                                   filename=os.path.basename(pdf))
                total += len(data)
            print(f"[mail] attached {min(len(pdfs), 99)} PDFs, {total} bytes" if pdfs else "[mail] no PDFs to attach")
        send(conf, msg)
        print(f"[mail] SENT daily briefing {date} to {to}")
        return 0

    ap.error("need --paper or --digest")


if __name__ == "__main__":
    sys.exit(main())
