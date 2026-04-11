#!/usr/bin/env bash
# ============================================================
#  Limmes Chatbot - one-click launcher (macOS / Linux / Git Bash)
#
#  Usage:
#    ./run.sh             -> CLI chat (default)
#    ./run.sh chat        -> CLI chat
#    ./run.sh serve       -> HTTP API + web widget on :8000
#    ./run.sh ingest      -> Rebuild the vector store
#    ./run.sh scrape      -> Scrape scrape_urls from active client
#
#  Pass extra args after the mode, e.g.:
#    ./run.sh chat --client limmes
# ============================================================
set -euo pipefail

cd "$(dirname "$0")"

# ---- 1. Locate Python ---------------------------------------
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
    if   command -v python3 >/dev/null 2>&1; then PY=python3
    elif command -v python  >/dev/null 2>&1; then PY=python
    else
        echo "[error] Python not found. Install Python 3.10+." >&2
        exit 1
    fi
fi

# ---- 2. Create venv if missing ------------------------------
if [ ! -d ".venv" ]; then
    echo "[setup] Creating virtual environment .venv ..."
    "$PY" -m venv .venv
fi

# Pick the right activate path (Linux/macOS vs Git Bash on Windows)
if   [ -f ".venv/bin/activate" ];        then . .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ];    then . .venv/Scripts/activate
else
    echo "[error] Could not find venv activate script." >&2
    exit 1
fi

# ---- 3. Install base deps if missing ------------------------
if ! python -c "import loguru, langchain, openai, chromadb" 2>/dev/null; then
    echo "[setup] Installing base requirements (first run only) ..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements/base.txt
fi

# ---- 4. Pick mode -------------------------------------------
MODE="${1:-chat}"
shift || true

# ---- 6. Mode dispatcher -------------------------------------
case "$MODE" in
    serve)
        if ! python -c "import fastapi, uvicorn" 2>/dev/null; then
            echo "[setup] Installing API requirements ..."
            python -m pip install -r requirements/api.txt
        fi
        echo "[run] Starting HTTP server on http://localhost:8000"
        exec python -m scripts.serve "$@"
        ;;
    ingest)
        echo "[run] Rebuilding vector store ..."
        exec python -m scripts.ingest "$@"
        ;;
    scrape)
        if ! python -c "import bs4" 2>/dev/null; then
            echo "[setup] Installing extras (beautifulsoup4, ...) ..."
            python -m pip install -r requirements/extras.txt
        fi
        exec python -m scripts.scrape "$@"
        ;;
    chat|cli)
        if [ ! -d ".vectorstore" ]; then
            echo "[setup] Building vector store from data/ (first run only) ..."
            python -m scripts.ingest "$@" || true
        fi
        echo "[run] Starting CLI chat. Type 'quit' to exit."
        exec python -m scripts.chat "$@"
        ;;
    *)
        echo "[error] Unknown mode: $MODE" >&2
        echo "        Use one of: chat | serve | ingest | scrape" >&2
        exit 1
        ;;
esac
