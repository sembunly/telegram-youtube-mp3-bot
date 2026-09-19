FROM denoland/deno:bin-2.9.7 AS deno
FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deno /deno /usr/local/bin/deno

WORKDIR /app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 bot \
    && mkdir -p /app/downloads \
    && chown bot:bot /app/downloads

COPY bot.py ./
USER bot

CMD ["python", "bot.py"]
