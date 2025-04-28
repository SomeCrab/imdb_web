from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from jinja2 import Environment, FileSystemLoader
import mysql.connector
from contextlib import contextmanager
import logging
import json
from config import MAX_ALLOWED_YEAR, MIN_ALLOWED_YEAR, SERVER_HOST, SERVER_PORT, DB_CONFIG as db_config


# ! annotation, annotation everywhere
# ! naming
# Настройка Jinja2
env = Environment(loader=FileSystemLoader('templates'))

# логирование
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)
file_handler = logging.FileHandler('app_errors.log', encoding='utf-8')
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


# db stuff
@contextmanager
def db_cursor(dictionary=True):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        connection.commit()
    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        logger.error("Ошибка MySQL в db_cursor: %s", e)
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def get_all_categories():
    try:
        with db_cursor() as cursor:
            cursor.execute(r"SELECT category_id, name FROM category ORDER BY name")
            return cursor.fetchall()
    except mysql.connector.Error:
        return []


def make_qerry(title=None, min_year=None, max_year=None, nsfw=False, exact_year=None, categories=None):
    if categories:
        query = """
            SELECT DISTINCT f.title, f.description, f.release_year, f.rating
            FROM film AS f
            JOIN film_category AS fc ON f.film_id = fc.film_id
            WHERE fc.category_id IN ({placeholders})
                AND f.title LIKE %s
        """
        # placeholders = '%s, %s, …' столько, сколько категорий
        ph = ','.join(['%s'] * len(categories))
        query = query.format(placeholders=ph)
        params = [*categories, f"%{title}%"]
    else:
        query = """
            SELECT f.title, f.description, f.release_year, f.rating
            FROM film AS f
            WHERE f.title LIKE %s
        """
        params = [f"%{title}%"]

    # Фильтр по году
    if exact_year:
        query += " AND f.release_year = %s"
        params.append(exact_year)
    else:
        if min_year:
            query += " AND f.release_year >= %s"
            params.append(min_year)
        if max_year:
            query += " AND f.release_year <= %s"
            params.append(max_year)
        
    # Фильтр исключения NSFW
    if nsfw:
        query += " AND f.rating != 'NC-17'"
    # TODO: переезать на fetchmany
    query += " LIMIT 10"

    return query, params


def search_movies(valid_data):
    try:
        with db_cursor() as cursor:
            cursor.execute(*make_qerry(**valid_data))
            results = cursor.fetchall()
        return results
        
    except mysql.connector.Error:
        return []


# validation stuff
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


def validate_parsed_data(movie_title, min_year, max_year, nsfw, exact_year, categories):
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

    valid_cats = []
    for cid in categories:
        if cid.isdigit():
            valid_cats.append(int(cid))
        else:
            errors.append(f"Некорректный идентификатор жанра: {cid}")

    validated = {
        "title": movie_title,
        "min_year": min_y,
        "max_year": max_y,
        "nsfw": nsfw,
        "exact_year": exact_y,
        "categories": valid_cats
    }
    return errors, validated

# server stuff
def parse_query(query):
    movie_title = query.get("movie", [""])[0]
    min_year = query.get("min_year", [None])[0]
    max_year = query.get("max_year", [None])[0]
    nsfw = query.get("nsfw", ["false"])[0].lower() == "on"
    exact_year = query.get("exact_year", [None])[0]
    categories = query.get("categories", [])
    return movie_title, min_year, max_year, nsfw, exact_year, categories


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            if parsed_path.path in ["/", "/search"]:
                all_categories = get_all_categories()
            
            # Главная страница
            if parsed_path.path == "/":
                self.send_custom_response(data=None, cats_sent={"categories": all_categories})

            # страница about
            elif parsed_path.path == "/about":
                self.send_custom_response(None, templ='about.html')
                
            # Поиск через форму и API для AJAX-запросов
            elif parsed_path.path in ["/api/search", "/search"]:
                query = parse_qs(parsed_path.query)
                movie_title, min_year, max_year, nsfw, exact_year, categories = parse_query(query)

                # Валидация
                errors, valid_data = validate_parsed_data(movie_title, min_year, max_year, nsfw, exact_year, categories)

                if errors:
                    self.send_custom_response(errors, resp_code=400, Cont_type="application/json")
                    return
                
                results = search_movies(valid_data)
                if parsed_path.path == "/api/search":
                    self.send_custom_response(results, Cont_type="application/json", api=True)
                else:
                    #all_categories = get_all_categories()
                    self.send_custom_response(results, valid_data, cats_sent={"categories": all_categories})

            # шоукейс ошибки 500
            elif parsed_path.path == "/err":
                5/0
            
            # страница 404
            else:
                self.send_custom_response(None, resp_code=404, templ='not_found.html')
        except Exception as e:
            print(f"Error: {e}")
            self.send_custom_response(e, resp_code=500, templ='error.html')

    def send_custom_response(self, data, valid_data=None, resp_code=200, Cont_type="text/html", templ='index.html', api=False, cats_sent=None):
        self.send_response(resp_code)
        self.send_header("Content-type", Cont_type)
        self.end_headers()
        
        if resp_code == 400:
            self.wfile.write(json.dumps({"errors": data}).encode("utf-8"))
        elif api:
            self.wfile.write(json.dumps(data).encode("utf-8"))
        else:
            kwargs_for_template = {"results": data, "queries": valid_data,}
            if cats_sent:
                kwargs_for_template.update(cats_sent)
            template = env.get_template(templ)
            html = template.render(**kwargs_for_template)
            self.wfile.write(html.encode("utf-8"))


if __name__ == "__main__":
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    print(f"Сервер запущен на http://{SERVER_HOST}:{SERVER_PORT}")
    httpd.serve_forever()