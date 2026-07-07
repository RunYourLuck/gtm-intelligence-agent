"""
Day 3 — GTM Intelligence Agent
Goal: chain multiple steps together — research the company, research
the specific role/job posting, then reason across both to produce one
structured briefing. This is the shift from "a chatbot with search" to
"an agent that does multi-step reasoning."

New concept vs. Day 2: explicit multi-step chaining
-----------------------------------------------------
Day 2 sent one user message and let Claude decide, in a single turn,
whether to search and what to say. That works, but it's a black box —
you don't control *what* gets researched or *how* the pieces combine.

Day 3 breaks the work into three deliberate calls:
  1. research_company()  -> a focused search-backed call about the company
  2. research_role()     -> a focused search-backed call about the specific
                             job posting (fetches the URL directly if given)
  3. synthesize()        -> a NON-search call that takes the outputs of
                             steps 1 and 2 as input and reasons across
                             them to produce one structured brief

This is "programmatic chaining" — you, the developer, decide the
sequence and what gets passed between steps. Claude isn't deciding the
overall workflow; it's doing focused reasoning at each stage you define.
This is the core skill the FDA/GTM roles want to see: not just calling
an LLM, but architecting how multiple LLM calls combine into a tool.
"""

import os
from anthropic import Anthropic

client = Anthropic()

MODEL = "claude-sonnet-4-6"

SEARCH_TOOL = [{"type": "web_search_20250305", "name": "web_search"}]


def _extract_text(response):
    """Pull just the text blocks out of a response's content list."""
    return "".join(
        block.text for block in response.content if block.type == "text"
    )


def research_company(company_name):
    """
    Step 1: Focused, search-backed research on the company itself —
    business model, products, recent news, competitive pressures.
    """
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
    """
    Step 2: Focused research on the specific role. If `role_input` looks
    like a URL, Claude will fetch and read it directly. Otherwise it
    treats it as a role description/title to research generally.
    """
    print(f"  -> Researching role/posting...")

    is_url = role_input.strip().startswith("http")
    instruction = (
        f"Fetch and read this job posting, then summarize: required "
        f"skills, responsibilities, seniority level, and any signals "
        f"about team structure or priorities. URL: {role_input}"
        if is_url
        else f"Research what this role typically involves and requires: {role_input}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=(
            "You are a GTM research analyst. Summarize job posting or "
            "role information clearly and factually. Keep it under 300 words."
        ),
        tools=SEARCH_TOOL,
        messages=[{"role": "user", "content": instruction}],
    )
    return _extract_text(response)


def synthesize(company_research, role_research, candidate_background=""):
    """
    Step 3: NO search tool here on purpose — this call's job is pure
    reasoning over the material already gathered in steps 1 and 2, not
    fetching anything new. This keeps the final step fast, cheap, and
    focused on synthesis rather than research.
    """
    print("  -> Synthesizing final briefing...\n")

    background_line = (
        f"\n\nCandidate background to weave in: {candidate_background}"
        if candidate_background
        else ""
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


def run_briefing(company_name, role_input, candidate_background=""):
    """The full Day 3 chain: research -> research -> synthesize."""
    company_research = research_company(company_name)
    role_research = research_role(role_input)
    final_brief = synthesize(company_research, role_research, candidate_background)
    return final_brief


def main():
    print("GTM Intelligence Agent — Day 3 (chained research + synthesis)\n")

    company = input("Company name: ").strip()
    role = input("Role title OR job posting URL: ").strip()
    background = input(
        "Your background/angle (optional, press enter to skip): "
    ).strip()

    print("\nRunning chain...\n")
    brief = run_briefing(company, role, background)

    print("=" * 60)
    print(brief)
    print("=" * 60)


if __name__ == "__main__":
    main()
