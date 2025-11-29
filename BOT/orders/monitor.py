'''
{'Jump 100 Index': {'Date': Timestamp('2024-12-21 20:15:00'),
  'Asset': 'Jump 100 Index',
  'Trend': 'Downtrend',
  'Entry Price': 1970.44,
  'Stop Loss': 1989.9173099588813,
  'Take Profit': 1853.5761402467117,
  'Signal ID': 'ab0b8381-7702-534f-a59e-64f647db4cb5',
  'RSI_2': 99.62655103108514},
 'Crash 500 Index': {'Date': Timestamp('2024-12-21 17:00:00'),
  'Asset': 'Crash 500 Index',
  'Trend': 'Downtrend',
  'Entry Price': 4129.293,
  'Stop Loss': 4137.413139174382,
  'Take Profit': 4080.572164953706,
  'Signal ID': '3cb1182b-0304-50f3-a87b-da67930061d2',
  'RSI_2': 99.19236879267369},
 'Step Index': {'Date': Timestamp('2024-12-21 18:30:00'),
  'Asset': 'Step Index',
  'Trend': 'Downtrend',
  'Entry Price': 8275.2,
  'Stop Loss': 8279.56144644471,
  'Take Profit': 8249.031321331746,
  'Signal ID': '004e8331-6a3a-591d-af57-56aee2aa026b',
  'RSI_2': 99.32909816827858},
 'Crash 1000 Index': None,
 'Boom 500 Index': None,
 'Boom 1000 Index': None}
 
'''



import time
import threading
from datetime import datetime, timedelta, timezone
from BOT.strategy.strategy import signal
from BOT.models.data_pipeline import fetch_current_data, prepare_latest_data, make_prediction
import MetaTrader5 as mt5
import pandas as pd
from BOT.orders.request import orders
from config import config
from logger_setup import logger
import asyncio
from aiogram import Bot, Dispatcher, html
from telegram_update import send_trade_signal
import sqlite3
from telegram_bot import bot, send_signal_to_subscribers
import asyncio
import multiprocessing as mp




# Global variables to manage state
used_signals = {}  # Tracks used signals per asset
open_trades = {}  # Tracks open trades per asset
signal_lock = threading.Lock()  # Lock for thread-safe operations


def sig(models):
    asset_signal = {}
    for asset, result in models.items():
        # fetch data and predict market trend
        model = result['model']
        fetch_data = fetch_current_data(asset, mt5.TIMEFRAME_M15, 300)
        prepared_data = prepare_latest_data(fetch_data, model, config["timeframes"])
        trend_decision = make_prediction(prepared_data, model)
        # print(f'{asset}: trend_decision: {trend_decision}' )
        # market_signal[asset] = trend_decision          
        asset_signal[asset] = signal(fetch_data, asset, trend_decision) # signal(fetch_data, asset, mt5.TIMEFRAME_M15, trend_decision, 300)
    return asset_signal

def update_open_trades():
    """
    Updates the open_trades dictionary by synchronizing it with the MT5 positions.
    Removes assets with no open positions and adjusts counts for others.
    """
    # Get all current positions
    positions = mt5.positions_get()

    # Reset the open_trades count
    current_open_trades = {}

    if positions:
        for position in positions:
            symbol = position.symbol
            if symbol not in current_open_trades:
                current_open_trades[symbol] = 0
            current_open_trades[symbol] += 1

    # Update global open_trades dictionary
    global open_trades
    open_trades = current_open_trades
    logger.info(f"Updated open trades: {open_trades}")

def is_signal_date_valid(signal_time, tolerance_minutes=2):
    """
    Checks if the signal time is within the tolerance window.
    """
    now = datetime.now(timezone.utc) #.strftime('%Y-%m-%d %H:%M:%S') #timezone.utc
    signal_date = pd.Timestamp(signal_time, tz='UTC').to_pydatetime()
    return now - timedelta(minutes=tolerance_minutes) <= signal_date <= now + timedelta(minutes=tolerance_minutes)


conn = sqlite3.connect("subscribers.db")
cursor = conn.cursor()


def clear_queue(q):
    """Remove all items from the queue."""
    while not q.empty():
        try:
            q.get_nowait()
        except Exception:
            break

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()  # Start time before calling the function
        result = func(*args, **kwargs)
        end_time = time.time()    # End time after calling the function
        logger.info(f"{func.__name__} ran for {(end_time - start_time)/60:.2f} minutes")
        
        return result
    return wrapper

