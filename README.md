# Perpetuum

*an autonomous research engine*

Every weekday it runs by itself — no SSH session, no interaction: it reads the day's newly announced arXiv papers across **econ.TH** (economic theory), **cs.GT** (game theory), **cs.DM** (discrete mathematics) and **math.CO** (combinatorics), writes a structured report for every paper, **associates research problems the papers inspire but do not state**, and develops the best of them into LaTeX research drafts — delivered to your inbox nightly.

The **digest layer** runs at 14:00 (server time) on weekdays:

1. **Fetch** every newly announced paper in each category (new submissions + cross-lists)
2. **Download** the PDF and extract its full text
3. **Generate** a structured report for each paper with an LLM via [Claude Code](https://docs.anthropic.com/en/docs/claude-code) headless mode
4. **Email** you **one daily briefing per category** (four emails a day), each containing
   every paper's full report, with all PDFs attached

For **math.CO**, papers longer than **30 pages** are skipped (not reported, not
attached); the other three categories include every paper regardless of length.

```
                    ┌──────────────────────────────────────────────┐
                    │  cron: weekdays 14:00 + 21:00 catch-up       │
                    └──────────────────────┬───────────────────────┘
                                           │ run-all.sh
                                           │ (econ.TH → cs.GT → cs.DM → math.CO)
                     ┌─────────────────────┼─────────────────────┐
                     ▼                     ▼                     ▼
             fetch_papers.py        extract_text.py         report.py
             per category:          PDF → plain text        claude -p (headless)
             arXiv RSS ──fallback►  (pypdf)                 structured markdown report
             arxiv.org/list/<cat>/new                            │
             + Atom API metadata                              themes.py
             dedup via state/<cat>.db                          ▼
                                                      build_digest.py + send_mail.py
                                                      one HTML email per category per day:
                                                      overview + themes + full reports + PDFs
```

Day artifacts (`papers/<DATE>/`) are shared across categories: a paper cross-listed
into several of your categories is downloaded and reported **once**, and each
category's digest reuses the same report — no duplicate LLM work, no duplicate
PDFs, while every email still covers its category completely.

## The research layer (ideas + drafts)

Every weekday evening (21:30, after the catch-up run), a second layer runs on
top of the day's reports:

1. **Associate** — batched LLM calls (10 papers each, categories mixed for
   cross-pollination) generate research problems the day's papers *inspire but
   do not state*, each via an explicit operator (technique-transfer,
   flip-assumption, domain-shift, dimension-change, inverse-problem,
   add-friction) and through quality gates (name the lemma it builds on, name
   the proof tool, state the minimal publishable result, difficulty label)
2. **Novelty check** — each idea's keywords are run against the arXiv API and
   one LLM pass flags collisions/adjacent work
3. **Draft** — the day's top 1-3 ideas (auto-picked by score, collisions
   excluded) become LaTeX drafts: formal model setup, numbered conjectures,
   proof attempts with every unproven step marked `[GAP: ...]` and a Gap Log
   on page 1. Drafts are scaffolds, never fake-complete papers
4. **Email** — one evening email with the drafts (PDF + tex attached) and the
   runners-up one-liners; a Saturday 10:00 memo reviews the week's ideas and
   suggests taste recalibration

Everything is idempotent (re-runs reuse `ideas/<date>.json`, skip drafted
ideas) and tuneable (`DRAFTS_PER_DAY`, default 2, auto-extends to 3 when
enough ideas score 8+).

## The daily briefing emails

- **Subject:** `[arXiv econ.TH] 2026-10-05 daily briefing - 2 papers` — one such
  email per category per weekday (`[arXiv cs.GT]`, `[arXiv cs.DM]`,
  `[arXiv math.CO]`)
- **Overview** — one entry per paper: title, authors, arXiv link, quoted TL;DR
- **Today's themes** — one extra LLM call synthesizing common threads, dialogues
  and contrasts across the day's papers (only when 2+ papers)
- **Full reports** — for every paper:
  - TL;DR · Research Question · Model and Setup · Main Results · Methodology
  - Relation to Literature · Comments (strengths / weaknesses / suggestions)
  - **Possible Publication Venues** (ranked, with fit rationale)
  - Tags
- **Attachments:** every paper's PDF (20 MB total cap; math.CO excludes papers
  over 30 pages)

You also get two health emails:
- **Heartbeat** (Mondays 09:00): pipeline status, last run time, 7-day and all-time
  paper stats — so a dead pipeline can never fail *silently*
- **Canary** (at most 1 per 7 days): warning when both arXiv fetch sources come
  back empty/unusable on a weekday (possible markup change or network issue)

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
git clone https://github.com/sammeng5232/perpetuum.git
cd perpetuum

# 2. install python deps (user-level, no root)
bash setup-deps.sh

# 3. configure mail
cp mail.conf.example mail.conf
chmod 600 mail.conf
nano mail.conf            # SMTP_USER / SMTP_PASS / MAIL_FROM / MAIL_TO

# 4. test the pieces
bash dev/smoke-test.sh           # syntax, state, fetch, health, digest (no emails, no LLM)
bash dev/test-claude.sh          # claude headless works?
bash run-all.sh                  # full run (all four categories, sends briefings)
bash run.sh cs.GT                # ...or just one category
bash dev/check-and-test-mail.sh  # validate mail.conf + send a test email

