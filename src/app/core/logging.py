import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    fmt = '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, dt_fmt))
    logger.addHandler(handler)
    return logger
