# # # # logger_setup.py
# import logging
# import os
# from datetime import datetime

# # Ensure logs folder exists
# os.makedirs("logs", exist_ok=True)



# class DeduplicationFilter(logging.Filter):
#     def __init__(self):
#         super().__init__()
#         self.logged_messages = set()

#     def filter(self, record):
#         if record.msg in self.logged_messages:
#             return False  # Skip duplicate
#         self.logged_messages.add(record.msg)
#         return True  # Allow log

# log_filename = f"logs/log_{datetime.now().strftime('%Y-%m-%d')}.log"

# # Logging configuration
# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] %(message)s',
#     handlers=[
#         logging.FileHandler(log_filename),
#         log_filename.setFormatter(format),
#         # logging.StreamHandler()  # Optional: prints to console too
#         log_filename.addFilter(DeduplicationFilter()),
#         logging.FileHandler("app.log"),
#         log_filename.addFilter(DeduplicationFilter()) 
#     ]
# )

# logger = logging.getLogger("algo_logger")
































# logger_setup.py
# import logging
# import os
# from datetime import datetime

# # Ensure logs folder exists
# os.makedirs("logs", exist_ok=True)

# class DeduplicationFilter(logging.Filter):
#     def __init__(self):
#         super().__init__()
#         self.logged_messages = set()

#     def filter(self, record):
#         message_body = record.getMessage()  # This strips out timestamp/level
#         if message_body in self.logged_messages:
#             return False  # Skip duplicate
#         self.logged_messages.add(message_body)
#         return True  # Allow log


# utc_now = datetime.now(timezone.utc)

# log_filename = f"logs/log_{utc_now.strftime('%Y-%m-%d')}.log"

# # Create formatter
# formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

# # Create handlers
# file_handler = logging.FileHandler(log_filename)
# file_handler.setFormatter(formatter)
# file_handler.addFilter(DeduplicationFilter())

# app_log_handler = logging.FileHandler("logs/app.log")
# app_log_handler.setFormatter(formatter)
# app_log_handler.addFilter(DeduplicationFilter())

# # Optional: Add console handler if needed
# # stream_handler = logging.StreamHandler()
# # stream_handler.setFormatter(formatter)

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     handlers=[
#         file_handler,
#         app_log_handler,
#         # stream_handler
#     ]
# )

# # Create your logger
# logger = logging.getLogger("algo_logger")


# ################################################################################################
# ###########EU daylight saving (correct auto-switch)	Europe/Berlin or Europe/Paris or Europe/Rome etc
# ################################################################################################























import logging
import os
import time
from datetime import datetime, timezone

# --- Custom Formatter forcing UTC timestamps ---
class UTCFormatter(logging.Formatter):
    converter = time.gmtime

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

# --- Setup format ---
log_format = '[%(asctime)s] [%(levelname)s] %(message)s'

# --- File Handlers (UTC) ---
log_filename = f"logs/log_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(UTCFormatter(log_format))

app_log_handler = logging.FileHandler("logs/app.log")
app_log_handler.setFormatter(UTCFormatter(log_format))

# --- Console Handler (Local time) ---
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(log_format))  # default: local time

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        app_log_handler,
        stream_handler
    ]
)

# --- Optional: Deduplication Filter ---
class DeduplicationFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.logged_messages = set()

    def filter(self, record):
        message_body = record.getMessage()
        if message_body in self.logged_messages:
            return False
        self.logged_messages.add(message_body)
        return True

# Attach the deduplication filter to handlers
dedup_filter = DeduplicationFilter()
file_handler.addFilter(dedup_filter)
app_log_handler.addFilter(dedup_filter)


# added today
# LOGGER SETUP
#TODO: Move to a separate file model_report_logger.py
# ------------------------------------------------------
def setup_model_report_logger(log_file="logs/multi_asset_model.log"):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger = logging.getLogger("MultiAssetLogger")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    # Console handler (add file handler later if needed)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

    return logger


logger = setup_model_report_logger()

#TODO: Move to a separate file logger_setup.py
# ------------------------------------------------------
# 1. LOGGING UTILITIES
# ------------------------------------------------------
def log_table_header():
    header = (
        f"| {'Asset':<12} | {'WFV Accuracy':<12} | {'IS Accuracy':<11} | "
        f"{'Difference':<10} | {'Verdict':<12} |"
    )
    separator = "-" * len(header)

    logger.info(separator)
    logger.info(header)
    logger.info(separator)

    return separator

#TODO: Move to a separate file model_report_logger.py
def log_table_row(asset, wfv_acc, is_acc, verdict):
    diff_pct = (wfv_acc - is_acc) * 100

    row = (
        f"| {asset:<12} | {wfv_acc:.4f}       | {is_acc:.4f}    "
        f"| {diff_pct:+.2f}%    | {verdict:<12} |"
    )
    logger.info(row)

# new update ends here


# --- Create logger ---
logger = logging.getLogger("algo_logger")

# # --- Example usage ---
# if __name__ == "__main__":
#     logger.info("Test log entry.")
