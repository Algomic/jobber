import MetaTrader5 as mt5
from BOT.models.model import fetch_current_data, fetch_and_store_data, prepare_latest_data, make_prediction, build_models_for_assets
from config import config
from BOT.orders.monitor import monitor_asset

import threading
import time
import os
from BOT.account.setup import open_platfrom, login
from dotenv import load_dotenv
from logger_setup import logger

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
# NAME = os.getenv("NAME")

# print(f"LOGIN: {LOGIN} PASSWORD: {PASSWORD} SERVER: {SERVER}") #PASSWORD: {PASSWORD} SERVER: {SERVER}"

# Setup and login into trading account.
# Open MT5 Trading Platform
open_platfrom(LOGIN, PASSWORD, SERVER)
logger.info("Terminal successfully initiated.")
# Login to trading account
login(ACCOUNT, PASSWORD, SERVER)
logger.info("Successfully logged in.")



# config = {
#             "timeframes" : {'D': 20, '4h': 80, '1h': 240, '15min': 960},
#             "asset_data_fetchers" : {
#                     "Boom 1000 Index": lambda: fetch_and_store_data("Boom 1000 Index", mt5.TIMEFRAME_D1),
#                     "Boom 500 Index": lambda: fetch_and_store_data("Boom 500 Index", mt5.TIMEFRAME_D1),
#                     "Crash 1000 Index": lambda: fetch_and_store_data("Crash 1000 Index", mt5.TIMEFRAME_D1),
#                     "Crash 500 Index": lambda: fetch_and_store_data("Crash 500 Index", mt5.TIMEFRAME_D1),
#                     "Step Index": lambda: fetch_and_store_data("Step Index", mt5.TIMEFRAME_D1),
#                     "Jump 100 Index": lambda: fetch_and_store_data("Jump 100 Index", mt5.TIMEFRAME_D1)
    
#             }

# }

# Initialize MetaTrader5
if not mt5.initialize():
    print("MetaTrader5 initialization failed")
    quit()

# Build and evaluate models for all assets
models = build_models_for_assets(config["asset_data_fetchers"], config["timeframes"])


# Thread
thread = threading.Thread(target=monitor_asset(models), daemon=True) #args=(asset, signal) update_open_trades
    # threads.append(thread)
thread.start()

    # Keep the main program running
try:
    while thread.is_alive():
        time.sleep(15*60)  # Keep checking if the thread is alive
except KeyboardInterrupt:
    print("Shutting down...")