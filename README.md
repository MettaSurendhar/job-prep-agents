# Job Prep Agents

A small local, scheduled AI assistant setup for daily job-search prep. Runs entirely
on your machine via Ollama — no per-call API costs, nothing sent to third parties
(except the job-digest agent, which needs Ollama's hosted web search).

## What's inside

```
job-prep-agents/
├── scheduler.py          # loads every agent, runs the ones scheduled for today, saves output
├── run_scheduler.bat      # wrapper script for Windows Task Scheduler
├── outputs/               # timestamped markdown results land here
├── history/               # auto-created: tracks past topics/questions per agent, so
│                          # dsa_problem, cs_fundamentals, and interview_qa avoid repeats
└── agents/
    ├── _history.py        # shared helper: load/save each agent's covered-topics log
    ├── dsa_problem.py     # daily DSA problem + progressive hints (no full solution)
    ├── cs_fundamentals.py # daily bite-sized OS/DBMS/CN/OOP/System Design concept
    ├── interview_qa.py    # daily tailored technical + behavioral interview Q&A
    └── job_digest.py      # Mon & Thu: fresh SDE/full-stack/AI-RAG job postings
```

Each agent is a Python file with a `NAME` and a `run()` function that returns
Markdown text. `scheduler.py` doesn't know what any agent does — it just imports
everything in `agents/`, runs what's scheduled for today, and writes the result
to `outputs/`. Add a new agent file and it's automatically picked up.

### The "calendar"

Instead of setting up 4 separate Windows scheduled tasks, each agent can declare
which weekdays it runs via a `SCHEDULE` set (0=Monday ... 6=Sunday):

- `dsa_problem`, `cs_fundamentals`, `interview_qa` — no `SCHEDULE` set → run every day
- `job_digest` — `SCHEDULE = {0, 3}` → runs only Monday and Thursday

You only need **one** Task Scheduler entry (see below); the scheduler figures out
which agents to actually run each day.

## Setup (Windows)

### 1. Pull the model (you already have Ollama installed)

With only 4GB of VRAM, skip `qwen3.5:4b` — at Q4 quantization it's right at the edge
of what 4GB can hold fully on-GPU once you add context overhead, so it'll likely spill
into slow CPU/RAM inference. Better options for 4GB VRAM:

```powershell
# Recommended: best quality-for-size at this VRAM tier
ollama pull phi4-mini

# Solid alternative, slightly lighter
ollama pull qwen2.5:3b

# Fastest / lightest fallback if the above still feels slow
ollama pull gemma2:2b
```

Since these agents run in the background (not an interactive chat), a slightly slower
but higher-quality model like `phi4-mini` is a good default — you're not waiting on it live.
Set `OLLAMA_MODEL` (see step 3) to whichever tag you pull, e.g.:

```powershell
$env:OLLAMA_MODEL = "phi4-mini"
```

If you upgrade your GPU or want to test a bigger model later, re-check current sizes
with `ollama list` / the Ollama library, since exact VRAM needs shift as models update.

### 2. Create a virtual environment and install dependencies

```powershell
cd C:\full\path\to\job-prep-agents
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. (Optional) Set your Ollama API key for the job-digest agent

The `job_digest` agent uses Ollama's hosted web search API to find fresh job
postings, which needs an API key from your Ollama account
(https://docs.ollama.com/api/authentication#api-keys):

```powershell
$env:OLLAMA_API_KEY = "paste-key-here"
```

The other three agents (`dsa_problem`, `cs_fundamentals`, `interview_qa`) don't
need this — they only talk to your local model.

### 4. Test it manually

```powershell
python scheduler.py
```

Check the `outputs/` folder — you should see new `.md` files for whichever
agents are scheduled today.

### 5. Edit `run_scheduler.bat`

Open `run_scheduler.bat` and update:
- `OLLAMA_API_KEY` (or remove that line if you're not using job_digest)
- The `cd` path to your actual project folder
- The path to `venv\Scripts\python.exe`

Test it by double-clicking `run_scheduler.bat` — check `runner.log` for output.

### 6. Schedule it with Windows Task Scheduler

From PowerShell:

```powershell
schtasks /Create /SC DAILY /TN "Job Prep Agents" /TR "C:\full\path\to\job-prep-agents\run_scheduler.bat" /ST 10:30
```

This runs every day at 10:30 AM — comfortably after you're awake, so everything is ready
and waiting by the time you check it. Because of each agent's `SCHEDULE`, you'll get
DSA + CS fundamentals + interview Q&A every day, and the job digest added in on
Mondays and Thursdays. Feel free to nudge the time further (e.g. `/ST 11:00`) if you
want more buffer.

To verify/edit later, open **Task Scheduler** (search it in the Start menu) →
find "Job Prep Agents" under Task Scheduler Library.

### How you're notified

After all of today's agents finish, `scheduler.py` automatically:
1. Builds `outputs/viewer-YYYY-MM-DD.html` — a tabbed page (one tab per agent,
   click to switch — no scrolling through everything at once), showing the fully
   rendered question, hints, and sample answers.
2. Rebuilds `outputs/index.html`, linking every day's viewer page so you can browse
   past days too.
3. Pops up a native Windows notification window with a working minimize button
   ("Your daily job prep is ready!") — it'll sit there waiting even if you're away.
4. Opens the viewer page automatically in your default browser.

So the flow each morning is: browser opens with today's tabs → popup confirms it's
ready (minimize it if you're not ready to look yet) → click through the tabs.

### What's in each tab

- **DSA Problem**: picked from a curated bank of real, well-known LeetCode problems
  (not AI-invented) — so every problem links to the actual LeetCode page, plus a
  pre-filled YouTube search for "neetcode + problem name" (one click to the right
  explainer video, since guessing an exact video URL risks a dead/wrong link).
- **CS Fundamentals**: ends with a "Further Reading" section — real links fetched
  live via DuckDuckGo at generation time. If the live search comes up empty (no
  internet, or DuckDuckGo changes its page layout), it falls back to a plain
  Google search link for the concept, so you're never left with nothing.
- **Interview Prep**: every "Sample Answer" section gets a "🔊 Read aloud" button —
  uses your browser's built-in text-to-speech (no installs, works offline) so you
  can hear the answer delivered aloud and practice your own delivery against it.
  Click again (now "⏹ Stop") to stop mid-read.

### Avoiding repeated questions

Each agent that generates questions (`dsa_problem`, `cs_fundamentals`, `interview_qa`)
logs a short summary of what it generated (problem title, concept name, or technical
question) into `history/<agent-name>.json` after every run. Next time that same topic
or focus area comes up in the rotation, the agent tells the model what's already been
covered and asks for something genuinely different — so you shouldn't see exact repeats
build up over weeks of daily runs. You can open the `history/*.json` files anytime to
see everything that's been covered so far, or delete a file to reset that agent's memory.

### A note on VRAM and context window

Ollama's default context window for some models (e.g. `phi4-mini`) is very large,
which can force it to allocate far more memory than the model's file size suggests —
sometimes overflowing a 4GB GPU into slow CPU inference even though the model itself
would easily fit. All four agents explicitly cap this via `num_ctx=4096` in the
`ChatOllama(...)` call, which keeps memory use predictable and keeps the model running
on GPU. If you switch models and see things get slow again, check `ollama ps` — if the
`PROCESSOR` column isn't close to 100% GPU, the context window (or model size) is too
big for your VRAM.

## Personalizing further

- **`interview_qa.py`**: `CANDIDATE_PROFILE` is a short summary of your resume —
  update it as your experience grows.
- **`job_digest.py`**: `SEARCH_QUERIES` — tune these to your target roles/locations.
- **`dsa_problem.py` / `cs_fundamentals.py`**: `TOPICS` — reorder, add, or remove
  topics to change what gets covered and when.
- Want a different frequency for job_digest? Just change the `SCHEDULE` set
  (e.g. `{0, 2, 4}` for Mon/Wed/Fri).

## A note on trust

Before trusting the results, spot-check them — small local models still
hallucinate, especially on things like specific problem statements or job
postings. Treat this as a study nudge and starting point, not gospel.
