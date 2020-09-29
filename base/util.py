import logging
import os
import pathlib
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


LOG_FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def init_file_logging(log_path) -> logging.Logger:
    level = log_level_from_env()
    logger = logging.getLogger()
    logger.setLevel(level)

    try:
        logger.info(f"Log path: {log_path}")
        path = pathlib.Path(log_path)

        def file_ready(file_path):
            try:
                return file_path.exists()
            except PermissionError:
                return False

        if not file_ready(path):
            logger.info(f"Path does't exists: {log_path}")
            logger.info("Try to create it.")
            path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(LOG_FORMATTER)
        logger.addHandler(file_handler)
    except Exception:
        logger.exception("Can't create file handler for logger")
    return logging


def init_stdout_logging() -> logging.Logger:
    level = log_level_from_env()
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)

    handler.setFormatter(LOG_FORMATTER)
    root.addHandler(handler)
    return root
