import os
import re
import requests
from datetime import datetime
from urllib.parse import quote_plus
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from . import _history

NAME = "dsa-problem"

# Runs every day (no SCHEDULE attribute = daily).

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

# Curated bank of real, well-known LeetCode problems (stable slugs + accurate
# difficulty ratings), grouped by topic. Rather than having the model invent a
# new problem each day (which can't be reliably linked to a real LeetCode page
# or matched to a real explainer video), we rotate through this fixed list —
# the model explains/solves the REAL problem, and we attach real links
# programmatically (no hallucination risk on the URLs themselves).
#
# Tuple: (topic, title, slug, difficulty)
# "Two Pointers & Sliding Window" has 4 entries instead of ~3 — known weak spot
# (missed a sliding window question in a real interview).
PROBLEM_BANK = [
    ("Arrays", "Two Sum", "two-sum", "Beginner"),
    ("Arrays", "Best Time to Buy and Sell Stock", "best-time-to-buy-and-sell-stock", "Beginner"),
    ("Arrays", "Maximum Subarray", "maximum-subarray", "Intermediate"),
    ("Strings", "Valid Anagram", "valid-anagram", "Beginner"),
    ("Strings", "Longest Substring Without Repeating Characters", "longest-substring-without-repeating-characters", "Intermediate"),
    ("Linked Lists", "Reverse Linked List", "reverse-linked-list", "Beginner"),
    ("Linked Lists", "Merge Two Sorted Lists", "merge-two-sorted-lists", "Beginner"),
    ("Linked Lists", "Linked List Cycle", "linked-list-cycle", "Beginner"),
    ("Stacks & Queues", "Valid Parentheses", "valid-parentheses", "Beginner"),
    ("Stacks & Queues", "Min Stack", "min-stack", "Intermediate"),
    ("Trees & Binary Search Trees", "Binary Tree Inorder Traversal", "binary-tree-inorder-traversal", "Beginner"),
    ("Trees & Binary Search Trees", "Validate Binary Search Tree", "validate-binary-search-tree", "Intermediate"),
    ("Trees & Binary Search Trees", "Maximum Depth of Binary Tree", "maximum-depth-of-binary-tree", "Beginner"),
    ("Graphs (BFS/DFS)", "Number of Islands", "number-of-islands", "Intermediate"),
    ("Graphs (BFS/DFS)", "Course Schedule", "course-schedule", "Intermediate"),
    ("Graphs (BFS/DFS)", "Clone Graph", "clone-graph", "Intermediate"),
    ("Dynamic Programming", "Climbing Stairs", "climbing-stairs", "Beginner"),
    ("Dynamic Programming", "Coin Change", "coin-change", "Intermediate"),
    ("Dynamic Programming", "Longest Common Subsequence", "longest-common-subsequence", "Advanced"),
    ("Recursion & Backtracking", "Subsets", "subsets", "Intermediate"),
    ("Recursion & Backtracking", "Permutations", "permutations", "Intermediate"),
    ("Recursion & Backtracking", "Combination Sum", "combination-sum", "Intermediate"),
    ("Sorting & Searching", "Binary Search", "binary-search", "Beginner"),
    ("Sorting & Searching", "Search in Rotated Sorted Array", "search-in-rotated-sorted-array", "Intermediate"),
    ("Sorting & Searching", "Kth Largest Element in an Array", "kth-largest-element-in-an-array", "Intermediate"),
    ("Greedy Algorithms", "Jump Game", "jump-game", "Intermediate"),
    ("Greedy Algorithms", "Gas Station", "gas-station", "Intermediate"),
    ("Hashing", "Group Anagrams", "group-anagrams", "Intermediate"),
    ("Hashing", "Contains Duplicate", "contains-duplicate", "Beginner"),
    ("Hashing", "Top K Frequent Elements", "top-k-frequent-elements", "Intermediate"),
    ("Two Pointers & Sliding Window", "Container With Most Water", "container-with-most-water", "Intermediate"),
    ("Two Pointers & Sliding Window", "3Sum", "3sum", "Intermediate"),
    ("Two Pointers & Sliding Window", "Minimum Window Substring", "minimum-window-substring", "Advanced"),
    ("Two Pointers & Sliding Window", "Sliding Window Maximum", "sliding-window-maximum", "Advanced"),
]


def pick_problem():
    day_of_year = datetime.now().timetuple().tm_yday
    return PROBLEM_BANK[day_of_year % len(PROBLEM_BANK)]


def find_youtube_video(query):
    """Look up a real matching YouTube video via the YouTube Data API v3.
    Requires a free YOUTUBE_API_KEY (see README). Returns a video ID, or None
    if the key isn't set or the lookup fails for any reason — callers should
    always fall back to a plain search link in that case."""
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return None
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 1,
                "key": api_key,
            },
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if items:
            return items[0]["id"]["videoId"]
    except Exception:
        pass
    return None


