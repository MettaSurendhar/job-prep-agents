@echo off
REM All model/API-key settings now live in .env (copy .env.example to .env
REM and fill it in) -- this file only needs your project path below.

REM Edit this to the full path of your project folder
cd /d "D:\MettaProjects\job-prep-agents"

REM Edit this to the full path of your venv's python.exe
"D:\MettaProjects\job-prep-agents\.venv\Scripts\python.exe" scheduler.py >> runner.log 2>&1