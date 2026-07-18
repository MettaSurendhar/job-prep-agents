import json
from pathlib import Path

HISTORY_DIR = Path("history")


def load_recent(agent_name, limit=12):
    """Return the most recent `limit` history entries for an agent, oldest first."""
    HISTORY_DIR.mkdir(exist_ok=True)
    path = HISTORY_DIR / f"{agent_name}.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data[-limit:]


def append(agent_name, entry):
    """Append one entry (a dict) to an agent's history log, capped at 200 entries."""
    HISTORY_DIR.mkdir(exist_ok=True)
    path = HISTORY_DIR / f"{agent_name}.json"
    data = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = []
    data.append(entry)
    data = data[-200:]  # keep the log from growing forever
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def format_for_prompt(entries, topic_key="topic"):
    """Turn history entries into a short bullet list for the prompt, grouped loosely."""
    if not entries:
        return "(none yet — this is the first time)"
    lines = []
    for e in entries:
        lines.append(f"- [{e.get(topic_key, '?')}] {e.get('summary', '')}")
    return "\n".join(lines)
