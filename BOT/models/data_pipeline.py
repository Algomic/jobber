#-----------------------------------------------------------
# BOT/models/data_pipeline.py
# OUT-SAMPLE DATA PIPELINE FUNCTIONS
#-----------------------------------------------------------

import MetaTrader5 as mt5
from datetime import datetime, timedelta
# from BOT import config
from .model import calculate_indicators_and_trend
import pandas as pd
# import numpy as np
# import lightgbm as lgb
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.metrics import accuracy_score
# from sklearn.model_selection import TimeSeriesSplit
# import ta  # Technical Analysis library for RSI calculation
# import threading
# from logger_setup import logger


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

