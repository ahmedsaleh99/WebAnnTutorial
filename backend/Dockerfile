FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir /data \
    && chown appuser:appuser /data

COPY --chown=appuser:appuser server.py ./server.py

USER appuser

EXPOSE 8000

CMD ["python", "server.py"]
