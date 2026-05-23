# ── Build stage ───────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /install
# Copy only requirements first (layer cache)
COPY payment-service/requirements.txt .
RUN pip install --prefix=/install/deps --no-cache-dir -r requirements.txt

# ── Runtime stage ─────────────────────────────────────────────
FROM python:3.11-slim
LABEL service="payment-service"

# Non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install/deps /usr/local

# Copy shared utilities (available because context = ./backend)
COPY shared/ /app/shared/

# Copy this service's source code
COPY payment-service/ /app/

ENV PYTHONPATH="/app:/app/shared"
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3   CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/health')" || exit 1

CMD ["python", "app.py"]
