from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader
import mysql.connector
import json
from dotenv import load_dotenv
from os import getenv


# Загрузка переменных окружения
load_dotenv()

# Настройка Jinja2
env = Environment(loader=FileSystemLoader('templates'))

# Конфигурация MySQL
db_config = {
    "host": getenv('HOST_READ'),
    "user": getenv('USER_READ'),
    "password": getenv('PASSWORD_READ'),
    "database": getenv('NAME_READ'),
    "raise_on_warnings": True
}


def search_movies(title):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT title, description, release_year, rating 
            FROM film 
            WHERE title LIKE %s
            LIMIT 10
        """
        cursor.execute(query, (f"%{title}%",))
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return results
        
    except mysql.connector.Error as err:
        print(f"Ошибка MySQL: {err}")
        return []

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Главная страница
        if parsed_path.path == "/":
            template = env.get_template('index.html')
            html = template.render(results=None)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        # страница about
        elif parsed_path.path == "/about":
            template = env.get_template('about.html')
            html = template.render()
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            
        # Поиск через форму
        elif parsed_path.path == "/search":
            query = parse_qs(parsed_path.query)
            movie_title = query.get("movie", [""])[0]
            results = search_movies(movie_title)
            
            template = env.get_template('index.html')
            html = template.render(results=results)
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            
        # API для AJAX-запросов
        elif parsed_path.path == "/api/search":
            query = parse_qs(parsed_path.query)
            movie_title = query.get("movie", [""])[0]
            results = search_movies(movie_title)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(results).encode("utf-8"))
            
        else:
        # страница 404
            
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")

if __name__ == "__main__":
    server_address = ("localhost", 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Сервер запущен на http://localhost:8000")
    httpd.serve_forever()