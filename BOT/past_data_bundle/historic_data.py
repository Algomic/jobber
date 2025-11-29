import os
import pandas as pd
from datetime import datetime, timedelta
import MetaTrader5 as mt5


# ---------------------------------------------
# SAFE MT5 INITIALIZATION
# ---------------------------------------------
def initialize_mt5():
    if not mt5.initialize():
        raise RuntimeError(f"MT5 Init failed: {mt5.last_error()}")
    print("✔ MT5 initialized")


# ---------------------------------------------
# FETCH RATES USING POSITION-BASED PULL
# ---------------------------------------------
def fetch_bars(symbol, timeframe, count):
    """Fetch 'count' historical bars from MT5, newest backward."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        raise RuntimeError(f"❌ Failed to fetch {count} bars for {symbol}: {mt5.last_error()}")

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.sort_values("time")


# ---------------------------------------------
# LOAD CSV CACHE IF EXISTS
# ---------------------------------------------
def load_cache(symbol, data_dir="data"):
    path = os.path.join(data_dir, f"{symbol}.csv")

    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["time"])
        return df, path

    return None, path


# ---------------------------------------------
# MAIN FUNCTION: 30-YEAR FIRST RUN + EXACT APPENDS
# ---------------------------------------------
def get_symbol_data(symbol, timeframe=mt5.TIMEFRAME_D1, data_dir="data"):
    """
    FIRST RUN:
        → Fetch 30,000 bars only
    SUBSEQUENT RUN:
        → Fetch EXACT number of missing days between last cached bar and today
    """
    os.makedirs(data_dir, exist_ok=True)

    df_cached, path = load_cache(symbol, data_dir)

    # ----------------------------
    # FIRST RUN — NO CACHE
    # ----------------------------
    if df_cached is None:
        print(f"⏳ No cache → Fetching 30,000 bars for {symbol}...")
        df = fetch_bars(symbol, timeframe, 30000)
        df.to_csv(path, index=False)
        print(f"✔ Cached full history → {path}")
        return df

    # ----------------------------
    # SUBSEQUENT RUN — ONLY MISSING DAYS
    # ----------------------------
    last_date = df_cached["time"].max().normalize()
    today = datetime.utcnow().normalize()

    days_missing = (today - last_date).days

    if days_missing <= 0:
        print(f"✔ {symbol}: No new bars")
        return df_cached

    print(f"⏳ {symbol}: Missing {days_missing} bars → Fetching...")

    # Fetch ONLY the missing bars
    df_new = fetch_bars(symbol, timeframe, days_missing)

    # Append only bars newer than last_date
    df_append = df_new[df_new["time"] > last_date]

    updated = pd.concat([df_cached, df_append], ignore_index=True)
    updated = updated.drop_duplicates(subset="time").reset_index(drop=True)
    updated.to_csv(path, index=False)

    print(f"✔ {symbol}: Added {len(df_append)} new bars → Updated cache")

    return updated


# ---------------------------------------------
# MULTI-SYMBOL HANDLER
# ---------------------------------------------
def fetch_for_all_symbols(symbols, timeframe=mt5.TIMEFRAME_D1, data_dir="data"):
    initialize_mt5()

    all_data = {}
    for sym in symbols:
        print("\n===============================")
        print(f"Fetching: {sym}")
        all_data[sym] = get_symbol_data(sym, timeframe, data_dir)

    mt5.shutdown()
    print("\n✔ Done fetching all symbols")
    return all_data


# ---------------------------------------------
# USAGE
# ---------------------------------------------
if __name__ == "__main__":
    symbols = ["EURUSD", "XAUUSD", "GBPUSD"]
    data = fetch_for_all_symbols(symbols)
