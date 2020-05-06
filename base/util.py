import logging
import os
import sys


def log_level_from_env() -> int:
    level_str = os.getenv('LOG_LEVEL', 'info').lower().strip()
    if level_str == 'info':
        level = logging.INFO
    elif level_str == 'debug':
        level = logging.DEBUG
    elif level_str == 'error':
        level = logging.ERROR
    else:
        level = logging.ERROR
        print(f"Unknown logging level {level_str}", file=sys.stderr)
    return level


def init_stdout_logging():
    level = log_level_from_env()
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)
