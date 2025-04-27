from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader
import mysql.connector
import json
from dotenv import load_dotenv
from os import getenv
from config import Configuration as conf


# ! annotation, annotation everywhere
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

# Константы
MAX_ALLOWED_YEAR = conf.MAX_ALLOWED_YEAR
MIN_ALLOWED_YEAR = conf.MIN_ALLOWED_YEAR


def search_movies(title=None, min_year=None, max_year=None, nsfw=False, exact_year=None):
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT title, description, release_year, rating 
            FROM film 
            WHERE title LIKE %s
        """
        params = [f"%{title}%"]

        # Фильтр по году
        if exact_year:
            query += " AND release_year = %s"
            params.append(exact_year)
        else:
            if min_year:
                query += " AND release_year >= %s"
                params.append(min_year)
            if max_year:
                query += " AND release_year <= %s"
                params.append(max_year)
            
        # Фильтр исключения NSFW
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
    exact_year = query.get("exact_year", [None])[0]
    return movie_title, min_year, max_year, nsfw, exact_year

# TODO: проверить после добавления exact_year в search_movies()
def validate_year(value, name):
    """
    Преобразует строку в int и проверяет, что год в [YEAR_MIN, YEAR_MAX].
    Возвращает (год, сообщение об ошибке).
    """
    if not value:
        return None, None
    try:
        year = int(value)
    except ValueError:
        return None, f"Некорректный формат {name}"
    if not (MIN_ALLOWED_YEAR <= year <= MAX_ALLOWED_YEAR):
        return None, f"{name} должен быть между {MIN_ALLOWED_YEAR} и {MAX_ALLOWED_YEAR}"
    return year, None


def validate_parsed_data(movie_title, min_year, max_year, nsfw, exact_year):
    errors = []
    min_y, err = validate_year(min_year, "минимальный год")
    if err: errors.append(err)

    max_y, err = validate_year(max_year, "максимальный год")
    if err: errors.append(err)

    exact_y, err = validate_year(exact_year, "конкретный год")
    if err: errors.append(err)

    if exact_y is not None and (min_y is not None or max_y is not None):
        errors.append("Нельзя указывать конкретный год вместе с диапазоном")

    if exact_y is None:
        if min_y is not None and max_y is not None and min_y > max_y and max_y < min_year:
            errors.append("Минимальный год должен быть меньше максимального года")

    validated = {
        "title": movie_title,
        "min_year": min_y,
        "max_year": max_y,
        "nsfw": nsfw,
        "exact_year": exact_y
    }
    return errors, validated


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            
            # Главная страница
            if parsed_path.path == "/":
                self.send_custom_response(None)

            # страница about
            elif parsed_path.path == "/about":
                self.send_custom_response(None, templ='about.html')
                
            # Поиск через форму и API для AJAX-запросов
            elif parsed_path.path in ["/api/search", "/search"]:
                query = parse_qs(parsed_path.query)
                movie_title, min_year, max_year, nsfw, exact_year = parse_query(query)

                # Валидация
                errors, valid_data = validate_parsed_data(movie_title, min_year, max_year, nsfw, exact_year)

                if errors:
                    self.send_custom_response(errors, resp_code=400, Cont_type="application/json")
                    return
                
                results = search_movies(**valid_data)
                if parsed_path.path == "/api/search":
                    self.send_custom_response(results, Cont_type="application/json", api=True)
                else:
                    self.send_custom_response(results, valid_data)

            # шоукейс ошибки 500
            elif parsed_path.path == "/err":
                5/0
            
            # страница 404
            else:
                self.send_custom_response(None, resp_code=404, templ='not_found.html')
        except Exception as e:
            print(f"Error: {e}")
            self.send_custom_response(e, resp_code=500, templ='error.html')

    def send_custom_response(self, data, valid_data=None, resp_code=200, Cont_type="text/html", templ='index.html', api=False):
        self.send_response(resp_code)
        self.send_header("Content-type", Cont_type)
        self.end_headers()
        
        if resp_code == 400:
            self.wfile.write(json.dumps({"errors": data}).encode("utf-8"))
        elif api:
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            template = env.get_template(templ)
            html = template.render(results=data, queries=valid_data)
            self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    server_address = ("localhost", 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Сервер запущен на http://localhost:8000")
    httpd.serve_forever()