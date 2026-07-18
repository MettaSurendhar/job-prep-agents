import importlib
import subprocess
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import markdown as md_lib

# Folder that contains all agent files.
AGENTS_DIR = Path("agents")

# Folder where the output files (markdown + HTML viewer) will be written.
OUTPUTS_DIR = Path("outputs")


def load_agents():
    """Import every valid agent module from the agents/ folder."""
    agents = []

    # Look through all Python files in agents/
    for path in sorted(AGENTS_DIR.glob("*.py")):
        # Skip private helper files like __init__.py and _history.py
        if path.name.startswith("_"):
            continue

        # Import the file as a Python module, e.g. agents.dsa_problem
        module = importlib.import_module(f"agents.{path.stem}")

        # Only keep modules that define NAME and run()
        if hasattr(module, "NAME") and hasattr(module, "run"):
            agents.append(module)
        else:
            print(f"[skip] {path.name} (missing NAME or run)")

    return agents


def is_scheduled_today(agent):
    """
    An agent can optionally define SCHEDULE = a set of weekday ints
    (0=Monday ... 6=Sunday). If SCHEDULE is not defined, the agent
    runs every day. If it IS defined, it only runs on those weekdays.
    """
    schedule = getattr(agent, "SCHEDULE", None)
    if schedule is None:
        return True
    return datetime.now().weekday() in schedule


# ---------------------------------------------------------------------------
# HTML viewer — combines today's agent outputs into one browsable page with
# collapsible sections per agent, using plain <details>/<summary> (no JS
# needed). Also rebuilds an index.html linking every day generated so far.
# ---------------------------------------------------------------------------

PAGE_STYLE = """
:root {
  --bg: #0f1115;
  --card-bg: #171a21;
  --card-bg-hover: #1c2029;
  --border: #262b36;
  --text: #e6e8eb;
  --muted: #8b93a1;
  --accent: #5eb3ff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 16px 64px;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.6;
}
.wrap { max-width: 780px; margin: 0 auto; }
h1 { font-size: 1.6rem; margin-bottom: 4px; }
.date { color: var(--muted); margin-bottom: 4px; font-size: 0.95rem; }
.progress-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tab-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
  overflow-x: auto;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}
.tab-btn {
  background: transparent;
  color: var(--muted);
  border: none;
  border-bottom: 2px solid transparent;
  padding: 10px 16px;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); }
.tab-meta { color: var(--muted); font-weight: 400; font-size: 0.78rem; margin-left: 6px; }

.tab-panel {
  display: none;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  animation: fadeIn 0.2s ease;
}
.tab-panel.active { display: block; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.agent-content h1 { font-size: 1.15rem; color: var(--accent); margin-top: 4px; }
.agent-content h2 { font-size: 1.15rem; color: var(--accent); margin-top: 20px; }
.agent-content h3 { font-size: 1rem; color: var(--text); margin-top: 16px; }
.agent-content code { background: #0d0f13; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; }
.agent-content pre { background: #0d0f13; padding: 14px; border-radius: 8px; overflow-x: auto; position: relative; }
.agent-content pre code { background: none; padding: 0; }

.copy-btn, .read-btn {
  background: var(--border);
  color: var(--text);
  border: none;
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 0.75rem;
  cursor: pointer;
  margin-top: 8px;
  margin-right: 6px;
}
.copy-btn:hover, .read-btn:hover { background: #35405a; }

a { color: var(--accent); }
.back-link { display: inline-block; margin-bottom: 20px; color: var(--muted); text-decoration: none; }
.back-link:hover { color: var(--accent); }
"""

VIEWER_SCRIPT = """
<script>
function showTab(id) {
  document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.getElementById(id).classList.add('active');
  document.getElementById('btn-' + id).classList.add('active');
}

function copyCard(btn, id) {
  var el = document.getElementById(id);
  var text = el.innerText;
  navigator.clipboard.writeText(text).then(function() {
    var original = btn.innerText;
    btn.innerText = 'Copied!';
    setTimeout(function() { btn.innerText = original; }, 1500);
  });
}

// Read-aloud: finds every heading whose text is "Sample Answer" inside agent
// content, and adds a Play/Stop button that reads the following text using the
// browser's built-in text-to-speech (no installs, works offline).
function initReadAloud() {
  var headings = document.querySelectorAll('.agent-content h1, .agent-content h2, .agent-content h3');
  headings.forEach(function(h) {
    if (!/sample answer/i.test(h.textContent)) return;

    var text = '';
    var node = h.nextElementSibling;
    while (node && !/^H[1-3]$/.test(node.tagName)) {
      text += node.innerText + ' ';
      node = node.nextElementSibling;
    }

    var btn = document.createElement('button');
    btn.className = 'read-btn';
    btn.innerText = '\\uD83D\\uDD0A Read aloud';
    btn.dataset.speaking = 'false';
    btn.addEventListener('click', function() {
      if (!window.speechSynthesis) {
        alert('Speech synthesis is not supported in this browser.');
        return;
      }
      if (btn.dataset.speaking === 'true') {
        window.speechSynthesis.cancel();
        btn.innerText = '\\uD83D\\uDD0A Read aloud';
        btn.dataset.speaking = 'false';
        return;
      }
      window.speechSynthesis.cancel();
      var utter = new SpeechSynthesisUtterance(text);
      utter.rate = 0.95;
      utter.onend = function() {
        btn.innerText = '\\uD83D\\uDD0A Read aloud';
        btn.dataset.speaking = 'false';
      };
      window.speechSynthesis.speak(utter);
      btn.innerText = '\\u23F9 Stop';
      btn.dataset.speaking = 'true';
    });
    h.parentNode.insertBefore(btn, h.nextSibling);
  });
}
document.addEventListener('DOMContentLoaded', initReadAloud);
</script>
"""


