# from ..models import asset_data_fetchers, fetch_current_data, prepare_latest_data, make_prediction, build_models_for_assets, trends, models
import uuid
import ta
import MetaTrader5 as mt5
from BOT.models.model import fetch_current_data, prepare_latest_data, make_prediction, calculate_indicators_and_trend
from logger_setup import logger
# import models 

# timeframes = {'D': 20, '4h': 80, '1h': 240, '15min': 960}

# def sig(models):
#     asset_signal = {}
#     for asset, result in models.items():
#         # fetch data and predict market trend
#         model = result['model']
#         fetch_data = fetch_current_data(asset, mt5.TIMEFRAME_M15, 300)
#         prepared_data = prepare_latest_data(fetch_data, model, config["timeframes"])
#         trend_decision = make_prediction(prepared_data, model)
#         # print(f'{asset}: trend_decision: {trend_decision}' )
#         # market_signal[asset] = trend_decision          
#         asset_signal[asset] = signal(fetch_data, asset, mt5.TIMEFRAME_M15, trend_decision, 300) # 
#     return asset_signal


# sig(models)


# Working with this
def rsi_atr(data):
    # Calculate RSI with period 2
    data['RSI_2'] = ta.momentum.RSIIndicator(data['close'], window=2).rsi()
    
    # Calculate ATR
    data['ATR'] = ta.volatility.AverageTrueRange(high=data['high'], low=data['low'], close=data['close'], window=14).average_true_range()
    # print(data)
    return data


def create_signal(asset, entry_price, atr, trend, date, rsi_value):
    """
    Creates a trade signal based on the provided parameters.

    Args:
        entry_price (float): The price at which the trade is entered.
        atr (float): Average True Range value.
        trend (str): Current trend ('Uptrend' or 'Downtrend').
        date (datetime): The date of the signal.
        rsi_value (float): RSI value for the signal.

    Returns:
    """
    
    if trend == "Uptrend":
        stop_loss = entry_price - atr
        take_profit = entry_price + 3 * atr
    elif trend == "Downtrend":  # Downtrend
        stop_loss = entry_price + atr
        take_profit = entry_price - 3 * atr

    # Create a string to uniquely identify this signal
    signal_content = f"{date}|{asset}|{trend}|{entry_price}|{stop_loss}|{take_profit}|{atr}|{rsi_value}"
    # Use a namespace and the content string to create a deterministic UUID
    signal_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, signal_content))

    return {
        'Date': date,
        'Asset': asset,
        "Trend": trend,
        'Entry Price': entry_price,
        'Stop Loss': stop_loss,
        'Take Profit': take_profit,
        "Signal ID": signal_id,
        "RSI_2": rsi_value,
        "ATR": atr
    }

def generate_signals(data, asset, trend_decision):
    """
    Generates trade signals for the given asset and data based on trend conditions.

    Args:
        data (pd.DataFrame): Market data with indicators.
        asset (str): The asset name (e.g., 'Boom 1000', 'Crash 500').
        trend_decision (str): Current trend decision ('Uptrend' or 'Downtrend').

    Returns:
        list: A list of generated trade signals.
    """
    signals = []
    is_boom_market = asset.startswith("Boom")
    is_crash_market = asset.startswith("Crash")

    for i in range(len(data)):
        rsi_value = data['RSI_2'].iloc[i]
        entry_price = data['close'].iloc[i]
        atr = data['ATR'].iloc[i]
        date = data.index[i]

        if is_boom_market and trend_decision == "Uptrend" and rsi_value <= 0.8:
            # Buy condition for Boom markets
            signals.append(create_signal(asset, entry_price, atr, trend_decision, date, rsi_value))
        elif is_crash_market and trend_decision == "Downtrend" and rsi_value >= 98:
            # Sell condition for Crash markets
            signals.append(create_signal(asset, entry_price, atr, trend_decision, date, rsi_value))
        elif not (is_boom_market or is_crash_market):
            # General FX market rules
            if trend_decision == "Uptrend" and rsi_value <= 0.8:
                signals.append(create_signal(asset, entry_price, atr, trend_decision, date, rsi_value))
            elif trend_decision == "Downtrend" and rsi_value >= 98:
                signals.append(create_signal(asset, entry_price, atr, trend_decision, date, rsi_value))

    return signals



def signal(fetch_data, asset, timeframe, trend_decision, count): # 
    """
    Generates the most recent signal for the given asset and data.

    Args:
        fetch_data (pd.DataFrame): The fetched market data.
        asset (str): The asset name (e.g., 'Boom 1000', 'Crash 500').
        timeframe (str): The timeframe for the data.
        trend_decision (str): Current trend decision ('Uptrend' or 'Downtrend').
        count (int): Number of data points to consider.

    Returns:
        dict or None: The most recent trade signal, or None if no signals are generated.
    """
    try:
        # fetch_data = fetch_current_data(asset, timeframe, count)
        indicators_and_trend_data = calculate_indicators_and_trend(fetch_data)
        plus_rsi_atr_data = rsi_atr(indicators_and_trend_data)
        plus_rsi_atr_data.dropna(inplace=True)
        signals = generate_signals(plus_rsi_atr_data, asset, trend_decision)
        return signals[-1] if signals else None
    except IndexError as e:
        logger.error(f"Index error encountered: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return None
