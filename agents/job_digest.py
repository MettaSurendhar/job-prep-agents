import os
import requests
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

NAME = "job-digest"

# Only run on Monday (0) and Thursday (3).
SCHEDULE = {0, 3}

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

# Edit these to match the roles/locations you're targeting.
SEARCH_QUERIES = [
    "fresher software engineer jobs India 2026",
    "entry level full stack developer jobs India React Node",
    "fresher AI engineer RAG LLM jobs India",
]


def search_jobs():
    api_key = os.getenv("OLLAMA_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OLLAMA_API_KEY is not set. This agent needs an Ollama API key "
            "for web search (see docs.ollama.com/api/authentication)."
        )

    all_results = []
    for query in SEARCH_QUERIES:
        r = requests.post(
            "https://ollama.com/api/web_search",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"query": query, "max_results": 5},
            timeout=30,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        all_results.append({"query": query, "results": results})

    return all_results


def run():
    data = search_jobs()

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0, num_ctx=4096),
        tools=[],
        system_prompt=(
            "You write concise job-listing digests for a fresher job seeker "
            "(SDE / full-stack / AI-RAG-engineer roles, based in India). "
            "Given raw search results grouped by query, produce Markdown with one "
            "section per query area, and under each section 2-4 bullet points. "
            "Each bullet should name the role/company if identifiable, a one-line "
            "note on why it's relevant, and end with its source URL. "
            "If a result doesn't look like an actual job posting, skip it. "
            "If nothing relevant was found for a section, say so briefly."
        ),
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": str(data)}]
    })

    return f"# Job Listings Digest\n\n{result['messages'][-1].content}\n"
