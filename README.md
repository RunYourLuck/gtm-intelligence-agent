# GTM Intelligence Agent

An agent that researches a company and a job posting, then generates
a structured briefing with talking points and a draft outreach opener
— built directly on the Claude API (Python).

## Project structure

```
gtm-agent/
├── gtm_agent.py          # the main tool — run this
├── requirements.txt      # dependencies
├── .gitignore            # keeps API keys and personal briefs out of git
├── archive/              # earlier day-by-day builds, kept for reference
│   ├── day1_basic_call.py
│   ├── day2_web_search.py
│   └── day3_chained_research.py
└── README.md
```

## Setup

```bash
git clone <your-repo-url>
cd gtm-agent
pip3 install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

## Usage

```bash
python3 gtm_agent.py \
  --company "Acme Corp" \
  --role "https://example.com/jobs/some-role" \
  --background "Salesforce Admin, Salesforce Consultant, GTM Systems Engineer, Business Analyst" \
  --years 5
```

Flags:

- `--company` (required) — company name
- `--role` (required) — role title OR a job posting URL
- `--background` (optional) — your angle, used to tailor talking points
- `--years` (optional) — avoids placeholder text in the outreach opener
- `--output-dir` (optional) — where to save the briefing (default: `briefs/`)
- `--no-save` (optional) — print only, skip saving to file

Each run saves a timestamped `.md` briefing, e.g. `briefs/2026-07-06_acme-corp_brief.md`.

## How it works

1. **`research_company()`** — uses `web_search` to pull current intel on the
   company: business model, core products, recent strategic moves, competitive
   pressure
2. **`research_role()`** — behavior depends on what you pass as `--role`:
   - **Job posting URL** → uses `web_fetch` to read the full page directly,
     getting the actual job description rather than search results about it.
     Falls back to `web_search` if the page is behind a login wall.
   - **Role title text** → uses `web_search` to research what the role
     typically involves and requires
3. **`synthesize()`** — a non-search call that reasons over steps 1 and 2 and
   produces one structured brief: Company Snapshot, Role Fit Signals, Talking
   Points, Draft Outreach Opener

This is "programmatic chaining" — the workflow shape and what data flows
between calls is deliberately architected, not left to one freeform prompt.
Each call uses the right tool for the job (`web_fetch` vs. `web_search`),
which is a meaningful architectural choice, not just a different API call.

## Known limitations

- **Login-walled job postings** (Workday, Greenhouse, Lever behind SSO) —
  `web_fetch` will fall back to `web_search` automatically, but the result
  will be less specific than a direct page read. In practice, postings on
  company career pages or LinkedIn tend to work well.

## Build history

| Stage | What changed                                                                   |
| ----- | ------------------------------------------------------------------------------ |
| Day 1 | Basic Claude API call                                                          |
| Day 2 | Added `web_search` tool use                                                    |
| Day 3 | Chained company research → role research → synthesis                           |
| Day 4 | Wrapped as a real CLI tool (argparse, file output, `--flags`)                  |
| Day 5 | Swapped `web_search` for `web_fetch` on job posting URLs for full-page content |

The `archive/` folder holds the day-by-day scripts for reference. `gtm_agent.py`
is the current production version.
