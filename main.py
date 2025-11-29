# import MetaTrader5 as mt5
# from BOT.models.model import fetch_current_data, fetch_and_store_data, prepare_latest_data, make_prediction, build_models_for_assets
# from config import config
# from BOT.orders.monitor import monitor_asset

# import threading
# import time
# import os
# import sys
# from BOT.account.setup import open_platfrom, login
# from dotenv import load_dotenv
# from logger_setup import logger
# # from telegram_update import jobber_telegram_bot
# from telegram_bot import bot, jobber_telegram_bot, periodic_cache_refresh
# import asyncio
# import signal





# logger.info("Starting the app...")
# logger.warning("This might be risky.")
# logger.critical("This is a heavy duty program !!!")



# # Load environment variables from .env
# load_dotenv(override=True)

# # Credentials
# ACCOUNT = int(os.getenv("ACCOUNT"))
# LOGIN = int(os.getenv("LOGIN"))
# PASSWORD = os.getenv("PASSWORD")
# SERVER = os.getenv("SERVER")
# STARTING_BAL = int(os.getenv("STARTING_BAL"))

# # Setup and login into trading account.
# # Open MT5 Trading Platform
# open_platfrom(LOGIN, PASSWORD, SERVER)
# logger.info("Terminal successfully initiated.")
# # Login to trading account
# login(ACCOUNT, PASSWORD, SERVER)
# logger.info("Successfully logged in.")


# # Build and evaluate models for all assets
# models = build_models_for_assets(config["asset_data_fetchers"], config["timeframes"])

# def monitor_asset_sync(models, bot, loop): 
#     # your existing monitor logic
#     thread = threading.Thread(target=monitor_asset(models, bot, loop), daemon=True) #args=(asset, signal) update_open_trades
#     # thread.append(thread)
#     thread.start()

#     # Keep the main program running
#     try:
#         while thread.is_alive():
#             time.sleep(15*60)  # Keep checking if the thread is alive
#             SystemExit
#     except KeyboardInterrupt:
#         logger.info("Shutting down...")
      




# # signal.signal(signal.SIGINT)

# async def main():
#     loop = asyncio.get_running_loop()
#     # 1) offload monitor_asset to a background thread
#     loop.run_in_executor(None, monitor_asset_sync, models, bot, loop)

#     # 2) Start periodic cache refresh (optional)
#     asyncio.create_task(periodic_cache_refresh())

#     # 3) run the Telegram bot forever
#     await jobber_telegram_bot()



# # Keyboard Interruption 
# # interrupt_count = 0

# # def handler(signum, frame):
# #     global interrupt_count
# #     interrupt_count += 1
# #     if interrupt_count == 1:
# #         print("\n(Press Ctrl-C again to quit.)")
# #     else:
# #         print("\nExiting on second Ctrl-C.")
# #         sys.exit(0)

# # signal.signal(signal.SIGINT, handler)

# if __name__ == "__main__":
#     asyncio.run(main())




















































import MetaTrader5 as mt5
from BOT.models.build_assets_models import build_models_for_assets
from config import config
from BOT.orders.monitor import monitor_asset
from BOT.account.setup import open_platfrom, login
from dotenv import load_dotenv
from logger_setup import logger
from telegram_bot import jobber_telegram_bot, periodic_cache_refresh, queue_consumer

import os
import threading
import time
import asyncio
import multiprocessing
import signal
import sys


signal_queue = multiprocessing.Queue()
logger.info("Starting the app...")
logger.warning("This might be risky.")
logger.critical("This is a heavy duty program !!!")

# Load environment variables from .env
load_dotenv(override=True)

# Credentials
ACCOUNT = int(os.getenv("ACCOUNT"))
LOGIN = int(os.getenv("LOGIN"))
PASSWORD = os.getenv("PASSWORD")
SERVER = os.getenv("SERVER")
STARTING_BAL = int(os.getenv("STARTING_BAL"))

# Setup and login into trading account
open_platfrom(LOGIN, PASSWORD, SERVER)
logger.info("Terminal successfully initiated.")
login(ACCOUNT, PASSWORD, SERVER)
logger.info("Successfully logged in.")

# Build and evaluate models for all assets
models = build_models_for_assets(config["asset_data_fetchers"], config["timeframes"])


# --- Trading Monitor Loop (Sync) ---
def start_monitoring(signal_queue):
    while True:
        try:
            monitor_asset(models, signal_queue)
            time.sleep(15 * 60)
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            time.sleep(60)


# --- Telegram Bot Runner (Async in its own thread) ---

# bot_loop = None
def run_telegram_bot(signal_queue):
    async def runner():
        # global bot_loop
        # bot_loop = asyncio.get_running_loop()
        asyncio.create_task(periodic_cache_refresh())
        asyncio.create_task(queue_consumer(signal_queue))  # <-- Start consumer
        await jobber_telegram_bot()
    asyncio.run(runner())


def main():
    # Start Telegram bot in a background thread
    telegram_thread = threading.Thread(target=run_telegram_bot, args=(signal_queue,), daemon=True)
    telegram_thread.start()

    # Start the trading monitor (blocking loop)
    start_monitoring(signal_queue)


if __name__ == "__main__":
    main()
