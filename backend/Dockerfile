# IncidentMind API container.
#
# Deployment-only artefact. The application code is unchanged: this file only
# decides how the existing FastAPI app is packaged and started.
#
# The app reads PORT from the environment (app/config.py), so the platform's
# assigned port is honoured without any code change.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# Dependencies first so the layer is reused while application code changes.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# `app` holds the FastAPI application. `seed` is imported by the startup
# lifespan on an empty database, so it has to ship inside the image.
COPY app ./app
COPY seed ./seed

# SQLite lives on a mounted volume, not in the image layer.
RUN mkdir -p /data

EXPOSE 8080

# Host must be 0.0.0.0 to be reachable from outside the container.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
