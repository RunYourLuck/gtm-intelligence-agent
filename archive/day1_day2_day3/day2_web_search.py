"""
Day 2 — GTM Intelligence Agent
Goal: add web search as a tool. The agent can now fetch and summarize
a real job posting (or company info) instead of relying only on
Claude's training knowledge.

New concept vs. Day 1: the "agent loop"
----------------------------------------
Previously, one call to client.messages.create() gave you a final
text answer. Now, Claude might respond with a `tool_use` block instead
of (or alongside) text — meaning "I want to run this tool before I can
answer." Your code has to:
  1. Send the message
  2. Check: did Claude ask to use a tool?
  3. If yes: no action needed on your end for web_search specifically —
     it's a SERVER-side tool, meaning Anthropic's API runs the search
     itself and hands Claude the results automatically. You just need
     to keep reading the response until Claude produces a final
     text-only answer.
  4. If Claude's response is plain text with no further tool calls,
     you're done — that's the final answer.

(Note: web_search is a "server tool" — unlike custom tools you write
yourself, you don't implement the search logic; Anthropic runs it and
Claude sees the results as part of the same response. This makes Day 2
simpler than it might sound.)
"""

import os
from anthropic import Anthropic

client = Anthropic()

SYSTEM_PROMPT = (
    "You are a sharp GTM (go-to-market) research assistant. "
    "You help analyze companies and job postings for a job search, "
    "focusing on tech stack, pain points, and relevant talking points. "
    "When asked about a company or role, use web search to find current, "
    "specific information rather than relying only on what you already know."
)

# This is the tool definition. web_search is a built-in Anthropic tool —
# you don't write the search logic yourself, you just declare that
# Claude is allowed to use it.
TOOLS = [
    {
        "type": "web_search_20250305",
        "name": "web_search",
    }
]


def ask_claude(user_message, conversation_history=None):
    """
    Sends a message to Claude with web search enabled.
    Returns the final text reply once Claude is done using tools.
    """
    messages = conversation_history or []
    messages.append({"role": "user", "content": user_message})

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages,
    )

    # Because web_search is a server-side tool, Anthropic handles the
    # actual searching internally. The response.content list may include
    # a mix of block types: "text", "server_tool_use", "web_search_tool_result".
    # We just need to extract the final text blocks for display.
    reply_text = "".join(
        block.text for block in response.content if block.type == "text"
    )

    # Store Claude's full response (not just the text) in history, since
    # it may reference the tool calls it made — this keeps context intact
    # if the conversation continues.
    messages.append({"role": "assistant", "content": response.content})

    return reply_text, messages, response


def main():
    print("GTM Intelligence Agent — Day 2 (web search enabled)")
    print("Try: 'Research <company> for a GTM/sales role'")
    print("Or paste a job posting URL and ask for a summary.")
    print("Type 'quit' to exit.\n")

    history = []

    while True:
        user_input = input("You: ").strip()

        if user_input.lower() in ("quit", "exit"):
            print("Session ended.")
            break

        if not user_input:
            continue

        reply, history, raw_response = ask_claude(user_input, history)
        print(f"\nClaude: {reply}\n")

        # Small transparency touch: show whether a search actually happened.
        used_search = any(
            block.type == "server_tool_use" for block in raw_response.content
        )
        if used_search:
            print("[Note: this answer used a live web search]\n")


if __name__ == "__main__":
    main()
