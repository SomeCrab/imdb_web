from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import logging
from inspect import stack
from jinja2 import Environment, FileSystemLoader
from configs.app_config import TEMPLATES_DIR
from app.database import get_all_categories, search_movies
from app.validation import validate_parsed_data

logger = logging.getLogger(__name__)
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


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
                1/0
                
            # страница 404
            else:
                logger.debug(f"User tried to load '{parsed_path.path}'")
                self.send_custom_response(None, resp_code=404, templ='not_found.html')

        except Exception as e:
            logger.error(f"Inside '{stack()[0][3]}' :{e}")
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
