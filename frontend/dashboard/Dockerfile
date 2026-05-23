FROM python:3.11-slim AS builder
WORKDIR /install
COPY requirements.txt .
RUN pip install --prefix=/install/deps --no-cache-dir -r requirements.txt

FROM python:3.11-slim
LABEL service="dashboard"
RUN groupadd -r appgroup && useradd -r -g appgroup appuser
WORKDIR /app
COPY --from=builder /install/deps /usr/local
COPY . /app
ENV PYTHONPATH="/app"
ENV FLASK_ENV=production
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 5006
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5006/health')" || exit 1
CMD ["python", "app.py"]
