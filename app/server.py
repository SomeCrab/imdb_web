from http.server import HTTPServer
from configs.app_config import SERVER_HOST, SERVER_PORT
from app.handler import RequestHandler
import logging

logger = logging.getLogger(__name__)

def run_server() -> None:
    'This function starts the http server and closes it at the end'
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    logger.info(f"Сервер запущен на http://{SERVER_HOST}:{SERVER_PORT}")
    print(f"Сервер запущен на http://{SERVER_HOST}:{SERVER_PORT}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print('Сервер остановлен.')