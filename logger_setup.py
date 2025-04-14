# # logger_setup.py
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
import logging
import os
from datetime import datetime

# Ensure logs folder exists
os.makedirs("logs", exist_ok=True)

class DeduplicationFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.logged_messages = set()

    def filter(self, record):
        message_body = record.getMessage()  # This strips out timestamp/level
        if message_body in self.logged_messages:
            return False  # Skip duplicate
        self.logged_messages.add(message_body)
        return True  # Allow log

log_filename = f"logs/log_{datetime.now().strftime('%Y-%m-%d')}.log"

# Create formatter
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

# Create handlers
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(formatter)
file_handler.addFilter(DeduplicationFilter())

app_log_handler = logging.FileHandler("logs/app.log")
app_log_handler.setFormatter(formatter)
app_log_handler.addFilter(DeduplicationFilter())

# Optional: Add console handler if needed
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(formatter)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        app_log_handler,
        # stream_handler
    ]
)

# Create your logger
logger = logging.getLogger("algo_logger")
