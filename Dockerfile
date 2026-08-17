# ---------- Stage 1: builder ----------
FROM python:3.12.7-slim AS builder

WORKDIR /build

# Install deps into a local dir so we can copy just this into the final image
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Stage 2: final (slim runtime) ----------
FROM python:3.12.7-slim

# Create non-root user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copy only installed packages from builder (no build tools/cache in final image)
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Ownership to non-root user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