# @timing_decorator
# def monitor_asset(models, signal_queue, session_ON=True, max_open_trades=2, wake=2):
#     """Function to monitor assets and process signals."""
#     def is_time_to_check():
#         """Checks if the current time is aligned with the 2-minute interval."""
#         now = datetime.now(timezone.utc) # .strftime('%Y-%m-%d %H:%M:%S') # timezone.utc
#         return now.minute % 15 == 0 and now.second < 60  # Allow a 2-second window

#     while session_ON:
#         try:
#             # Fetch signals for all assets
# #             assets_signal = sig(models)

#             # Debugging output for assets_signal
# #             print(f"Assets Signal: {assets_signal}")

#             # Process each asset in the signal data
#             for asset, signal in sig(models).items():
# #                 print(f"Processing {asset}, Signal: {signal}")

#                 if signal is None:
#                     continue

#                 if asset not in used_signals:
#                     used_signals[asset] = set()
#                 if asset not in open_trades:
#                     open_trades[asset] = 0

#                 if is_time_to_check(): 
#                     update_open_trades()
#                     logger.info(f"Open trades updated for {asset}")

#                     if open_trades.get(asset, 0) >= max_open_trades:
#                         logger.warning(f"Max open trades reached for {asset}. Skipping.")
#                         continue

#                     signal_id = signal["Signal ID"]
#                     signal_time = signal["Date"]

#                     with signal_lock:
#                         if signal_id in used_signals[asset]:
#                             logger.warning(f"Signal {signal_id} already used for {asset}. Skipping.")
#                             continue
# #                         used_signals[asset].add(signal_id)

#                     try:
#                         if is_signal_date_valid(signal_time):
#                             orders(asset, signal, open_trades, signal_lock, used_signals)
#                             # Instead of sending notification directly, put signal in queue
#                             signal_queue.put(signal)
#                         else:
#                             logger.warning(f"Signal time {signal_time} is not valid for {asset}. Skipping.")
                           
#                     except Exception as e:
#                         logger.error(f"Failed to execute order for {asset}: {e}")

#         except KeyboardInterrupt:
#             logger.info("Shutting down monitor...")
#             session_ON = False
#         except Exception as e:
#             logger.fatal(f"Unexpected error: {e}")
#         time.sleep(wake * 60)  # Sleep for 'wake' minutes before next check






@timing_decorator
def monitor_asset(models, signal_queue, session_ON=True, max_open_trades=2, wake=2):
    def is_time_to_check():
        now = datetime.now(timezone.utc)
        return now.minute % 15 == 0 and now.second < 60

    while session_ON:
        try:
            # Clear the queue at the start of each loop
            clear_queue(signal_queue)

            for asset, signal in sig(models).items():
                if signal is None:
                    continue

                signal_id = signal["Signal ID"]
                signal_time = signal["Date"]

                if asset not in used_signals:
                    used_signals[asset] = set()
                if asset not in open_trades:
                    open_trades[asset] = 0

                if is_time_to_check():
                    update_open_trades()
                    logger.info(f"Open trades updated for {asset}")

                    if open_trades.get(asset, 0) >= max_open_trades:
                        logger.warning(f"Max open trades reached for {asset}. Skipping.")
                        continue

                    with signal_lock:
                        # Only process if signal_id is not already used
                        if signal_id in used_signals[asset]:
                            logger.info(f"Signal {signal_id} already used for {asset}. Skipping.")
                            continue

                    try:
                        if is_signal_date_valid(signal_time):
                            # Place order; used_signals will be updated in request.py after success
                            orders(asset, signal, open_trades, signal_lock, used_signals)
                            signal_queue.put(signal)
                        else:
                            logger.warning(f"Signal time {signal_time} is not valid for {asset}. Skipping.")
                    except Exception as e:
                        logger.error(f"Failed to execute order for {asset}: {e}")

        except KeyboardInterrupt:
            logger.info("Shutting down monitor...")
            session_ON = False
        except Exception as e:
            logger.fatal(f"Unexpected error: {e}")
        # time.sleep(wake * 60)  # Sleep for 'wake' minutes before next check