"""
Day 1 — GTM Intelligence Agent
Goal: get the Claude API working locally, make a basic call,
and understand the `messages` structure.

Before running:
  1. Get an API key from https://console.anthropic.com
  2. Set it as an environment variable, e.g.:
       export ANTHROPIC_API_KEY="sk-ant-..."
     (On Windows: set ANTHROPIC_API_KEY=sk-ant-...)
"""

import os
from anthropic import Anthropic

# The client automatically reads ANTHROPIC_API_KEY from your environment.
# You could also pass it explicitly: Anthropic(api_key="sk-ant-...")
client = Anthropic()

# A system prompt sets persistent behavior/context for the whole conversation.
# This is where you'll eventually put "you are a GTM research assistant..."
SYSTEM_PROMPT = (
    "You are a sharp GTM (go-to-market) research assistant. "
    "You help analyze companies and roles for a job search, "
    "focusing on tech stack, pain points, and relevant talking points."
)


def ask_claude(user_message, conversation_history=None):
    """
    Sends one message to Claude and returns the text response.

    `conversation_history` is a list of prior {"role": ..., "content": ...}
    turns. Passing this in is what makes it a real "conversation" rather
    than a single one-off call — the API itself has no memory between
    requests, so you have to resend the history every time.
    """
    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    # response.content is a LIST of content blocks (text now, tool_use later
    # once we add tools on Day 2). For now we just grab the text blocks.
    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    # Append Claude's reply to history so the next turn has full context.
    messages.append({"role": "assistant", "content": reply_text})

    return reply_text, messages


def main():
    print("GTM Intelligence Agent — Day 1 prototype")
    print("Type a message (or 'company:<name>' to try the stretch goal).")
    print("Type 'quit' to exit.\n")

    history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("quit", "exit"):
            print("Session ended.")
            break

        if not user_input:
            continue

        # Stretch goal: if they type "company:Stripe", turn it into a
        # research-framing prompt instead of sending the raw text.
        if user_input.lower().startswith("company:"):
            company = user_input.split(":", 1)[1].strip()
            user_input = (
                f"I'm preparing outreach related to {company}. "
                f"Without doing live research yet, outline the categories "
                f"of information I'd want to gather about them: likely "
                f"tech stack signals, probable pain points for a company "
                f"their size/industry, and 2-3 angles I could use in a "
                f"first outreach message. Keep it to a short structured list."
            )

        reply, history = ask_claude(user_input, history)
        print(f"\nClaude: {reply}\n")


if __name__ == "__main__":
    main()
