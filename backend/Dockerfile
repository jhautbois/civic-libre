FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CIVIC_DATA_DIR=/data

# sqlite3 pour les sauvegardes sûres (.backup), curl pour le healthcheck.
RUN apt-get update \
    && apt-get install -y --no-install-recommends sqlite3 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

RUN useradd --system --uid 1000 civic \
    && mkdir -p /data \
    && chown civic:civic /data

USER civic
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "civic.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
