import MetaTrader5 as mt5
from datetime import datetime, timedelta
# from BOT import config
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit
import ta  # Technical Analysis library for RSI calculation
import threading

def fetch_and_store_data(symbol, timeframe):
    # fetch historical data
    # rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_of_bars)
    utc_from = datetime(2019, 1, 1)
    utc_to = datetime(2025, 2, 18)
    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    df = pd.DataFrame(rates)
    df = df.rename(columns={"time":"datetime", "tick_volume":"volume"})
    df = df[["datetime", "open", "low", "close"]]
    df['datetime'] = pd.to_datetime(df['datetime'], unit='s')
    df.set_index('datetime', inplace=True)
    # df.to_csv("Boom1k.csv")
    return df



def calculate_indicators_and_trend(data,  rsi_period=14):
        data['50_EMA'] = data['close'].ewm(span=50, adjust=False).mean()
        data['200_EMA'] = data['close'].ewm(span=200, adjust=False).mean()
        data['RSI'] = ta.momentum.RSIIndicator(data['close'], window=rsi_period).rsi()
        data['Trend'] = np.where((data['50_EMA'] > data['200_EMA']) & (data['RSI'] > 50), 1, 0)
        data['Trend'] = np.where((data['50_EMA'] < data['200_EMA']) & (data['RSI'] < 50), -1, data['Trend'])
        return data 


def build_and_evaluate_model(data_fetcher, timeframes, rsi_period=14, n_splits=5):
    """
    Builds a trading model using technical indicators and evaluates it with walk-forward validation.

    Args:
        data_fetcher (function): Function to fetch and return market data as a DataFrame.
        timeframes (dict): Dictionary of timeframes for feature generation.
        rsi_period (int): RSI calculation period.
        n_splits (int): Number of splits for walk-forward validation.

    Returns:
        model (RandomForestClassifier): Trained RandomForest model.
        float: Mean accuracy from walk-forward validation.
    """
    def load_data():
        # return fetch_and_store_data(symbol, timeframe)
        return data_fetcher()


    # def calculate_indicators_and_trend(data):
    #     data['50_EMA'] = data['close'].ewm(span=50, adjust=False).mean()
    #     data['200_EMA'] = data['close'].ewm(span=200, adjust=False).mean()
    #     data['RSI'] = ta.momentum.RSIIndicator(data['close'], window=rsi_period).rsi()
    #     data['Trend'] = np.where((data['50_EMA'] > data['200_EMA']) & (data['RSI'] > 50), 1, 0)
    #     data['Trend'] = np.where((data['50_EMA'] < data['200_EMA']) & (data['RSI'] < 50), -1, data['Trend'])
    #     return data

    def prepare_features(data):
        features = pd.DataFrame(index=data.index)
        for tf, period in timeframes.items():
            tf_data = data.resample(tf).last()
            tf_data = calculate_indicators_and_trend(tf_data)
            features[f'{tf}_Trend'] = tf_data['Trend']
        features.dropna(inplace=True)
        return features

    # Load and preprocess data
    data = load_data()

    # Prepare features and labels
    features = prepare_features(data)
    features['Label'] = features['15min_Trend'].shift(-1)
    features.dropna(inplace=True)

    # Split data for walk-forward validation
    tscv = TimeSeriesSplit(n_splits=n_splits)
    accuracies = []
    model = RandomForestClassifier()

    for train_index, test_index in tscv.split(features):
        train, test = features.iloc[train_index], features.iloc[test_index]
        X_train, y_train = train.drop('Label', axis=1), train['Label']
        X_test, y_test = test.drop('Label', axis=1), test['Label']

        # Train the model
        model.fit(X_train, y_train)

        # Predict and evaluate
        predictions = model.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        accuracies.append(accuracy)

    mean_accuracy = np.mean(accuracies)
    print(f"Mean accuracy: {mean_accuracy:.2f}")

    return model, mean_accuracy # calculate_indicators_and_trend


