@echo off
REM ============================================================
REM  Limmes Chatbot - one-click launcher (Windows)
REM
REM  Double-click this file, or run from a terminal:
REM
REM    run.bat              -> CLI chat (default)
REM    run.bat chat         -> CLI chat
REM    run.bat serve        -> HTTP API + web widget on :8000
REM    run.bat ingest       -> Rebuild the vector store
REM    run.bat scrape       -> Scrape scrape_urls from active client
REM
REM  Pass extra args after the mode, e.g.:
REM    run.bat chat --client limmes
REM ============================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM ---- 1. Check Python ---------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo [error] Python is not on PATH.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ---- 2. Create venv if missing -----------------------------
if not exist ".venv\Scripts\activate.bat" (
    echo [setup] Creating virtual environment .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [error] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

REM ---- 3. Install base deps if missing -----------------------
python -c "import loguru, langchain, openai, chromadb" 1>nul 2>nul
if errorlevel 1 (
    echo [setup] Installing base requirements ^(first run only^) ...
    python -m pip install --upgrade pip
    python -m pip install -r requirements\base.txt
    if errorlevel 1 (
        echo [error] Failed to install base requirements.
        pause
        exit /b 1
    )
)

REM ---- 4. Pick mode ------------------------------------------
set "MODE=%~1"
if "%MODE%"=="" set "MODE=chat"

REM Strip the mode token from the args, keep the rest
shift
set "REST=%1 %2 %3 %4 %5 %6 %7 %8 %9"

REM ---- 5. Mode dispatcher ------------------------------------
if /i "%MODE%"=="serve" (
    python -c "import fastapi, uvicorn" 1>nul 2>nul
    if errorlevel 1 (
        echo [setup] Installing API requirements ...
        python -m pip install -r requirements\api.txt
        if errorlevel 1 (
            echo [error] Failed to install API requirements.
            pause
            exit /b 1
        )
    )
    echo [run] Starting HTTP server on http://localhost:8000
    python -m scripts.serve %REST%
    pause
    exit /b %errorlevel%
)

if /i "%MODE%"=="ingest" (
    echo [run] Rebuilding vector store ...
    python -m scripts.ingest %REST%
    pause
    exit /b %errorlevel%
)

if /i "%MODE%"=="scrape" (
    python -c "import bs4" 1>nul 2>nul
    if errorlevel 1 (
        echo [setup] Installing extras ^(beautifulsoup4, ...^) ...
        python -m pip install -r requirements\extras.txt
    )
    echo [run] Scraping ...
    python -m scripts.scrape %REST%
    pause
    exit /b %errorlevel%
)

if /i "%MODE%"=="chat" goto :run_chat
if /i "%MODE%"=="cli"  goto :run_chat

echo [error] Unknown mode: %MODE%
echo         Use one of: chat ^| serve ^| ingest ^| scrape
pause
exit /b 1

:run_chat
REM Auto-build the vector store on first run.
if not exist ".vectorstore" (
    echo [setup] Building vector store from data\ ^(first run only^) ...
    python -m scripts.ingest %REST%
)
echo [run] Starting CLI chat. Type 'quit' to exit.
python -m scripts.chat %REST%
pause
exit /b %errorlevel%
