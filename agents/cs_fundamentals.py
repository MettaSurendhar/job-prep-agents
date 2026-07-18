import os
import re
from datetime import datetime
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from . import _history, _websearch

NAME = "cs-fundamentals"

# Runs every day (no SCHEDULE attribute = daily).

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

TOPICS = [
    "Operating Systems",
    "DBMS (Database Management Systems)",
    "Computer Networks",
    "Object-Oriented Programming",
    "System Design Basics",
]


def pick_topic():
    # Weekday-based rotation (Mon-Fri map to the 5 topics, weekends repeat System Design)
    weekday = datetime.now().weekday()
    return TOPICS[weekday % len(TOPICS)]


def extract_concept(text):
    """Pull the concept name out of the '## Concept' section for logging."""
    match = re.search(r"## Concept\s*\n(.+)", text)
    return match.group(1).strip() if match else "(unnamed concept)"


def build_further_reading(concept):
    """Fetch real links for deeper reading on this concept. Falls back to a
    plain search-query link if the live search comes up empty."""
    links = _websearch.duckduckgo_links(f"{concept} explained tutorial", max_results=3)
    if links:
        lines = "\n".join(f"- [{title}]({url})" for title, url in links)
        return f"\n## Further Reading\n{lines}\n"
    fallback_url = _websearch.fallback_search_link(f"{concept} explained")
    return f"\n## Further Reading\n- [Search for '{concept}' explained]({fallback_url})\n"


def run():
    topic = pick_topic()

    past_entries = _history.load_recent(NAME, limit=20)
    same_topic_concepts = [
        e["summary"] for e in past_entries if e.get("topic") == topic
    ]

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0.4, num_ctx=4096),
        tools=[],
        system_prompt=(
            "You are a CS fundamentals tutor helping a fresher prepare for SDE interviews. "
            "Given a subject area, produce ONE bite-sized concept explanation in Markdown "
            "with this structure:\n\n"
            "## Concept\n(name of one specific concept within the subject, e.g. "
            "'Deadlock' for Operating Systems)\n\n"
            "## Explanation\n(3-5 sentences, clear and simple)\n\n"
            "## Diagram\n(a Mermaid flowchart or state diagram illustrating this concept "
            "visually — e.g. process states, a sequence of steps, memory layout, or a "
            "system flow. Use a ```mermaid fenced code block. Most CS concepts CAN be "
            "diagrammed in some useful way — states, steps, before/after, or component "
            "relationships all work well. Only write 'Not applicable for this concept' for "
            "genuinely non-visual concepts like naming conventions or simple definitions; "
            "don't default to skipping it. Never use triple-backtick fences anywhere else "
            "in your response, and always close every fence you open.)\n\n"
            "## Likely Interview Question\n(one question an interviewer might ask about this)\n\n"
            "## How to Answer\n(2-3 bullet points outlining a strong answer approach)\n\n"
            "## Sample Answer\n(a full, well-explained model answer to the interview "
            "question, written as you'd say it out loud)\n\n"
            "If you are given a list of concepts already covered in this subject, you MUST "
            "pick a genuinely different concept, not the same one reworded.\n\n"
            "Keep it concise — this should take 3-5 minutes to read. Try answering the "
            "question yourself first — the Sample Answer is there to self-check afterward."
        ),
    )

    user_message = f"Subject area: {topic}"
    if same_topic_concepts:
        already_covered = "\n".join(f"- {c}" for c in same_topic_concepts)
        user_message += (
            f"\n\nConcepts already covered in this subject (pick something different):\n"
            f"{already_covered}"
        )

    result = agent.invoke({
        "messages": [{"role": "user", "content": user_message}]
    })

    content = result["messages"][-1].content
    concept = extract_concept(content)

    _history.append(NAME, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "summary": concept,
    })

    return (
        f"# Daily CS Fundamentals — {topic}\n\n"
        f"{content}\n"
        f"{build_further_reading(concept)}"
    )
