import MetaTrader5 as mt5
from BOT.orders.position import initial_pos, close_partial_position
from logger_setup import logger
def create_request_packet(symbol, lot, signal_data, trade_type):
    """
    Creates a request packet for an order.

    Args:
        symbol (str): The symbol for the trade.
        lot (float): Lot size for the trade.
        signal_data (dict): Data containing signal details.
        trade_type (int): Type of trade (e.g., BUY or SELL).

    Returns:
        dict: The request packet for the order.
    """
    return {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": trade_type,
        "price": signal_data["Entry Price"],
        "sl": signal_data["Stop Loss"],
        "tp": signal_data["Take Profit"],
        "deviation": 5,
        "magic": 234000,
        "comment": "python script open",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

def send_order(symbol, lot, signal_data, trade_type, open_trades, signal_lock, used_signals):
    """
    Sends an order to the trading platform.

    Args:
        symbol (str): The symbol for the trade.
        lot (float): Lot size for the trade.
        signal_data (dict): Data containing signal details.
        trade_type (int): Type of trade (e.g., BUY or SELL).
    """
    request = create_request_packet(symbol, lot, signal_data, trade_type)
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        open_trades[symbol] += 1
        with signal_lock:
            used_signals.add(signal_data["Signal ID"])
        logger.info(f"Trade successful for {symbol}. Signal ID {signal_data['Signal ID']} marked as used.")
    else:
        logger.error(f"Order failed, retcode={result.retcode}")

def orders(symbol, signal_data, open_trades, signal_lock, used_signals):
    """
    Processes a trade order based on RSI conditions.

    Args:
        symbol (str): The symbol for the trade.
        signal_data (dict): Data containing signal details.
        lot (float, optional): Lot size for the trade (default is from the market config).
    """
    lot, volume_to_close  = initial_pos(symbol, signal_data["ATR"])
    if signal_data["RSI_2"] <= 0.8:  # Condition for BUY trade
        send_order(symbol, lot, signal_data, mt5.ORDER_TYPE_BUY, open_trades, signal_lock, used_signals)
        close_partial_position(symbol, volume_to_close)
    elif signal_data["RSI_2"] >= 98:  # Condition for SELL trade
        send_order(symbol, lot, signal_data, mt5.ORDER_TYPE_SELL, open_trades, signal_lock, used_signals)
        close_partial_position(symbol, volume_to_close)
    