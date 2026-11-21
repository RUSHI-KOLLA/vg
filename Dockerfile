# ---- Build stage: install deps & pre-bake ChromaDB ----
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps for ChromaDB / fastembed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source into vg/ subdirectory to make it a proper package
COPY . vg/

# Pre-bake ChromaDB index (downloads embedding model ~130MB, builds vector DB)
# Run from /app so `vg` is importable as a package
RUN python -m vg.rag.builder

# ---- Runtime stage: minimal image ----
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code (vg package)
COPY --from=builder /app/vg ./vg

# Copy pre-built ChromaDB
COPY --from=builder /app/chroma_db ./chroma_db

# Non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Hugging Face Spaces / Koyeb expect port 7860
ENV PORT=7860
EXPOSE 7860

# Run the VG web server from /app (parent of vg package)
CMD ["python", "-m", "vg.main", "--web", "--host", "0.0.0.0", "--port", "7860"]