import threading
import logging
import os
from logger_setup import logger, log_table_header, log_table_row
from BOT.models.model import build_and_evaluate_model

# ------------------------------------------------------
# 1. BUILD MODEL FOR A SINGLE ASSET
# ------------------------------------------------------
def build_single_asset_model(asset, fetcher, timeframes, n_splits):
    """
    Builds + evaluates model for ONE asset.
    Returns metrics ONLY.
    """

    model, wfv_acc, is_acc, trends = build_and_evaluate_model(
        fetcher, timeframes, n_splits
    )

    # Compute verdict
    diff_pct = abs((wfv_acc - is_acc) * 100)

    if diff_pct < 0.2:
        verdict = "Perfect"
    elif diff_pct < 0.5:
        verdict = "Excellent"
    elif diff_pct < 1.0:
        verdict = "Very Good"
    else:
        verdict = "Check"

    return model, wfv_acc, is_acc, verdict


# ------------------------------------------------------
# 2. ORCHESTRATOR
# ------------------------------------------------------
def build_models_for_assets(asset_data_fetchers, timeframes, rsi_period=14, n_splits=5):
    """
    High-level orchestrator:
    - Runs threads
    - Coordinates model building
    - Logs the table (ONLY table)
    - Returns {asset: results}
    """

    results = {}

    # Log header once
    separator = log_table_header()

    def worker(asset, fetcher):
        model, wfv_acc, is_acc, verdict = build_single_asset_model(
            asset, fetcher, timeframes, n_splits
        )

        # Save results
        results[asset] = {
            "model": model,
            "wfv_accuracy": wfv_acc,
            "in_sample_accuracy": is_acc,
            "verdict": verdict,
        }

        # Log table row
        log_table_row(asset, wfv_acc, is_acc, verdict)

    # Launch threads
    threads = []
    for asset, fetcher in asset_data_fetchers.items():
        t = threading.Thread(target=worker, args=(asset, fetcher))
        threads.append(t)
        t.start()

    # Join threads
    for t in threads:
        t.join()

    logger.info(separator)
    return results
