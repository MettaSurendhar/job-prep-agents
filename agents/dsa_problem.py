import os
import re
from datetime import datetime
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from . import _history

NAME = "dsa-problem"

# Runs every day (no SCHEDULE attribute = daily).

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

# Rotate through topics so you get broad coverage over time
# instead of the model picking randomly every day.
# "Two Pointers & Sliding Window" appears twice — it's a known weak spot
# (missed a sliding window question in a real interview), so it comes up
# roughly twice as often as other topics.
TOPICS = [
    "Arrays",
    "Strings",
    "Linked Lists",
    "Stacks & Queues",
    "Trees & Binary Search Trees",
    "Graphs (BFS/DFS)",
    "Dynamic Programming",
    "Recursion & Backtracking",
    "Sorting & Searching",
    "Greedy Algorithms",
    "Hashing",
    "Two Pointers & Sliding Window",
    "Two Pointers & Sliding Window",
]


def pick_topic():
    day_of_year = datetime.now().timetuple().tm_yday
    return TOPICS[day_of_year % len(TOPICS)]


def extract_title(text):
    """Pull the short title out of the '## Problem Title' section for logging."""
    match = re.search(r"## Problem Title\s*\n(.+)", text)
    return match.group(1).strip() if match else "(untitled)"


def run():
    topic = pick_topic()

    # Look back at everything logged for this agent so far (across all topics)
    # so the model can avoid repeating a problem it already gave you.
    past_entries = _history.load_recent(NAME, limit=20)
    same_topic_titles = [
        e["summary"] for e in past_entries if e.get("topic") == topic
    ]

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0.4, num_ctx=4096),
        tools=[],
        system_prompt=(
            "You are an interview coach for a fresher preparing for SDE roles. "
            "Given a DSA topic, produce ONE medium-difficulty coding interview problem "
            "on that topic, in Markdown, with this exact structure:\n\n"
            "## Problem Title\n(a short 3-8 word title for this specific problem)\n\n"
            "## Problem\n(clear problem statement)\n\n"
            "## Example\n(one input/output example)\n\n"
            "## Hint 1\n(a nudge toward the approach, no code)\n\n"
            "## Hint 2\n(a stronger nudge, e.g. mention the technique/data structure, "
            "still no code)\n\n"
            "## Solution & Explanation\n(the full approach explained step by step, "
            "followed by a working Python code solution in a code block)\n\n"
            "## Time & Space Complexity\n(brief complexity analysis of the solution)\n\n"
            "If you are given a list of problems already covered on this topic, you MUST "
            "pick a genuinely different problem, not a reworded version of one already given.\n\n"
            "Try to solve it yourself using only the hints first — the Solution section "
            "is there so you can check your answer afterward, not to read before attempting."
        ),
    )

    user_message = f"Topic: {topic}"
    if same_topic_titles:
        already_covered = "\n".join(f"- {t}" for t in same_topic_titles)
        user_message += (
            f"\n\nProblems already covered on this topic (pick something different):\n"
            f"{already_covered}"
        )

    result = agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    })

    content = result["messages"][-1].content

    # Log this problem's title so future runs on the same topic avoid repeating it.
    _history.append(NAME, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "summary": extract_title(content),
    })

    return (
        f"# Daily DSA Problem — {topic}\n\n"
        f"{content}\n"
    )
