# import sqlite3
# import logging
# from os import getenv
# from aiogram import Bot
# from aiogram import Dispatcher, Router
# from aiogram.filters import Command
# from aiogram.types import Message
# import asyncio
# from datetime import datetime, timedelta, timezone
# from logger_setup import logger

# sent_signals = {}  # { signal_id: expiry_datetime }




# # Bot token can be obtained via https://t.me/BotFather
# TOKEN = getenv("JOBBAH_BOT_TOKEN")
# bot = Bot(token=TOKEN)

# dp = Dispatcher()
# router = Router()

# conn = sqlite3.connect("subscribers.db", check_same_thread=False)
# cursor = conn.cursor()
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS subscribers (
#     chat_id INTEGER PRIMARY KEY
# )
# """)
# conn.commit()

# # In-memory cache of subscriber chat_ids
# subscriber_cache = set()

# def load_subscribers_cache():
#     cursor.execute("SELECT chat_id FROM subscribers")
#     rows = cursor.fetchall()
#     global subscriber_cache
#     subscriber_cache = set(row[0] for row in rows)
#     logging.info(f"Subscriber cache loaded: {len(subscriber_cache)} users")

# def add_subscriber(chat_id: int):
#     try:
#         cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
#         conn.commit()
#         subscriber_cache.add(chat_id)
#         logging.info(f"Added subscriber: {chat_id}")
#     except Exception as e:
#         logging.error(f"Failed to add subscriber {chat_id}: {e}")


# def remove_subscriber(chat_id: int):
#     try:
#         cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
#         conn.commit()
#         subscriber_cache.discard(chat_id)
#         logging.info(f"Removed subscriber: {chat_id}")
#     except Exception as e:
#         logging.error(f"Failed to remove subscriber {chat_id}: {e}")


# def get_all_subscribers():
#     cursor.execute('SELECT chat_id FROM subscribers')
#     rows = cursor.fetchall()
#     return [row[0] for row in rows]


# async def periodic_cache_refresh(interval_minutes=10):
#     while True:
#         try:
#             load_subscribers_cache()
#             logging.info("Subscriber cache refreshed")
#         except Exception as e:
#             logging.error(f"Failed to refresh subscriber cache: {e}")
#         await asyncio.sleep(interval_minutes * 60)




# def format_signal_message(signal):
#     """
#     Formats a trade signal dict into a nice emoji-rich message string.

#     :param signal: dict with keys like 'Asset', 'Entry Price', 'Take Profit', 'Stop Loss', 'Trend', 'Date', etc.
#     :return: formatted string ready to send via Telegram
#     """

#     trend_emoji = {
#         "Buy": "🟢📈 Buy",
#         "Sell": "🔴📉 Sell",
#         "Neutral": "⚪🔍 Neutral"
#     }

#     asset = signal.get("Asset", "Unknown")
#     entry = signal.get("Entry Price", "N/A")
#     target = signal.get("Take Profit", "N/A")
#     stop = signal.get("Stop Loss", "N/A")
#     trend = signal.get("Trend", "Neutral")
#     date = signal.get("Date", "N/A")

#     message = (
#         f"🚀 **New Trade Alert!**\n\n"
#         f"📊 **Asset:** {asset}\n"
#         f"💰 **Entry Price:** {entry}\n"
#         f"🎯 **Target Price:** {target}\n"
#         f"🛡️ **Stop Loss:** {stop}\n\n"
#         f"📈 **Trend Bias:** {trend_emoji.get(trend, trend)}\n"
#         f"📅 **Date:** {date}\n"
#     )
#     return message



# def send_signal_to_subscribers(signal):

#     # Create a unique ID for this signal
#     signal_id = f"{signal.asset}_{signal.entry_price}_{signal.target_price}_{signal.stop_price}"

#     # Remove expired entries
#     # now = datetime.utcnow()
#     now = datetime.now(timezone.utc)
#     expired_keys = [k for k, v in sent_signals.items() if v < now]
#     for k in expired_keys:
#         del sent_signals[k]

#     # Check if this signal has already been sent
#     if signal_id in sent_signals:
#         logger.info(f"TELGRAM NOTIFICATION: Duplicate detected, skipping signal: {signal_id}")
#         return

#     # Format and send the message
#     message = format_signal_message(signal)
#     for subscriber_id in get_all_subscribers():
#         bot.send_message(subscriber_id, message)

#     # Mark signal as sent for the next hour
#     sent_signals[signal_id] = now + timedelta(hours=1)
#     logger.info(f"TELGRAM NOTIFICATION: Signal sent and stored: {signal_id}")




# # @router.message(commands=["start"])
# @router.message(Command(commands=["start"]))
# async def start_handler(message: Message):
#     add_subscriber(message.chat.id)
#     await message.answer(
#         "Welcome! You have been subscribed to trade signals.\n"
#         "You will receive trade signals updates automatically."
#     )


# @router.message(Command(commands=["stop"]))
# async def stop_handler(message: Message):
#     remove_subscriber(message.chat.id)
#     await message.answer(
#         "You have been unsubscribed from trade signals. "
#         "Send /start anytime to subscribe again."
#     )

# # /report command to be fully implemented soon.
# @router.message(Command(commands=["report"]))
# async def report_handler(message: Message):
#     # Placeholder: you can extend this later with actual report logic
#     await message.answer("📊 Report functionality coming soon. Stay tuned!")


# dp.include_router(router)

# # Load cache at import (or call explicitly on bot startup)
# load_subscribers_cache()


# async def jobber_telegram_bot():
#     # from bot_instance import bot
#     await dp.start_polling(bot)











































import sqlite3
import logging
from os import getenv
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime, timedelta, timezone
from logger_setup import logger
import asyncio

# ======================
# Global state variables
# ======================
sent_signals = {}  # { signal_id: expiry_datetime }
subscriber_cache = set()  # In-memory cache of subscribers

# ======================
# Bot instance
# ======================
TOKEN = getenv("JOBBAH_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

# ======================
# SQLite database setup
# ======================
conn = sqlite3.connect("subscribers.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS subscribers (
    chat_id INTEGER PRIMARY KEY
)
""")
conn.commit()


# ======================
# Subscriber cache functions
# ======================
def load_subscribers_cache():
    cursor.execute("SELECT chat_id FROM subscribers")
    rows = cursor.fetchall()
    global subscriber_cache
    subscriber_cache = set(row[0] for row in rows)
    logger.info(f"Subscriber cache loaded: {len(subscriber_cache)} users")


def add_subscriber(chat_id: int):
    try:
        cursor.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        subscriber_cache.add(chat_id)
        logger.info(f"Added subscriber: {chat_id}")
    except Exception as e:
        logger.error(f"Failed to add subscriber {chat_id}: {e}")


def remove_subscriber(chat_id: int):
    try:
        cursor.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        subscriber_cache.discard(chat_id)
        logger.info(f"Removed subscriber: {chat_id}")
    except Exception as e:
        logger.error(f"Failed to remove subscriber {chat_id}: {e}")


def get_all_subscribers():
    """Return all subscribers from DB."""
    cursor.execute("SELECT chat_id FROM subscribers")
    rows = cursor.fetchall()
    return [row[0] for row in rows]



async def periodic_cache_refresh(interval_minutes=10):
    while True:
        try:
            load_subscribers_cache()
            logging.info("Subscriber cache refreshed")
        except Exception as e:
            logging.error(f"Failed to refresh subscriber cache: {e}")
        await asyncio.sleep(interval_minutes * 60)


async def queue_consumer(signal_queue):
    while True:
        try:
            # Use run_in_executor to avoid blocking the event loop
            signal = await asyncio.get_event_loop().run_in_executor(None, signal_queue.get, True, 1)
            await send_signal_to_subscribers(signal)
        except Exception:
            await asyncio.sleep(0.5)


# ======================
# Signal message formatting
# ======================
def format_signal_message(signal):
    trend_emoji = {
        "Uptrend": "🟢📈 Buy",
        "Downtrend": "🔴📉 Sell",
        "Neutral": "⚪🔍 Neutral"
    }

    asset = signal.get("Asset", "Unknown")
    entry = signal.get("Entry Price", "N/A")
    target = signal.get("Take Profit", "N/A")
    stop = signal.get("Stop Loss", "N/A")
    trend = signal.get("Trend", "Neutral")
    date = signal.get("Date", "N/A")
    if hasattr(date, "strftime"):
        date = date.strftime("%Y-%m-%d %H:%M:%S UTC")

    message = (
        f"🚀 **New Trade Alert!**\n\n"
        f"📊 **Asset:** {asset}\n"
        f"💰 **Entry Price:** {entry}\n"
        f"🎯 **Target Price:** {target}\n"
        f"🛡️ **Stop Loss:** {stop}\n\n"
        f"📈 **Trend Bias:** {trend_emoji.get(trend, trend)}\n"
        f"📅 **Date:** {date}\n"
    )
    return message


# ======================
# Send signal to all subscribers
# ======================
async def send_signal_to_subscribers(signal):

    logger.info("The notify func called successfully")
    """
    Sends a trade signal to all subscribers while avoiding duplicates.
    Duplicate signals are identified using a unique signal_id.
    """
    # Construct unique signal_id
    signal_id = f"{signal['Asset']}_{signal['Entry Price']}_{signal['Take Profit']}_{signal['Stop Loss']}"

    # Remove expired signals
    now = datetime.now(timezone.utc)
    expired_keys = [k for k, v in sent_signals.items() if v < now]
    for k in expired_keys:
        del sent_signals[k]

    # Skip duplicate
    if signal_id in sent_signals:
        logger.info(f"Telegram Notification: Duplicate detected, skipping signal: {signal_id}")
        return

    # Format message
    message = format_signal_message(signal)

    # Send message to all subscribers
    for subscriber_id in get_all_subscribers():
        try:
            await bot.send_message(subscriber_id, message)
        except Exception as e:
            logger.error(f"Failed to send signal to {subscriber_id}: {e}")

    # Mark signal as sent for 1 hour
    sent_signals[signal_id] = now + timedelta(hours=1)
    logger.info(f"Telegram Notification: Signal sent and stored: {signal_id}")


# ======================
# Telegram command handlers
# ======================
@router.message(Command(commands=["start"]))
async def start_handler(message: Message):
    add_subscriber(message.chat.id)
    await message.answer(
        "✅ Welcome! You have been subscribed to trade signals.\n"
        "You will receive trade signals updates automatically."
    )


@router.message(Command(commands=["stop"]))
async def stop_handler(message: Message):
    remove_subscriber(message.chat.id)
    await message.answer(
        "❌ You have been unsubscribed from trade signals.\n"
        "Send /start anytime to subscribe again."
    )


@router.message(Command(commands=["report"]))
async def report_handler(message: Message):
    # Placeholder for future report
    await message.answer("📊 Report functionality coming soon. Stay tuned!")


# Include router
dp.include_router(router)

# Load subscriber cache at import
load_subscribers_cache()


# ======================
# Bot polling function
# ======================
async def jobber_telegram_bot():
    await dp.start_polling(bot)
