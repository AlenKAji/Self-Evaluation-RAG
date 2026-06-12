# ─────────────────────────────────────────────
# Stage 1: Builder – install heavy deps once
# ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps for FAISS, PyPDF2, sentence-transformers
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    git \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps into a prefix so we can copy them cleanly
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2: Runtime image
# ─────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="your-team@example.com"
LABEL description="Self-Evaluation RAG – Streamlit + FAISS + Ollama"

WORKDIR /app

# Minimal runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas0 \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY app.py build_index.py config.py evaluator.py generator.py retriever.py ./

# ── Persistent volume mount points ──────────────────────────────
# On ECS/EFS these paths get overridden by volume mounts.
# Locally, Docker named volumes or bind-mounts work the same way.
RUN mkdir -p /app/data /app/index /app/logs

# Non-root user for security
RUN useradd -m -u 1000 appuser \
 && chown -R appuser:appuser /app
USER appuser

# Remove the Windows-specific venv check in app.py at runtime
# (the container IS the environment; env name check is irrelevant)
ENV STREAMLIT_ENV_CHECK_DISABLED=1

# Streamlit config via env (no config.toml needed)
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Ollama sidecar address (override at deploy time)
ENV OLLAMA_HOST=http://ollama:11434

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
