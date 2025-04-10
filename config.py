import MetaTrader5 as mt5
from BOT.models.model import fetch_current_data, fetch_and_store_data


config = {
            "timeframes" : {'D': 20, '4h': 80, '1h': 240, '15min': 960},
            "asset_data_fetchers" : {
                    "Boom 1000 Index": lambda: fetch_and_store_data("Boom 1000 Index", mt5.TIMEFRAME_D1),
                    "Boom 500 Index": lambda: fetch_and_store_data("Boom 500 Index", mt5.TIMEFRAME_D1),
                    "Crash 1000 Index": lambda: fetch_and_store_data("Crash 1000 Index", mt5.TIMEFRAME_D1),
                    "Crash 500 Index": lambda: fetch_and_store_data("Crash 500 Index", mt5.TIMEFRAME_D1),
                    "Step Index": lambda: fetch_and_store_data("Step Index", mt5.TIMEFRAME_D1),
                    "Jump 100 Index": lambda: fetch_and_store_data("Jump 100 Index", mt5.TIMEFRAME_D1)
    
            }

}
