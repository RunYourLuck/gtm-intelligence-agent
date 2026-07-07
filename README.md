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
1. `research_company()` — a search-backed call focused on the company:
   business model, products, recent moves, competitive pressure
2. `research_role()` — a search-backed call focused on the specific
   role or job posting
3. `synthesize()` — a non-search call that reasons over steps 1 and 2
   and produces one structured brief (Company Snapshot, Role Fit
   Signals, Talking Points, Draft Outreach Opener)

This is "programmatic chaining" — the workflow shape and what data
flows between calls is deliberately architected, not left to one
freeform prompt.

## Build history
The `archive/` folder holds the day-by-day scripts this was built up
from: a basic API call, then adding web search, then chaining research
into synthesis. `gtm_agent.py` is the final, wrapped version of that
same chain as a real CLI tool.