# 5. install the cron schedule (weekdays 14:00 + 21:00)
bash install-cron.sh
```

Done. Reports arrive every weekday, whether or not you ever log in again.

## Configuration

| What | Where | Default |
|---|---|---|
| Categories | `run-all.sh` (`ARXIV_DAILY_CATEGORIES` or edit the list) | `econ.TH cs.GT cs.DM math.CO` |
| math.CO page cap | `run.sh` (`MAX_PAGES` in the case block) | 30 pages (other categories: no cap) |
| Report language/structure | `PROMPT_TEMPLATE` in `report.py` | English, fixed section layout |
| LLM models | `report.py` (`glm-5.3` default, `glm-5.3-1` / `glm-5.3-2` fallbacks) | change to your endpoint's names |
| Mail settings | `mail.conf` (gitignored) | Gmail SMTP 587 |
| Schedule | `install-cron.sh` | weekdays 14:00 digests + 21:00 catch-up + 21:30 research layer, Mon 09:00 heartbeat, Sat 10:00 ideas memo |
| Max papers per run | `MAX_PAPERS` in `fetch_papers.py` | 25 per category (rest → catch-up run) |
| Retry attempts per paper | `MAX_ATTEMPTS` in `state.py` | 3 (1 try + 2 retries) |
| PDF attachment cap | `send_mail.py` | 20 MB |
| Drafts per day | `DRAFTS_PER_DAY` env in `run-ideas.sh` | 2 (3 when enough ideas score 8+) |

## Design notes

- **Exactly-once processing, per category:** processed arXiv IDs are recorded in
  `state/<category>.db` (TSV: id, status, attempts, date); each paper is reported
  exactly once per category, ever. Double runs are therefore harmless.
- **Cross-list reuse:** papers live in a shared per-day directory
  (`papers/<DATE>/`). A paper cross-listed into two of your categories is
  processed once (PDF, text, LLM report) and reused by both digests, so you get
  complete category coverage without duplicate work or duplicate attachments.
- **Page cap for math.CO:** the PDF page count is recorded in each paper's
  metadata; math.CO skips papers over 30 pages (state `skip`, excluded from the
  digest, themes and attachments). Other categories are unaffected — a long
  paper cross-listed into cs.DM is still reported in the cs.DM email.
- **Two fetch sources:** the category RSS feed first; if it is empty *or stale*
  (all items already processed), the pipeline consults
  `arxiv.org/list/<cat>/new` (New submissions + Cross-listings, excluding
  Replacements), which goes live earlier than RSS. Metadata (authors, v1 date,
  categories, abstract) comes from the arXiv Atom API.
- **Bounded retry queue:** a paper whose report fails (LLM timeout, garbled PDF)
  is marked `fail` with an attempt count and automatically retried on later runs
  of its category, up to 3 total attempts, after which it is abandoned and noted
  in the briefing.
- **Catch-up run at 21:00:** if the 14:00 run missed anything (feed lag, failed
  download, transient API error), the 21:00 run picks it up the same day. A
  per-category sent marker (`_sent-<category>`) plus re-send-on-new-papers
  logic guarantees no duplicate emails.
- **Heartbeat:** a Monday-morning email reports pipeline status, last run per
  category and paper statistics. A pipeline that dies stops being silent after
  at most a week.
- **Empty-fetch canary:** on a weekday, if both the RSS feed and the listing page
  of a category are unusable (network error, or a page with zero arXiv IDs — a
  markup-change signal), a throttled warning email is sent (max 1 per category
  per 7 days). A genuinely quiet announcement day (healthy page, zero new
  papers) sends nothing.
- **Day-theme synthesis:** when 2+ papers are reported in a category, one extra
  LLM call over the TL;DRs produces a "Today's themes" section — common threads,
  papers that dialogue with each other, methodological contrasts.
- **Locking:** a global `flock` serializes runs (including the four categories),
  so LLM and arXiv load stays polite.
- **Failure isolation:** one paper failing never blocks the others.
- **No-paper days:** if nothing new was announced in a category, that category
  sends no email.
- **Privacy:** `mail.conf`, `state/`, `papers/`, `logs/` are gitignored and never
  leave your server.

## Project layout

```
perpetuum/
├── run.sh               # one cron run for ONE category (e.g. run.sh cs.GT)
├── run-all.sh           # loops over all categories (cron entry point)
├── run-ideas.sh         # evening research layer (ideas + drafts + email)
├── ideas.py             # associative idea generation + novelty check + scoring
├── draft.py             # idea -> LaTeX draft scaffold (compiles via pdflatex)
├── fetch_papers.py      # per-category RSS + listing fetch, retry queue, PDF download
├── extract_text.py      # PDF → text (pypdf)
├── report.py            # LLM report generation via claude -p
├── themes.py            # day-theme synthesis (one LLM call over TL;DRs)
├── build_digest.py      # assembles one category's briefing markdown
├── send_mail.py         # markdown → HTML email + PDF attachments
├── state.py             # state/<category>.db: dedup + bounded retry accounting
├── health.py            # weekly heartbeat + empty-fetch canary emails
├── mail.conf.example    # SMTP config template
├── setup-deps.sh        # bootstrap pip + install pypdf/requests (user-level)
├── install-cron.sh      # install/refresh cron entries
├── dev/                 # test & maintenance scripts (smoke-test.sh!)
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
- **Force a run manually:** `bash run-all.sh` (all categories) or
  `bash run.sh math.CO` (one category)

## License

[MIT](LICENSE)
