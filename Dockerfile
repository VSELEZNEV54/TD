FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    SITE_DIR=/app/site \
    BIND=0.0.0.0:8000

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 teacherdesk \
    && useradd --uid 10001 --gid teacherdesk --no-create-home teacherdesk \
    && mkdir /data \
    && chown teacherdesk:teacherdesk /data

COPY server/ ./server/
COPY site/ ./site/
COPY deploy/gunicorn.conf.py ./deploy/gunicorn.conf.py

USER teacherdesk
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["gunicorn", "--config", "deploy/gunicorn.conf.py", "server.app:application"]
