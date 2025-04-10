import math
import MetaTrader5 as mt5

def position_size(asset, asset_present_volatility, starting_bal, step_size= 0.02, initial_lot= 0.05, lot_increment = 0.01, max_multiplier= 1.5):
    asset_max_volatility = {'Jump 100 Index': 15, 'Step Index': 5, 'Crash 500 Index': 8, 'Boom 500 Index': 12, 
    'Boom 1000 Index': 21, 'Crash 1000 Index': 7}
    free_margin = mt5.account_info()._asdict()["margin_free"]
    if free_margin < starting_bal:
        base_position = initial_lot
    else:
        step_count = (free_margin - 100) // step_size
        base_position = initial_lot + (step_count * lot_increment)
        
    adjustment_factor = asset_max_volatility[asset] / asset_present_volatility
    adjustment_factor = min(adjustment_factor, max_multiplier)
    # Compute the adjusted position size:
    adjusted_position_size = base_position * adjustment_factor
    return round(adjusted_position_size, 2)


def initial_pos(asset, asset_present_volatility):
        required_lot = position_size(asset, asset_present_volatility)
        minimum_lot = mt5.symbol_info(asset)._asdict()["volume_min"]
        volume_to_close = minimum_lot - required_lot
        if required_lot < minimum_lot:
            return (minimum_lot, volume_to_close)
        else:
            volume_to_close = 0
            return (required_lot, volume_to_close)



# close partial positions


def close_partial_position(symbol, volume_to_close):
    """
    Closes a partial portion of an open position for the specified symbol.
    
    Parameters:
    - symbol (str): The trading symbol (e.g., "EURUSD").
    - volume_to_close (float): The volume to close (e.g., 0.5 lots).
    
    Returns:
    - bool: True if the operation succeeds, False otherwise.
    """
    # Fetch open positions for the given symbol
    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        print(f"No open positions found for {symbol}.")
        return False

    # Process each position
    for position in positions:
        # Extract position details
        ticket = position.ticket
        open_volume = position.volume

        # Ensure there's enough volume to close
        if volume_to_close > open_volume:
            print(f"Requested close volume ({volume_to_close}) exceeds open volume ({open_volume}). Skipping.")
            continue

        # Determine trade action based on position type
        if position.type == mt5.ORDER_TYPE_BUY:
            action = mt5.ORDER_SELL
        elif position.type == mt5.ORDER_TYPE_SELL:
            action = mt5.ORDER_BUY
        else:
            print(f"Unknown position type for ticket {ticket}. Skipping.")
            continue

        # Prepare the close request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume_to_close,
            "type": action,
            "position": ticket,  # Reference the position to close
            "price": mt5.symbol_info_tick(symbol).bid if action == mt5.ORDER_BUY else mt5.symbol_info_tick(symbol).ask,
            "deviation": 10,  # Maximum price deviation in points
            "comment": "Partial close",
        }

        # Send the trade request
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close partial position for {symbol}. Error: {result.comment}")
            return False

        print(f"Successfully closed {volume_to_close} lots of {symbol} position.")
        return True  # Exit after handling one position

    print(f"No matching positions for partial closure on {symbol}.")
    return False
