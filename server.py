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


def search_movies(title, min_year=None, max_year=None, nsfw=False):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        print(f'search_movies: {nsfw}{type(nsfw)}')
        query = """
            SELECT title, description, release_year, rating 
            FROM film 
            WHERE title LIKE %s
        """
        params = [f"%{title}%"]

        # Фильтр по году
        if min_year:
            query += " AND release_year >= %s"
            params.append(min_year)
        if max_year:
            query += " AND release_year <= %s"
            params.append(max_year)
            
        # Фильтр NSFW
        if nsfw:
            query += " AND rating != 'NC-17'"

        query += " LIMIT 10"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        return results
        
    except mysql.connector.Error as err:
        print(f"Ошибка MySQL: {err}")
        return []


def parse_query(query):
    movie_title = query.get("movie", [""])[0]
    min_year = query.get("min_year", [None])[0]
    max_year = query.get("max_year", [None])[0]
    nsfw = query.get("nsfw", ["false"])[0].lower() == "on"
    return movie_title, min_year, max_year, nsfw


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Главная страница
        if parsed_path.path == "/":
            self.send_custom_response(None)

        # страница about
        elif parsed_path.path == "/about":
            self.send_custom_response(None, templ='about.html')
            
        # Поиск через форму
        elif parsed_path.path == "/search":
            query = parse_qs(parsed_path.query)
            movie_title, min_year, max_year, nsfw = parse_query(query)
            
            
            # Валидация
            errors = []
            try:
                min_year = int(min_year) if min_year else None
                if min_year and (min_year < 1890 or min_year > 2030):
                    errors.append("Минимальный год должен быть между 1890 и 2030")
            except ValueError:
                errors.append("Некорректный формат минимального года")

            try:
                max_year = int(max_year) if max_year else None
                if max_year and (max_year < 1890 or max_year > 2030):
                    errors.append("Максимальный год должен быть между 1890 и 2030")
            except ValueError:
                errors.append("Некорректный формат максимального года")

            if min_year and max_year and min_year > max_year:
                errors.append("Минимальный год не может быть больше максимального")

            if errors:
                self.send_custom_response(errors, resp_code=400, Cont_type="application/json")
                return
            
            results = search_movies(
                title=movie_title,
                min_year=min_year,
                max_year=max_year,
                nsfw=nsfw
            )
            print(f'parsed res: {results}{type(results)}')
            self.send_custom_response(results)
            
        # API для AJAX-запросов
        elif parsed_path.path == "/api/search":
            query = parse_qs(parsed_path.query)
            movie_title, min_year, max_year, nsfw = parse_query(query)
            print(f'parsed nsfw: {nsfw}{type(nsfw)}')

            # Валидация
            errors = []
            try:
                min_year = int(min_year) if min_year else None
                if min_year and (min_year < 1890 or min_year > 2030):
                    errors.append("Минимальный год должен быть между 1890 и 2030")
            except ValueError:
                errors.append("Некорректный формат минимального года")

            try:
                max_year = int(max_year) if max_year else None
                if max_year and (max_year < 1890 or max_year > 2030):
                    errors.append("Максимальный год должен быть между 1890 и 2030")
            except ValueError:
                errors.append("Некорректный формат максимального года")

            if min_year and max_year and min_year > max_year:
                errors.append("Минимальный год не может быть больше максимального")

            if errors:
                self.send_custom_response(errors, resp_code=400, Cont_type="application/json")
                return
            
            results = search_movies(
                title=movie_title,
                min_year=min_year,
                max_year=max_year,
                nsfw=nsfw
            )
            
            self.send_custom_response(results, Cont_type="application/json", api=True)

        # страница 404
        else:
            self.send_custom_response(None, resp_code=404, templ='not_found.html')

    def send_custom_response(self, data, resp_code=200, Cont_type="text/html", templ='index.html', api=False):
        if not api:
            template = env.get_template(templ)
            html = template.render(results=data)
        self.send_response(resp_code)
        self.send_header("Content-type", Cont_type)
        self.end_headers()
        if resp_code == 404:
            self.wfile.write(html.encode("utf-8"))
        elif resp_code == 400:
            self.wfile.write(json.dumps({"errors": data}).encode("utf-8"))
        elif not api:
            self.wfile.write(html.encode("utf-8"))
        else:
            self.wfile.write(json.dumps(data).encode("utf-8"))


if __name__ == "__main__":
    server_address = ("localhost", 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Сервер запущен на http://localhost:8000")
    httpd.serve_forever()