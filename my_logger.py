import logging

logging_format = "[%(levelname)s] %(asctime)s : %(name)10s : %(funcName)10s : %(message)s"

file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(logging_format))

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    return logger
