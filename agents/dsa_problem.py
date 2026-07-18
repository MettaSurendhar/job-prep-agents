import os
from datetime import datetime
from urllib.parse import quote_plus
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from . import _history

NAME = "dsa-problem"

# Runs every day (no SCHEDULE attribute = daily).

MODEL = os.getenv("OLLAMA_MODEL", "phi4-mini:latest")

# Curated bank of real, well-known LeetCode problems (stable slugs), grouped by
# topic. Rather than having the model invent a new problem each day (which can't
# be reliably linked to a real LeetCode page or matched to a real explainer
# video), we rotate through this fixed list — the model explains/solves the
# REAL problem, and we attach real links programmatically (no hallucination risk
# on the URLs themselves).
#
# "Two Pointers & Sliding Window" has 4 entries instead of ~3 — known weak spot
# (missed a sliding window question in a real interview).
PROBLEM_BANK = [
    ("Arrays", "Two Sum", "two-sum"),
    ("Arrays", "Best Time to Buy and Sell Stock", "best-time-to-buy-and-sell-stock"),
    ("Arrays", "Maximum Subarray", "maximum-subarray"),
    ("Strings", "Valid Anagram", "valid-anagram"),
    ("Strings", "Longest Substring Without Repeating Characters", "longest-substring-without-repeating-characters"),
    ("Linked Lists", "Reverse Linked List", "reverse-linked-list"),
    ("Linked Lists", "Merge Two Sorted Lists", "merge-two-sorted-lists"),
    ("Linked Lists", "Linked List Cycle", "linked-list-cycle"),
    ("Stacks & Queues", "Valid Parentheses", "valid-parentheses"),
    ("Stacks & Queues", "Min Stack", "min-stack"),
    ("Trees & Binary Search Trees", "Binary Tree Inorder Traversal", "binary-tree-inorder-traversal"),
    ("Trees & Binary Search Trees", "Validate Binary Search Tree", "validate-binary-search-tree"),
    ("Trees & Binary Search Trees", "Maximum Depth of Binary Tree", "maximum-depth-of-binary-tree"),
    ("Graphs (BFS/DFS)", "Number of Islands", "number-of-islands"),
    ("Graphs (BFS/DFS)", "Course Schedule", "course-schedule"),
    ("Graphs (BFS/DFS)", "Clone Graph", "clone-graph"),
    ("Dynamic Programming", "Climbing Stairs", "climbing-stairs"),
    ("Dynamic Programming", "Coin Change", "coin-change"),
    ("Dynamic Programming", "Longest Common Subsequence", "longest-common-subsequence"),
    ("Recursion & Backtracking", "Subsets", "subsets"),
    ("Recursion & Backtracking", "Permutations", "permutations"),
    ("Recursion & Backtracking", "Combination Sum", "combination-sum"),
    ("Sorting & Searching", "Binary Search", "binary-search"),
    ("Sorting & Searching", "Search in Rotated Sorted Array", "search-in-rotated-sorted-array"),
    ("Sorting & Searching", "Kth Largest Element in an Array", "kth-largest-element-in-an-array"),
    ("Greedy Algorithms", "Jump Game", "jump-game"),
    ("Greedy Algorithms", "Gas Station", "gas-station"),
    ("Hashing", "Group Anagrams", "group-anagrams"),
    ("Hashing", "Contains Duplicate", "contains-duplicate"),
    ("Hashing", "Top K Frequent Elements", "top-k-frequent-elements"),
    ("Two Pointers & Sliding Window", "Container With Most Water", "container-with-most-water"),
    ("Two Pointers & Sliding Window", "3Sum", "3sum"),
    ("Two Pointers & Sliding Window", "Minimum Window Substring", "minimum-window-substring"),
    ("Two Pointers & Sliding Window", "Sliding Window Maximum", "sliding-window-maximum"),
]


def pick_problem():
    day_of_year = datetime.now().timetuple().tm_yday
    return PROBLEM_BANK[day_of_year % len(PROBLEM_BANK)]


def run():
    topic, title, slug = pick_problem()
    leetcode_url = f"https://leetcode.com/problems/{slug}/"
    # We can't reliably guess the exact NeetCode video ID without risking a wrong
    # or dead link, so this is a pre-filled YouTube search instead — one click
    # to the right video rather than a hallucinated direct URL.
    youtube_search_url = f"https://www.youtube.com/results?search_query={quote_plus('neetcode ' + title)}"

    agent = create_agent(
        model=ChatOllama(model=MODEL, temperature=0.4, num_ctx=4096),
        tools=[],
        system_prompt=(
            "You are an interview coach for a fresher preparing for SDE roles. "
            "You will be given the exact name of a real, well-known LeetCode problem. "
            "Produce Markdown with this exact structure:\n\n"
            "## Problem\n(restate the problem clearly and accurately, the way it's "
            "commonly phrased for this exact LeetCode problem)\n\n"
            "## Example\n(one input/output example matching this exact problem)\n\n"
            "## Hint 1\n(a nudge toward the approach, no code)\n\n"
            "## Hint 2\n(a stronger nudge, e.g. mention the technique/data structure, "
            "still no code)\n\n"
            "## Solution & Explanation\n(the full approach explained step by step, "
            "followed by a working Python code solution in a code block)\n\n"
            "## Time & Space Complexity\n(brief complexity analysis of the solution)\n\n"
            "Try to solve it yourself using only the hints first — the Solution section "
            "is there so you can check your answer afterward, not to read before attempting."
        ),
    )

    result = agent.invoke({
        "messages": [{"role": "user", "content": f"Problem: {title} (topic: {topic})"}]
    })

    content = result["messages"][-1].content

    _history.append(NAME, {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "topic": topic,
        "summary": title,
    })

    links_section = (
        f"\n## Practice Links\n"
        f"- [Solve it on LeetCode]({leetcode_url})\n"
        f"- [Search NeetCode's explanation video on YouTube]({youtube_search_url})\n"
    )

    return (
        f"# Daily DSA Problem — {title} ({topic})\n\n"
        f"{content}\n"
        f"{links_section}"
    )
