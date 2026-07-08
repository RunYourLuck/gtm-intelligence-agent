"""
GTM Intelligence Agent
Goal: wrap the Day 3 chain in a proper CLI tool — flags instead of
interactive prompts, and output saved to a file so each run produces
a real, shareable artifact.

New concept vs. Day 3: argparse + file output
------------------------------------------------
Day 3 was interactive (input() prompts) — fine for testing, but not
how a "real tool" behaves. A real CLI tool:
  - Accepts arguments up front:  --company, --role, --background
  - Can be run non-interactively (scriptable, chainable with other
    tools, usable in automation later)
  - Produces a durable output (a saved .md file), not just something
    that scrolls past in the terminal

Day 5 upgrade — web_fetch for job posting URLs
----------------------------------------------
When --role is a URL, we now use the dedicated web_fetch tool instead
of web_search. web_fetch reads the full page content directly, so
Claude gets the actual job description rather than searching around it.
web_search is still used for text-based role lookups and company research.
"""

import argparse
import os
import re
from datetime import datetime
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-6"
SEARCH_TOOL = [{"type": "web_search_20250305", "name": "web_search"}]
FETCH_TOOL = [{"type": "web_fetch_20250124", "name": "web_fetch"}]
# When fetching a job URL, expose both tools so Claude can follow
# redirects or do a quick search if the page is behind a login wall.
FETCH_AND_SEARCH_TOOLS = FETCH_TOOL + SEARCH_TOOL


def _extract_text(response):
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


def research_company(company_name):
    print(f"  -> Researching company: {company_name}...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=(
            "You are a GTM research analyst. Research the given company "
            "using web search. Focus on: business model, core products, "
            "recent strategic moves (last 6-12 months), and competitive "
            "pressures. Be factual and current. Keep it under 400 words."
        ),
        tools=SEARCH_TOOL,
        messages=[
            {"role": "user", "content": f"Research {company_name} for GTM purposes."}
        ],
    )
    return _extract_text(response)


def research_role(role_input):
    """Research a role by either fetching a job posting URL directly
    (using web_fetch for full page content) or searching for general
    role information (using web_search)."""
    is_url = role_input.strip().startswith("http")

    if is_url:
        print(f"  -> Fetching job posting URL: {role_input}...")
        tools = FETCH_AND_SEARCH_TOOLS
        instruction = (
            f"Use the web_fetch tool to fetch and read this job posting in full, "
            f"then summarize: required skills, responsibilities, seniority level, "
            f"and any signals about team structure or priorities. "
            f"If the page requires login or returns an error, use web_search as a "
            f"fallback to find the same posting. URL: {role_input}"
        )
    else:
        print(f"  -> Researching role: '{role_input}'...")
        tools = SEARCH_TOOL
        instruction = (
            f"Research what this role typically involves and requires: {role_input}"
        )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=(
            "You are a GTM research analyst. Summarize job posting or "
            "role information clearly and factually. Keep it under 400 words. "
            "Focus on: required skills, key responsibilities, seniority level, "
            "team structure signals, and any hints about what the hiring manager "
            "actually cares about."
        ),
        tools=tools,
        messages=[{"role": "user", "content": instruction}],
    )
    return _extract_text(response)


def synthesize(company_research, role_research, candidate_background="", years_experience=""):
    print("  -> Synthesizing final briefing...\n")

    background_line = (
        f"\n\nCandidate background to weave in: {candidate_background}"
        if candidate_background
        else ""
    )
    years_line = (
        f" The candidate has {years_experience} years of relevant experience "
        f"— use this exact figure in the outreach opener, don't leave a "
        f"placeholder."
        if years_experience
        else " If you don't know years of experience, phrase the outreach "
        "opener so it doesn't need a specific number (avoid placeholders "
        "like '[X]')."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=(
            "You are a GTM research assistant producing a final briefing "
            "for a job candidate. You will be given company research and "
            "role research. Synthesize them into ONE structured briefing "
            "with these exact sections: \n"
            "1. Company Snapshot (2-3 bullets)\n"
            "2. Role Fit Signals (what this role likely needs, tied to "
            "what the company is prioritizing right now)\n"
            "3. Talking Points (3-4 specific points connecting the "
            "candidate's angle to the company's current priorities)\n"
            "4. Draft Outreach Opener (2-3 sentences, specific not generic)\n"
            "Keep the whole thing under 350 words. Be concrete, not generic."
            f"{years_line}"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"COMPANY RESEARCH:\n{company_research}\n\n"
                    f"ROLE RESEARCH:\n{role_research}"
                    f"{background_line}"
                ),
            }
        ],
    )
    return _extract_text(response)


def slugify(text):
    """Turn a company name into a safe filename fragment."""
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s]+", "-", text).strip("-")


def save_brief(company_name, brief_text, output_dir="briefs"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d")
    filename = f"{timestamp}_{slugify(company_name)}_brief.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(brief_text)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="GTM Intelligence Agent — generate a structured research "
        "briefing for a company and role."
    )
    parser.add_argument("--company", default=None, help="Company name, e.g. Stripe")
    parser.add_argument(
        "--role",
        default=None,
        help="Role title (e.g. 'Forward Deployed Engineer') or a job posting URL",
    )
    parser.add_argument(
        "--background",
        default="",
        help="Your background/angle to tailor talking points and outreach",
    )
    parser.add_argument(
        "--years",
        default="",
        help="Years of relevant experience (used in the outreach opener)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print only, don't save the briefing to a file",
    )
    parser.add_argument(
        "--output-dir",
        default="briefs",
        help="Folder to save the briefing into, e.g. a path inside your "
        "Obsidian vault. Defaults to a local 'briefs' folder.",
    )

    args = parser.parse_args()

    # Hybrid mode: any required detail not passed as a flag gets asked
    # for interactively (Day 3 behavior as a fallback).
    if not args.company:
        args.company = input("Company name: ").strip()
    if not args.role:
        args.role = input("Role title or job posting URL: ").strip()
    if not args.company or not args.role:
        parser.error("company and role are required")
    if not args.background:
        args.background = input("Your background/angle (optional, Enter to skip): ").strip()
    if not args.years:
        args.years = input("Years of relevant experience (optional, Enter to skip): ").strip()

    print(f"\nGTM Intelligence Agent — building briefing for {args.company}\n")

    company_research = research_company(args.company)
    role_research = research_role(args.role)
    brief = synthesize(company_research, role_research, args.background, args.years)

    print("=" * 60)
    print(brief)
    print("=" * 60)

    if not args.no_save:
        filepath = save_brief(args.company, brief, output_dir=args.output_dir)
        print(f"\nSaved to: {filepath}")


if __name__ == "__main__":
    main()
