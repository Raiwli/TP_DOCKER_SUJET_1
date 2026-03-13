FROM python:3.12-slim

LABEL maintainer="ecommerce-team"
LABEL version="1.0"

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5002

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5002/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5002", "--workers", "2", "app:app"]