# trends
# trends = 0
def build_models_for_assets(asset_data_fetchers, timeframes, rsi_period=14, n_splits=5):
    """
    Builds and evaluates models for multiple assets concurrently.

    Args:
        asset_data_fetchers (dict): Dictionary where keys are asset names and values are data-fetching functions.
        timeframes (dict): Dictionary of timeframes for feature generation.
        rsi_period (int): RSI calculation period.
        n_splits (int): Number of splits for walk-forward validation.

    Returns:
        dict: A dictionary of models and accuracies per asset.
    """
    results = {}

    def process_asset(asset, fetcher):
        # global trends
        print(f"Starting model build for {asset}...")
        model, accuracy = build_and_evaluate_model(fetcher, timeframes, n_splits)
        results[asset] = {"model": model, "accuracy": accuracy}
        print(f"Completed model for {asset}: Accuracy = {accuracy:.2f}")

        # return trends

    threads = []
    for asset, fetcher in asset_data_fetchers.items():
        thread = threading.Thread(target=process_asset, args=(asset, fetcher))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    return results



##########################################################################################################################
#                                           OUT-SAMPLE DATA
##########################################################################################################################

# fetch out-sample data
def fetch_current_data(market, timeframe, count, start_pos=0):
    # utc_from = datetime(2024, 7, 3)
    # utc_to = datetime(2024, 7, 23)

    # rates = mt5.copy_rates_range("Boom 1000 Index", mt5.TIMEFRAME_D1, utc_from, utc_to)
    rates = mt5.copy_rates_from_pos(market, timeframe, start_pos, count)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df



# clean data:
def pred_features(data, timeframes):
    pred_features = pd.DataFrame(index=data.index)
    for tf, period in timeframes.items():
        tf_data = data.resample(tf).last()
        tf_data = calculate_indicators_and_trend(tf_data) # calculate_indicators_and_trend
        pred_features[f'{tf}_Trend'] = tf_data['Trend']
    pred_features.dropna(inplace=True)
    return pred_features



def prepare_latest_data(data, model, timeframes):
    # data = fetch_current_data()
    features = pred_features(data, timeframes)
    recent_data = features.iloc[-1].drop('Label', errors='ignore')
    recent_data_df = pd.DataFrame([recent_data], columns=model.feature_names_in_)
    return recent_data_df


    
def make_prediction(recent_data_df, model):
    prediction = model.predict(recent_data_df)
    return 'Uptrend' if prediction[0] == 1 else 'Downtrend'


# main
# if __name__ == "__main__":
    # Define timeframes and periods for trend determination
    # timeframes = {'D': 20, '4h': 80, '1h': 240, '15min': 960}

    # # Define data fetchers for assets
    # asset_data_fetchers = {
    #     "Boom 1000 Index": lambda: fetch_and_store_data("Boom 1000 Index", mt5.TIMEFRAME_D1),
    #     "Boom 500 Index": lambda: fetch_and_store_data("Boom 500 Index", mt5.TIMEFRAME_D1),
    #     "Crash 1000 Index": lambda: fetch_and_store_data("Crash 1000 Index", mt5.TIMEFRAME_D1),
    #     "Crash 500 Index": lambda: fetch_and_store_data("Crash 500 Index", mt5.TIMEFRAME_D1),
    #     "Step Index": lambda: fetch_and_store_data("Step Index", mt5.TIMEFRAME_D1),
    #     "Jump 100 Index": lambda: fetch_and_store_data("Jump 100 Index", mt5.TIMEFRAME_D1)
    #     # "EURUSD": lambda: fetch_and_store_data("Jump 100 Index", mt5.TIMEFRAME_D1)
    # }

    # Initialize MetaTrader5
    if not mt5.initialize():
        print("MetaTrader5 initialization failed")
        quit()

    # Build and evaluate models for all assets
    # models = build_models_for_assets(config.asset_data_fetchers, timeframes)
    # print(models)
    
    # market_signal = {}
    # for asset, result in models.items():
    #     model = result['model']
    #     data = fetch_current_data(asset, mt5.TIMEFRAME_D1, 3)
    #     latest_data = prepare_latest_data(data, model, timeframes)
    #     trend_decision = make_prediction(latest_data, model)
    #     market_signal[asset] = trend_decision
    # print(market_signal)

    # Shutdown MetaTrader5 after use
    # mt5.shutdown()