def build_daily_viewer(results):
    """Combine today's (agent_name, markdown_output, elapsed_seconds) results
    into one HTML page with a tab per agent. Returns the path to the generated
    file."""
    date_str = datetime.now().strftime("%Y-%m-%d")
    viewer_path = OUTPUTS_DIR / f"viewer-{date_str}.html"

    # Find the most recent existing day (if any) to link "Previous day" nav.
    existing_dates = sorted(
        f.stem.replace("viewer-", "")
        for f in OUTPUTS_DIR.glob("viewer-*.html")
        if f.stem.replace("viewer-", "") != date_str
    )
    prev_date = existing_dates[-1] if existing_dates else None

    tab_buttons = []
    tab_panels = []
    for i, (name, content, elapsed) in enumerate(results):
        html_body = md_lib.markdown(content, extensions=["fenced_code", "tables"])
        pretty_name = name.replace("-", " ").title()
        panel_id = f"panel-{i}"
        is_first = i == 0

        tab_buttons.append(
            f'<button class="tab-btn{" active" if is_first else ""}" '
            f'id="btn-{panel_id}" onclick="showTab(\'{panel_id}\')">'
            f'{pretty_name}<span class="tab-meta">{elapsed:.0f}s</span></button>'
        )
        tab_panels.append(
            f'<div class="tab-panel{" active" if is_first else ""}" id="{panel_id}">'
            f'<div class="agent-content">{html_body}</div>'
            f'<button class="copy-btn" onclick="copyCard(this, \'{panel_id}\')">Copy text</button>'
            f'</div>'
        )

    nav_links = '<a class="back-link" href="index.html">&larr; All days</a>'
    if prev_date:
        nav_links += f' &nbsp;·&nbsp; <a class="back-link" href="viewer-{prev_date}.html">&larr; Previous day ({prev_date})</a>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Job Prep — {date_str}</title>
<style>{PAGE_STYLE}</style>
</head>
<body>
<div class="wrap">
  {nav_links}
  <h1>Job Prep — Daily Digest</h1>
  <div class="date">{date_str}</div>
  <div class="progress-label">{len(results)} agent{'s' if len(results) != 1 else ''} completed today</div>
  <div class="tab-bar">
    {''.join(tab_buttons)}
  </div>
  {''.join(tab_panels)}
</div>
{VIEWER_SCRIPT}
</body>
</html>"""
    viewer_path.write_text(html, encoding="utf-8")
    return viewer_path


def build_index():
    """Rebuild an index.html linking to every daily viewer page generated so far."""
    viewer_files = sorted(OUTPUTS_DIR.glob("viewer-*.html"), reverse=True)
    links = "\n".join(
        f'<li><a href="{f.name}">{f.stem.replace("viewer-", "")}</a></li>'
        for f in viewer_files
    )
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Job Prep — All Days</title>
<style>{PAGE_STYLE}</style></head>
<body><div class="wrap"><h1>Job Prep — All Days</h1><ul>{links}</ul></div></body></html>"""
    (OUTPUTS_DIR / "index.html").write_text(html, encoding="utf-8")


def show_popup(message):
    """Show a custom Windows notification window (with a working minimize button,
    unlike a plain MessageBox) via notify.ps1. Blocks until dismissed/minimized-
    then-left-open, which is fine — it just waits patiently for you to see it."""
    script_path = Path(__file__).parent / "notify.ps1"
    try:
        subprocess.run(
            [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(script_path), "-Message", message,
            ],
            check=False,
        )
    except Exception as e:
        print(f"[warn] couldn't show popup notification: {e}")


def main():
    """Load all agents, run the ones scheduled for today, save their outputs,
    build an HTML viewer, and notify via a popup + auto-opened browser tab."""
    OUTPUTS_DIR.mkdir(exist_ok=True)

    results = []  # (agent_name, markdown_output, elapsed_seconds) for successful runs

    for agent in load_agents():
        if not is_scheduled_today(agent):
            print(f"[skip] {agent.NAME} (not scheduled today)")
            continue

        print(f"[run]  {agent.NAME} (this can take a few minutes on limited VRAM — please wait)")
        start = time.time()

        try:
            output = agent.run()
            elapsed = time.time() - start

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_path = OUTPUTS_DIR / f"{agent.NAME}-{timestamp}.md"
            out_path.write_text(output, encoding="utf-8")

            print(f"[ok]   {agent.NAME} -> {out_path} ({elapsed:.1f}s)")
            results.append((agent.NAME, output, elapsed))
        except Exception as e:
            elapsed = time.time() - start
            print(f"[fail] {agent.NAME} after {elapsed:.1f}s: {e}")

    if not results:
        print("[info] no agents produced output today.")
        return

    viewer_path = build_daily_viewer(results)
    build_index()
    print(f"[done] viewer -> {viewer_path}")

    agent_list = ", ".join(name.replace("-", " ").title() for name, _, _ in results)

    try:
        webbrowser.open(viewer_path.resolve().as_uri())
    except Exception as e:
        print(f"[warn] couldn't auto-open browser: {e}")

    show_popup(f"Your daily job prep is ready!\n\n{agent_list}\n\nCheck your browser tab.")


if __name__ == "__main__":
    main()
