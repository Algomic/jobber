import sqlite3
import logging
from os import getenv
from aiogram import Bot
from aiogram import Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
import asyncio


# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("JOBBAH_BOT_TOKEN")
bot = Bot(token=TOKEN)

dp = Dispatcher()
router = Router()

conn = sqlite3.connect("subscribers.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscribers (
    chat_id INTEGER PRIMARY KEY
)
""")
conn.commit()

# In-memory cache of subscriber chat_ids
subscriber_cache = set()

def load_subscribers_cache():
    cursor.execute("SELECT chat_id FROM subscribers")
    rows = cursor.fetchall()
    global subscriber_cache
    subscriber_cache = set(row[0] for row in rows)
    logging.info(f"Subscriber cache loaded: {len(subscriber_cache)} users")

def add_subscriber(chat_id: int):
    try:
        cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        subscriber_cache.add(chat_id)
        logging.info(f"Added subscriber: {chat_id}")
    except Exception as e:
        logging.error(f"Failed to add subscriber {chat_id}: {e}")


def remove_subscriber(chat_id: int):
    try:
        cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        subscriber_cache.discard(chat_id)
        logging.info(f"Removed subscriber: {chat_id}")
    except Exception as e:
        logging.error(f"Failed to remove subscriber {chat_id}: {e}")


async def periodic_cache_refresh(interval_minutes=10):
    while True:
        try:
            load_subscribers_cache()
            logging.info("Subscriber cache refreshed")
        except Exception as e:
            logging.error(f"Failed to refresh subscriber cache: {e}")
        await asyncio.sleep(interval_minutes * 60)

# @router.message(commands=["start"])
@router.message(Command(commands=["start"]))
async def start_handler(message: Message):
    add_subscriber(message.chat.id)
    await message.answer(
        "Welcome! You have been subscribed to trade signals.\n"
        "You will receive trade signals updates automatically."
    )


@router.message(Command(commands=["stop"]))
async def stop_handler(message: Message):
    remove_subscriber(message.chat.id)
    await message.answer(
        "You have been unsubscribed from trade signals. "
        "Send /start anytime to subscribe again."
    )

# /report command to be fully implemented soon.
@router.message(Command(commands=["report"]))
async def report_handler(message: Message):
    # Placeholder: you can extend this later with actual report logic
    await message.answer("📊 Report functionality coming soon. Stay tuned!")


dp.include_router(router)

# Load cache at import (or call explicitly on bot startup)
load_subscribers_cache()


async def jobber_telegram_bot():
    # from bot_instance import bot
    await dp.start_polling(bot)