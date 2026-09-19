# Telegram YouTube MP3 Bot

## Run with Docker

Install Docker with Docker Compose on your server. The image includes Python,
FFmpeg (including ffprobe), and Deno. The `yt-dlp[default]` dependency includes
the JavaScript support used for YouTube extraction; see the
[yt-dlp EJS documentation](https://github.com/yt-dlp/yt-dlp/wiki/EJS).

1. Create a `.env` file next to `compose.yaml`:

   ```dotenv
   BOT_TOKEN=your_telegram_bot_token
   ```

2. Stop any other running copy of this bot using the same token, then build and
   start one instance:

   ```sh
   docker compose up -d --build
   ```

3. View logs and send `/start` to the bot in Telegram:

   ```sh
   docker compose logs -f bot
   ```

The bot uses polling, so no incoming port or public URL is required. It needs
outbound internet access to Telegram and YouTube. Compose passes `BOT_TOKEN`
from `.env` into the container; the `.env` file is excluded from the image.
Downloads are temporary files stored inside the container and cleaned up by
the bot. The container runs as an unprivileged user and restarts automatically
unless stopped manually.

## Check installed tools

```sh
docker compose run --rm --no-deps bot ffmpeg -version
docker compose run --rm --no-deps bot ffprobe -version
docker compose run --rm --no-deps bot deno --version
```

## Update or stop

Rebuild with current dependencies and restart:

```sh
docker compose build --pull --no-cache
docker compose up -d
```

Stop the bot:

```sh
docker compose down
```
