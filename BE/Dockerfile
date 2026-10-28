FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# GeoDjango needs GDAL/GEOS/PROJ; libgl/libglib for OpenCV (YOLO inference).
RUN apt-get update && apt-get install -y --no-install-recommends \
        binutils gdal-bin libproj-dev libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
# run as an unprivileged user: a bug in the app or a library must not hand out root in the container.
# media/staticfiles exist in the image owned by that user, so fresh volumes inherit the ownership.
RUN chmod +x /app/entrypoint.sh     && useradd --create-home --uid 1000 app     && mkdir -p /app/media /app/staticfiles     && chown -R app:app /app
USER app

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
# one worker process per CPU core (Python runs on one core per process): WEB_CONCURRENCY workers, read by uvicorn.
# Cache, rate limits and the WebSocket channel layer live in Redis, so the workers share them.
# No access log here: nginx writes it without query strings (WebSocket URLs carry the login token).
ENV WEB_CONCURRENCY=2
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--lifespan", "off", \
     "--no-access-log", "--no-server-header", "--timeout-graceful-shutdown", "20"]
