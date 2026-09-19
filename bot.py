# Author: Sem Bunli
# Date: 19-09-2026
# Project: Telegram YouTube MP3 Bot

import os
import asyncio
import logging
import tempfile
from urllib.parse import urlsplit

import yt_dlp

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DOWNLOAD_DIR = "downloads"
logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu = [
        ["/start", "Download MP3"],
        ["Help", "About"],
    ]

    keyboard = ReplyKeyboardMarkup(
        menu,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )

    await update.message.reply_text(
        "Hello!\n"
        "Please choose an option below.\n\n"
        "👨‍💻 Developed by SEM Bunly",
        reply_markup=keyboard
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "Download MP3":
        context.user_data["mode"] = "mp3"

        await update.message.reply_text(
            "Send me a YouTube link to download as MP3."
        )

    elif text == "Help":
        await update.message.reply_text(
            "How to use this bot\n\n"
            "1. Choose Download MP3.\n"
            "2. Paste a YouTube link.\n"
            "3. Wait for the bot to send your MP3.\n\n"
            "Use /start to refresh the menu."
        )

    elif text == "About":
        await update.message.reply_text(
            "YouTube MP3 Downloader Bot\n"
            "Developed by SEM Bunly"
        )

    else:
        mode = context.user_data.get("mode")

        if mode == "mp3":
            await download_handler(update, context)
        else:
            await update.message.reply_text(
                "Please choose Download MP3 first. "
                "Use /start to show the menu."
            )


def download_mp3(url, output_dir, progress_callback=None):
    options = {
        "outtmpl": os.path.join(output_dir, "media.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }

    if progress_callback is not None:
        reported_stages = set()

        def report_once(text):
            if text not in reported_stages:
                reported_stages.add(text)
                progress_callback(text)

        def download_progress(event):
            if event.get("status") in ("downloading", "finished"):
                report_once("🎵 Downloading audio...")

        def conversion_progress(event):
            if (
                event.get("status") == "started"
                and event.get("postprocessor") == "ExtractAudio"
            ):
                report_once("🔄 Converting to MP3...")

        options["progress_hooks"] = [download_progress]
        options["postprocessor_hooks"] = [conversion_progress]

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)

    if not info:
        raise ValueError("No media information returned")

    return (
        os.path.join(output_dir, "media.mp3"),
        info.get("title") or "YouTube download"
    )


def is_youtube_url(url):
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    host = parsed.hostname or ""
    return (
        parsed.scheme in ("http", "https")
        and (host in ("youtube.com", "youtu.be") or host.endswith(".youtube.com"))
        and parsed.username is None
        and parsed.password is None
    )


async def download_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    url = update.message.text.strip()

    if not is_youtube_url(url):
        await update.message.reply_text(
            "Please send a valid YouTube link."
        )
        return

    message = await update.message.reply_text(
        "⏳ Preparing your download..."
    )

    async def edit_status(text):
        try:
            await message.edit_text(text)
        except TelegramError:
            # A status update failure should not interrupt the download or upload.
            logger.warning("Could not update the status message", exc_info=True)

    loop = asyncio.get_running_loop()
    progress_queue = asyncio.Queue()

    def report_progress(text):
        # yt-dlp runs in a worker thread; Telegram edits run on the event loop.
        loop.call_soon_threadsafe(progress_queue.put_nowait, text)

    async def update_progress():
        while True:
            text = await progress_queue.get()
            if text is None:
                return
            await edit_status(text)

    try:
        with tempfile.TemporaryDirectory(dir=DOWNLOAD_DIR) as output_dir:
            progress_task = asyncio.create_task(update_progress())
            try:
                file_path, title = await asyncio.to_thread(
                    download_mp3, url, output_dir, report_progress
                )
            finally:
                # Finish queued edits before showing the upload or error status.
                progress_queue.put_nowait(None)
                await progress_task

            if os.path.getsize(file_path) > 50_000_000:
                await edit_status(
                    "❌ This MP3 is too large to send.\n"
                    "Please try another YouTube link with a shorter video."
                )
                return

            await edit_status("📤 Uploading your MP3...")

            with open(file_path, "rb") as media:
                await update.message.reply_audio(
                    audio=media, title=title, write_timeout=120
                )

    except Exception:
        logger.exception("Failed to download or send media")
        await edit_status(
            "Sorry, your download or upload failed.\n\n"
            "Please try another YouTube link. Thanks for your patience!"
        )
        return

    await edit_status(
        "✅ Download completed successfully!\n\n"
        "🎧 Enjoy your music.\n"
        "🙏 Thanks for using my bot!\n\n"
        "If you like this bot, please share it with your friends ❤️\n\n"
        "👨‍💻 Developed by SEM Bunly"
    )


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN not found in .env")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            menu_handler
        )
    )

    print("Bot running...")

    app.run_polling()


if __name__ == "__main__":
    main()
