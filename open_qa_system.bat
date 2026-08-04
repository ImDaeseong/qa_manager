@echo off
rem Regenerate every project page plus the system index, then open the index.
cd /d "%~dp0"

python scripts\generate_system_index.py
if errorlevel 1 (
    echo [WARN] the qa_manager verification system reported at least one FAILing item - opening it anyway.
)

start "" "%~dp0index.html"
