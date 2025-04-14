import MetaTrader5 as mt5
from logger_setup import logger

# details = {"ACCOUNT": 40477972, "LOGIN": 40477972, "PASSWORD":"081excel200@DMT5", "SERVER":"Deriv-Demo", "STARTING_BAL":100}


# Initialize mt5
def open_platfrom(login, password, server):
    if not mt5.initialize(login=login, password=password, server=server):
        logger.critical(f"Failed to start up mt5 terminal, error code: {mt5.last_error()}")
        quit()
    else:
        logger.info(f"Mt5 terminal initiated successfully!. ")
    # print(login, password, server)

# open_platfrom(details["LOGIN"], details["PASSWORD"], details["SERVER"])
# open_platfrom(LOGIN, PASSWORD, SERVER)




# Login to account
def login(account, password, server):
    if not mt5.login(account, password, server):
        logger.error(f"failed to login to #{account}")
    else:
        accnt_info = mt5.account_info()._asdict()
        for prop in accnt_info:
            if prop == 'login':
                logger.info(f"Account Details\nLogin: {accnt_info[prop]}")
            elif prop == 'balance':
                logger.info(f"Balance: {accnt_info[prop]}")
            elif prop == 'name':
                logger.info(f"Name: {accnt_info[prop]}")

    # print(account, password, server)

# login(ACCOUNT, PASSWORD, SERVER)