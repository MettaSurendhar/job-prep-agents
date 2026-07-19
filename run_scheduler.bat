@echo off
REM Edit the path below to your Ollama API key (only needed for job-digest agent)
set OLLAMA_API_KEY=e73d315a4c714ee18cb6a80084104888.d4bJIba_4lOL8bJZ3gmpyhjf

REM Set this to whichever model you pulled (recommended for 4GB VRAM: phi4-mini)
set OLLAMA_MODEL=phi4-mini:latest

REM Optional: add your YouTube Data API key for embedded videos in DSA
REM problems (see README step 3b). Uncomment and fill in to enable; leave
REM commented out to just get a search link instead.
set YOUTUBE_API_KEY=AIzaSyDK-mkOhZGSwkaBIY1YfofpyWTabIbNeSI

REM Keep the model loaded in memory for 30 min after last use, instead of the
REM default 5 min, so back-to-back agent calls (and manual reruns) stay fast.
set OLLAMA_KEEP_ALIVE=30m

REM Edit this to the full path of your project folder
cd /d "D:\MettaProjects\job-prep-agents"
REM Edit this to the full path of your venv's python.exe
"D:\MettaProjects\job-prep-agents\.venv\Scripts\python.exe" scheduler.py >> runner.log 2>&1