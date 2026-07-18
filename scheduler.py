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


def sanitize_markdown(content):
    """Small local models occasionally leave a code fence (```) unclosed or
    mismatched, which swallows the rest of the content into a broken code
    block or leaks a stray ``` as literal text. As a safety net, if the fence
    count is odd, append one more closing fence so the page never breaks —
    at worst you lose a little formatting on the last block, instead of the
    entire rest of the tab rendering wrong."""
    fence_count = content.count("```")
    if fence_count % 2 != 0:
        content = content + "\n```\n"
    return content


# ---------------------------------------------------------------------------
# HTML viewer — combines today's agent outputs into one browsable page with
# collapsible sections per agent, using plain <details>/<summary> (no JS
# needed). Also rebuilds an index.html linking every day generated so far.
# ---------------------------------------------------------------------------

PAGE_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --bg: #0d0e14;
  --bg-glow: radial-gradient(circle at 15% 0%, rgba(94,230,196,0.10), transparent 40%),
             radial-gradient(circle at 85% 10%, rgba(124,155,255,0.08), transparent 40%);
  --panel-bg: #161822;
  --panel-bg-hover: #1c1f2b;
  --border: #262a38;
  --text: #eef1f6;
  --muted: #949bab;
  --accent: #5ee6c4;
  --accent-soft: rgba(94,230,196,0.12);
  --accent-warm: #ffb86b;
  --code-bg: #0a0b10;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 16px 64px;
  background-color: var(--bg);
  background-image: var(--bg-glow);
  color: var(--text);
  font-family: 'Inter', -apple-system, "Segoe UI", Roboto, sans-serif;
  line-height: 1.65;
}
.wrap { max-width: 800px; margin: 0 auto; }
h1 {
  font-family: 'Sora', 'Inter', sans-serif;
  font-size: 1.7rem;
  margin-bottom: 4px;
  background: linear-gradient(90deg, #eef1f6, #b9c2d0);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.date { color: var(--muted); margin-bottom: 4px; font-size: 0.95rem; }
.progress-label { color: var(--muted); font-size: 0.85rem; margin-bottom: 20px; }

.voice-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
  font-size: 0.85rem;
  color: var(--muted);
}
.voice-row select {
  background: var(--panel-bg);
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85rem;
  max-width: 260px;
}

.tab-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.tab-btn {
  background: var(--panel-bg);
  color: var(--muted);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 9px 18px;
  font-family: 'Sora', sans-serif;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.18s ease;
}
.tab-btn:hover { color: var(--text); border-color: #3a4256; transform: translateY(-1px); }
.tab-btn.active {
  color: #0d0e14;
  background: var(--accent);
  border-color: var(--accent);
}

.tab-panel {
  display: none;
  background: var(--panel-bg);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 24px 26px;
  animation: fadeSlide 0.25s ease;
}
.tab-panel.active { display: block; }
@keyframes fadeSlide { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

.agent-content h1 {
  font-family: 'Sora', sans-serif; font-size: 1.2rem; color: var(--text);
  -webkit-background-clip: unset; background: none; margin-top: 0;
}
.agent-content h2 {
  font-family: 'Sora', sans-serif; font-size: 1.08rem; color: var(--accent);
  margin-top: 26px; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;
}
.agent-content h3 {
  font-family: 'Sora', sans-serif; font-size: 0.98rem; color: var(--text);
  margin-top: 18px; display: flex; align-items: center; gap: 8px;
}
.agent-content p, .agent-content li { color: #d4d9e2; }
.agent-content ul, .agent-content ol { padding-left: 22px; }
.agent-content code { background: var(--code-bg); padding: 2px 6px; border-radius: 4px; font-size: 0.88em; color: #ffcb8f; }
.agent-content pre {
  background: var(--code-bg); padding: 16px; border-radius: 10px; overflow-x: auto;
  position: relative; border: 1px solid var(--border); margin-top: 10px;
}
.agent-content pre code { background: none; padding: 0; color: #d4d9e2; }
.agent-content iframe { border-radius: 10px; margin-top: 10px; }
.agent-content a { color: var(--accent); }

.video-thumb-link {
  display: block;
  position: relative;
  margin-top: 10px;
  border-radius: 10px;
  overflow: hidden;
  max-width: 480px;
  text-decoration: none;
}
.video-thumb { width: 100%; display: block; }
.video-play-badge {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(13,14,20,0.85);
  color: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
}

.mermaid { background: var(--code-bg); border-radius: 10px; padding: 14px; margin-top: 10px; border: 1px solid var(--border); }
.mermaid-container { background: var(--code-bg); border-radius: 10px; padding: 14px; margin-top: 10px; border: 1px solid var(--border); overflow-x: auto; }
.mermaid-container svg { max-width: 100%; height: auto; }
.diagram-fallback {
  background: var(--code-bg);
  border: 1px dashed var(--border);
  border-radius: 10px;
  padding: 14px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 0.88rem;
  font-style: italic;
}

.answer-actions { margin: 10px 0 4px; display: flex; gap: 8px; }
.read-btn, .answer-copy-btn {
  background: var(--accent-soft);
  color: var(--accent);
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
}
.read-btn:hover, .answer-copy-btn:hover { background: rgba(94,230,196,0.22); }

.code-copy-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: var(--border);
  color: var(--text);
  border: none;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.72rem;
  cursor: pointer;
}
.code-copy-btn:hover { background: #3a4256; }

a { color: var(--accent); }
.back-link { display: inline-block; margin-bottom: 20px; color: var(--muted); text-decoration: none; font-size: 0.9rem; }
.back-link:hover { color: var(--accent); }
"""

VIEWER_SCRIPT = """
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
function showTab(id) {
  document.querySelectorAll('.tab-panel').forEach(function(p) { p.classList.remove('active'); });
  document.querySelectorAll('.tab-btn').forEach(function(b) { b.classList.remove('active'); });
  document.getElementById(id).classList.add('active');
  document.getElementById('btn-' + id).classList.add('active');
}

// Prefix known section headings with a matching icon, for visual variety
// without needing external images.
var HEADING_ICONS = [
  ['sample answer', '\\uD83D\\uDDE3\\uFE0F'],
  ['approach 1', '\\uD83D\\uDC22'],
  ['approach 2', '\\u26A1'],
  ['approach 3', '\\uD83C\\uDFC6'],
  ['solutions', '\\u2699\\uFE0F'],
  ['diagram', '\\uD83D\\uDCCA'],
  ['practice links', '\\uD83D\\uDD17'],
  ['problem', '\\uD83E\\uDDE9'],
  ['example', '\\uD83D\\uDCDD'],
  ['hint', '\\uD83D\\uDCA1'],
  ['time & space complexity', '\\u23F1\\uFE0F'],
  ['concept', '\\uD83E\\uDDE0'],
  ['explanation', '\\uD83D\\uDCD6'],
  ['likely interview question', '\\u2753'],
  ['how to answer', '\\uD83D\\uDDD2\\uFE0F'],
  ['how to approach it', '\\uD83D\\uDDD2\\uFE0F'],
  ['further reading', '\\uD83D\\uDCDA'],
  ['technical question', '\\uD83D\\uDCBB'],
  ['behavioral question', '\\uD83E\\uDD1D'],
  ['star approach', '\\u2B50'],
];
function initIcons() {
  var headings = document.querySelectorAll('.agent-content h1, .agent-content h2, .agent-content h3');
  headings.forEach(function(h) {
    var t = h.textContent.toLowerCase();
    for (var i = 0; i < HEADING_ICONS.length; i++) {
      if (t.indexOf(HEADING_ICONS[i][0]) !== -1) {
        h.innerHTML = HEADING_ICONS[i][1] + ' ' + h.innerHTML;
        break;
      }
    }
  });
}

// Render any ```mermaid fenced blocks as real diagrams. Validates syntax first
// so an invalid diagram shows a clean fallback message instead of Mermaid's
// own "bomb icon" error UI.
async function initMermaid() {
  if (typeof mermaid === 'undefined') return;
  mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

  var blocks = document.querySelectorAll('code.language-mermaid');
  var diagramIndex = 0;

  for (var i = 0; i < blocks.length; i++) {
    var code = blocks[i];
    var pre = code.parentElement;
    var source = code.textContent;
    var container = document.createElement('div');

    try {
      var isValid = await mermaid.parse(source, { suppressErrors: true });
      if (isValid) {
        var id = 'mermaid-diagram-' + (diagramIndex++);
        var rendered = await mermaid.render(id, source);
        container.className = 'mermaid-container';
        container.innerHTML = rendered.svg;
      } else {
        container.className = 'diagram-fallback';
        container.textContent = 'Diagram unavailable this time (invalid diagram syntax) — see the written explanation above instead.';
      }
    } catch (e) {
      container.className = 'diagram-fallback';
      container.textContent = 'Diagram unavailable this time — see the written explanation above instead.';
    }

    pre.parentElement.replaceChild(container, pre);
  }
}

// Copy button on every remaining code block (skips mermaid, which was
// converted to a diagram above).
function initCodeCopyButtons() {
  document.querySelectorAll('.agent-content pre').forEach(function(pre) {
    var btn = document.createElement('button');
    btn.className = 'code-copy-btn';
    btn.innerText = 'Copy';
    btn.onclick = function() {
      navigator.clipboard.writeText(pre.innerText.replace(/Copy$/, '').trim());
      btn.innerText = 'Copied!';
      setTimeout(function() { btn.innerText = 'Copy'; }, 1200);
    };
    pre.appendChild(btn);
  });
}

// Voice picker for read-aloud.
var availableVoices = [];
var selectedVoiceURI = null;
function populateVoices() {
  if (!window.speechSynthesis) return;
  availableVoices = window.speechSynthesis.getVoices();
  var select = document.getElementById('voice-select');
  if (!select || !availableVoices.length) return;
  select.innerHTML = '';
  availableVoices.forEach(function(v) {
    var opt = document.createElement('option');
    opt.value = v.voiceURI;
    opt.innerText = v.name + ' (' + v.lang + ')';
    select.appendChild(opt);
  });
  var preferred = availableVoices.find(function(v) { return /natural|neural|online/i.test(v.name); });
  var chosen = preferred || availableVoices[0];
  select.value = chosen.voiceURI;
  selectedVoiceURI = chosen.voiceURI;
}
document.addEventListener('DOMContentLoaded', function() {
  var select = document.getElementById('voice-select');
  if (select) {
    select.addEventListener('change', function(e) { selectedVoiceURI = e.target.value; });
  }
  if (window.speechSynthesis) {
    populateVoices();
    window.speechSynthesis.onvoiceschanged = populateVoices;
  }
});

// Read-aloud + copy, attached only under "Sample Answer" headings.
function initSampleAnswerActions() {
  var headings = document.querySelectorAll('.agent-content h1, .agent-content h2, .agent-content h3');
  headings.forEach(function(h) {
    if (!/sample answer/i.test(h.textContent)) return;

    var text = '';
    var node = h.nextElementSibling;
    while (node && !/^H[1-3]$/.test(node.tagName)) {
      text += node.innerText + ' ';
      node = node.nextElementSibling;
    }

    var row = document.createElement('div');
    row.className = 'answer-actions';

    var readBtn = document.createElement('button');
    readBtn.className = 'read-btn';
    readBtn.innerText = '\\uD83D\\uDD0A Read aloud';
    readBtn.dataset.speaking = 'false';
    readBtn.addEventListener('click', function() {
      if (!window.speechSynthesis) {
        alert('Speech synthesis is not supported in this browser.');
        return;
      }
      if (readBtn.dataset.speaking === 'true') {
        window.speechSynthesis.cancel();
        readBtn.innerText = '\\uD83D\\uDD0A Read aloud';
        readBtn.dataset.speaking = 'false';
        return;
      }
      window.speechSynthesis.cancel();
      var utter = new SpeechSynthesisUtterance(text);
      utter.rate = 0.95;
      var voice = availableVoices.find(function(v) { return v.voiceURI === selectedVoiceURI; });
      if (voice) utter.voice = voice;
      utter.onend = function() {
        readBtn.innerText = '\\uD83D\\uDD0A Read aloud';
        readBtn.dataset.speaking = 'false';
      };
      window.speechSynthesis.speak(utter);
      readBtn.innerText = '\\u23F9 Stop';
      readBtn.dataset.speaking = 'true';
    });

    var copyBtn = document.createElement('button');
    copyBtn.className = 'answer-copy-btn';
    copyBtn.innerText = '\\uD83D\\uDCCB Copy';
    copyBtn.addEventListener('click', function() {
      navigator.clipboard.writeText(text.trim());
      copyBtn.innerText = 'Copied!';
      setTimeout(function() { copyBtn.innerText = '\\uD83D\\uDCCB Copy'; }, 1200);
    });

    row.appendChild(readBtn);
    row.appendChild(copyBtn);
    h.parentNode.insertBefore(row, h.nextSibling);
  });
}

document.addEventListener('DOMContentLoaded', async function() {
  initIcons();
  await initMermaid();
  initCodeCopyButtons();
  initSampleAnswerActions();
});
</script>
"""


TAB_ICONS = {
    "dsa-problem": "\U0001F9E9",
    "cs-fundamentals": "\U0001F9E0",
    "interview-qa": "\U0001F3A4",
    "job-digest": "\U0001F4BC",
}


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
        html_body = md_lib.markdown(sanitize_markdown(content), extensions=["fenced_code", "tables"])
        pretty_name = name.replace("-", " ").title()
        icon = TAB_ICONS.get(name, "\U0001F4C4")
        panel_id = f"panel-{i}"
        is_first = i == 0

        tab_buttons.append(
            f'<button class="tab-btn{" active" if is_first else ""}" '
            f'id="btn-{panel_id}" onclick="showTab(\'{panel_id}\')">'
            f'{icon} {pretty_name}</button>'
        )
        tab_panels.append(
            f'<div class="tab-panel{" active" if is_first else ""}" id="{panel_id}">'
            f'<div class="agent-content">{html_body}</div>'
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
  <div class="voice-row">
    \U0001F3A7 Read-aloud voice:
    <select id="voice-select"><option>Loading voices...</option></select>
  </div>
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