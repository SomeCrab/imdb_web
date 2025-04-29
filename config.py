from dotenv import load_dotenv
from os import getenv


# константы
MAX_ALLOWED_YEAR = 2030
MIN_ALLOWED_YEAR = 1890

# настройка сервера
SERVER_HOST = 'localhost'
SERVER_PORT = 8000

# Конфигурация MySQL
load_dotenv()
DB_CONFIG = {
    "host": getenv('HOST_READ'),
    "user": getenv('USER_READ'),
    "password": getenv('PASSWORD_READ'),
    "database": getenv('NAME_READ'),
    "raise_on_warnings": True
}