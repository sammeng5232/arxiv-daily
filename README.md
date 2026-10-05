# arxiv-daily

Automated daily research digest for arXiv categories (default: **econ.TH**, economic theory).

Every weekday at 14:00 (server time), the pipeline runs from `cron` — no SSH session or user interaction required:

1. **Fetch** every newly announced paper in the category (new submissions + cross-lists)
2. **Download** the PDF and extract its full text
3. **Generate** a structured report for each paper with an LLM via [Claude Code](https://docs.anthropic.com/en/docs/claude-code) headless mode
4. **Email** you **one daily briefing** containing every paper's full report, with all PDFs attached

```
                    ┌─────────────────────────────────────────────┐
                    │  cron: weekdays 14:00 + 21:00 catch-up      │
                    └──────────────────────┬──────────────────────┘
                                           │ run.sh (flock-protected)
        ┌──────────────────────────────────┼──────────────────────────────────┐
        ▼                                  ▼                                  ▼
 fetch_papers.py                    extract_text.py                      report.py
 arXiv RSS ──fallback──►            PDF → plain text              claude -p (headless)
 arxiv.org/list/<cat>/new           (pypdf)                       structured markdown report
 + Atom API metadata enrichment                                           │
 dedup via seen.db                                                        ▼
                                                                   send_mail.py
                                                        one HTML email per weekday:
                                                        overview + full reports + PDFs
```

## The daily briefing email

- **Subject:** `[arXiv econ.TH] 2026-10-05 daily briefing - 2 papers`
- **Overview** — one entry per paper: title, authors, arXiv link, quoted TL;DR
- **Full reports** — for every paper:
  - TL;DR · Research Question · Model and Setup · Main Results · Methodology
  - Relation to Literature · Comments (strengths / weaknesses / suggestions)
  - **Possible Publication Venues** (ranked, with fit rationale)
  - Tags
- **Attachments:** every paper's PDF (20 MB total cap)

See [`examples/sample-report.md`](examples/sample-report.md) and [`examples/sample-briefing.md`](examples/sample-briefing.md) for real output.

## Requirements

- A Linux server (tested on Ubuntu 22.04) with:
  - `python3` (3.10+), `cron`, `flock`, `curl`
  - outbound HTTPS (arXiv, PyPI) and SMTP (port 587)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and working
  (`claude -p "hello"` succeeds) — any Anthropic-compatible endpoint works; the model
  names are configured in `report.py`
- An SMTP account for sending (Gmail with an App Password is the easiest)
- Python deps: `pypdf`, `requests` (installed by `setup-deps.sh`, no root needed)

## Quickstart

```bash
# 1. clone anywhere (scripts resolve their own location)
git clone https://github.com/sammeng5232/arxiv-daily.git
cd arxiv-daily

# 2. install python deps (user-level, no root)
bash setup-deps.sh

# 3. configure mail
cp mail.conf.example mail.conf
chmod 600 mail.conf
nano mail.conf            # SMTP_USER / SMTP_PASS / MAIL_FROM / MAIL_TO

# 4. test the pieces
bash dev/test-claude.sh           # claude headless works?
bash run.sh                       # full run (processes today's papers, sends briefing)
bash dev/check-and-test-mail.sh   # validate mail.conf + send a test email

# 5. install the cron schedule (weekdays 14:00 + 21:00)
bash install-cron.sh
```

Done. Reports arrive every weekday, whether or not you ever log in again.

## Configuration

| What | Where | Default |
|---|---|---|
| arXiv category | `RSS_URL` + listing URL in `fetch_papers.py` | `econ.TH` |
| Report language/structure | `PROMPT_TEMPLATE` in `report.py` | English, fixed section layout |
| LLM models | `report.py` (`scrp-assistant`, fallback `scrp-assistant-flash`) | change to your endpoint's names |
| Mail settings | `mail.conf` (gitignored) | Gmail SMTP 587 |
| Schedule | `install-cron.sh` | weekdays 14:00 + 21:00 catch-up |
| Max papers per run | `MAX_PAPERS` in `fetch_papers.py` | 25 |
| PDF attachment cap | `send_mail.py` | 20 MB |

## Design notes

- **Exactly-once processing:** processed arXiv IDs are recorded in `seen.db`; each
  paper is reported exactly once, ever. Double runs are therefore harmless.
- **Two fetch sources:** the category RSS feed first; if it is stale/empty (it lags
  the announcement), the pipeline falls back to scraping `arxiv.org/list/<cat>/new`
  (New submissions + Cross-listings, excluding Replacements). Metadata (authors,
  v1 date, categories, abstract) comes from the arXiv Atom API.
- **Catch-up run at 21:00:** if the 14:00 run missed anything (feed lag, failed
  download, transient API error), the 21:00 run picks it up the same day. Dedup
  guarantees no duplicate emails.
- **Locking:** `flock` prevents overlapping runs.
- **Failure isolation:** one paper failing (bad PDF, LLM timeout) never blocks the
  others; failures are noted in the briefing.
- **No-paper days:** if nothing new was announced, no email is sent.
- **Privacy:** `mail.conf`, `seen.db`, `papers/`, `logs/` are gitignored and never
  leave your server.

## Project layout

```
arxiv-daily/
├── run.sh               # orchestrator (cron entry point)
├── fetch_papers.py      # RSS + listing-page fetch, dedup, PDF download
├── extract_text.py      # PDF → text (pypdf)
├── report.py            # LLM report generation via claude -p
├── send_mail.py         # markdown → HTML email + PDF attachments
├── mail.conf.example    # SMTP config template
├── setup-deps.sh        # bootstrap pip + install pypdf/requests (user-level)
├── install-cron.sh      # install/refresh cron entries
├── dev/                 # one-off test & maintenance scripts
└── examples/            # sample report and daily briefing
```

## Troubleshooting

- **Gmail auth rejected:** you need a 16-character *App Password*
  (`myaccount.google.com/apppasswords`), not your account password. 2-Step
  Verification must be enabled. Spaces in the app password are stripped automatically.
- **`claude -p` errors like `unrecognized_model`:** your endpoint does not know the
  model name — edit the model list at the top of `report.py`.
- **No email but logs say papers were processed:** check `logs/<date>.log` for
  `[mail]` lines; SMTP failures exit with a clear reason.
- **Force a run manually:** `bash run.sh`

## License

[MIT](LICENSE)
