# syntax=docker/dockerfile:1.7

# ── Builder ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# System deps for chromadb / lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --upgrade pip && pip install -r requirements/all.txt


# ── Runtime ─────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project source
COPY chatbot/ chatbot/
COPY scripts/ scripts/
COPY config/ config/
COPY data/ data/

# Create non-root user and pre-create runtime directories owned by it
RUN groupadd -r chatbot && useradd -r -g chatbot chatbot \
    && mkdir -p .vectorstore .sessions logs \
    && chown -R chatbot:chatbot /app

USER chatbot

EXPOSE 8000

# Defaults — override at runtime: `docker run -e ACTIVE_CLIENT=limmes ...`
ENV API_HOST=0.0.0.0 \
    API_PORT=8000 \
    LOG_LEVEL=INFO

CMD ["python", "-m", "scripts.serve"]
