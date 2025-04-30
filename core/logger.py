import logging.config
import json
from configs.app_config import LOG_DIR, LOGGING_CONFIG_FILE


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)

    with open(LOGGING_CONFIG_FILE) as f_in:
        config = json.load(f_in)
    logging.config.dictConfig(config=config)