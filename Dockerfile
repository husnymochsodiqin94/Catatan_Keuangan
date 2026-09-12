# AI Financial Assistant — image ramping, tanpa dependency pihak ketiga.
FROM python:3.11-slim

WORKDIR /app

# Kode aplikasi (tanpa docs/tests/DB — lihat .dockerignore).
COPY financial_engine ./financial_engine
COPY nlp ./nlp
COPY voice ./voice
COPY reporting ./reporting
COPY server ./server
COPY webapp ./webapp

ENV HOST=0.0.0.0 \
    PORT=8000 \
    CATATAN_DB=/data/data.db \
    PYTHONUNBUFFERED=1

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3).status==200 else 1)"

CMD ["python3", "-m", "server.app"]
