from dotenv import load_dotenv
from os import getenv
from pathlib import Path


# Paths
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
LOG_DIR = BASE_DIR / "logs"
LOGGING_CONFIG_FILE = BASE_DIR / "configs" / "logging_config" / "config.json"

# Constants
MAX_ALLOWED_YEAR = 2030
MIN_ALLOWED_YEAR = 1890
LIMIT = 50

# server set ups
SERVER_HOST = 'localhost'
SERVER_PORT = 8000

# MySQL configuration
load_dotenv()
STATS_DB_NAME = getenv('STATS_DB_NAME')
DB_CONFIG = {
    "host": getenv('HOST_WRITE'),
    "user": getenv('USER_WRITE'),
    "password": getenv('PASSWORD_WRITE'),
    "database": getenv('NAME_WRITE'),
    "raise_on_warnings": True
}