def build_video_block(title):
    """Return a clickable video thumbnail if a real video was found via the API,
    otherwise a plain search link (never a guessed/hallucinated direct URL).

    Deliberately NOT using an <iframe> embed: many videos have embedding
    disabled by their owner, which fails with YouTube's "Error 153" inside an
    iframe player. A thumbnail image + outbound link always works regardless
    of the video's embed settings."""
    query = f"neetcode {title} explanation"
    video_id = find_youtube_video(query)
    if video_id:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        watch_url = f"https://www.youtube.com/watch?v={video_id}"
        return (
            f'<a href="{watch_url}" target="_blank" class="video-thumb-link">'
            f'<img src="{thumbnail_url}" alt="Explanation video thumbnail" class="video-thumb">'
            f'<span class="video-play-badge">\u25B6 Watch on YouTube</span>'
            f'</a>'
        )
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    return f'<a href="{search_url}">Search NeetCode\'s explanation video on YouTube</a>'


def clean_example_section(content):
    """The model doesn't reliably follow the 'exactly one example, no code
    fences' instruction — it sometimes writes Example 2, Example 3, etc. with
    unbalanced fences, which breaks the page's formatting. This deterministically
    trims the Example section down to just the first example and strips any
    stray fences, regardless of what the model actually produced."""
    match = re.search(r"(## Example\s*\n)(.*?)(?=\n## )", content, re.DOTALL)
    if not match:
        return content

    prefix, example_body = match.group(1), match.group(2)

    # If the model added more examples, cut everything from the second one on.
    cut_match = re.search(r"\n\s*Example\s*\d+\s*:?\s*\n", example_body, re.IGNORECASE)
    if cut_match:
        example_body = example_body[:cut_match.start()]

    # Strip any stray triple-backtick fences — this section shouldn't have any,
    # and any the model left are unbalanced noise that breaks the rest of the page.
    example_body = example_body.replace("```", "").strip()

    cleaned = f"{prefix}{example_body}\n"
    return content[:match.start()] + cleaned + content[match.end():]


def run():
    topic, title, slug, difficulty = pick_problem()
    leetcode_url = f"https://leetcode.com/problems/{slug}/"
    video_block = build_video_block(title)

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0.4, num_ctx=4096),
        tools=[],
        system_prompt=(
            "You are an interview coach for a fresher preparing for SDE roles. "
            "You will be given the exact name of a real, well-known LeetCode problem. "
            "Produce Markdown with this exact structure:\n\n"
            "## Problem\n(restate the problem clearly and accurately, the way it's "
            "commonly phrased for this exact LeetCode problem)\n\n"
            "## Example\nGive EXACTLY ONE input/output example — do not give multiple "
            "examples, and do not use triple-backtick code fences here. Write the input "
            "and output as plain text or with single backticks for inline values only.\n\n"
            "## Hint 1\n(a nudge toward the approach, no code)\n\n"
            "## Hint 2\n(a stronger nudge, e.g. mention the technique/data structure, "
            "still no code)\n\n"
            "## Solutions\n"
            "Provide MULTIPLE solution tiers, each with an explanation of the reasoning, "
            "a working Python code block, and its time/space complexity:\n\n"
            "### Approach 1: Brute Force\n(the naive/obvious approach — explain why it "
            "works and why it's inefficient, then the code, then complexity)\n\n"
            "### Approach 2: Better\n(an improved approach — explain what insight makes "
            "it better than brute force, then the code, then complexity)\n\n"
            "### Approach 3: Optimal\n(the best known approach — explain the key insight "
            "that makes it optimal, then the code, then complexity)\n\n"
            "If brute force and optimal are the only two meaningfully different approaches "
            "for this specific problem, it's fine to skip 'Better' — don't invent a fake "
            "middle approach just to fill the slot.\n\n"
            "## Diagram\n(a Mermaid flowchart or diagram illustrating the optimal approach "
            "step by step — e.g. pointer movements, recursion tree, or data structure state "
            "changes. Use a ```mermaid fenced code block. If a diagram genuinely wouldn't "
            "add clarity for this problem, write 'Not applicable for this problem' instead "
            "of forcing one.)\n\n"
            "IMPORTANT: only use triple-backtick code fences (```) inside the Solutions "
            "section (```python) and the Diagram section (```mermaid). Never use triple "
            "backticks anywhere else in your response, and always close every fence you "
            "open — an unclosed or stray fence breaks the page's formatting.\n\n"
            "Try to solve it yourself using only the hints first — the Solutions section "
            "is there so you can check your answer afterward, not to read before attempting."
        ),
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": f"Problem: {title} (topic: {topic}, difficulty: {difficulty})"}]
    })

    content = result["messages"][-1].content
    content = clean_example_section(content)

    _history.append(NAME, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "summary": title,
    })

    links_section = (
        f"\n## Practice Links\n"
        f"- [Solve it on LeetCode]({leetcode_url})\n\n"
        f"{video_block}\n"
    )

    return (
        f"# Daily DSA Problem — {title} ({topic}) — Difficulty: {difficulty}\n\n"
        f"{content}\n"
        f"{links_section}"
    )