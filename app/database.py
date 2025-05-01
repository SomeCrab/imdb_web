import mysql.connector
from contextlib import contextmanager
from configs.app_config import DB_CONFIG, STATS_DB_NAME
import logging
from inspect import stack
from hashlib import md5

logger = logging.getLogger(__name__)


@contextmanager
def db_cursor(dictionary=True):
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=dictionary)
        yield cursor
        connection.commit()
    except mysql.connector.Error as e:
        if connection:
            connection.rollback()
        logger.error(f"Ошибка MySQL в '{stack()[0][3]}': %s", e)
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
    except Exception as e:
        logger.error(f"Inside '{stack()[0][3]}' :{e}")
        return []


def make_qerry(
        title=None,
        min_year=None,
        max_year=None,
        nsfw=False,
        exact_year=None,
        categories=None,
        limit=None
    ):
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
    
    if limit is not None:
        query += " LIMIT %s"
        params.append(limit)

    return query, params


# TODO: bring it out to debug_utils.py
def _set_counter(query, new_count):
    query_hash = md5(query.encode()).hexdigest()
    
    with db_cursor() as cursor:
        cursor.execute(f"""
            UPDATE {STATS_DB_NAME}.popular_searches
            SET counter = %s
            WHERE query_hash = %s
        """, (new_count, query_hash))
        logger.info(f"Updated {query} to {new_count}")


# _set_counter("/search?movie=lexx&exact_year=", 150500)
# _set_counter("/search?movie=griechische&exact_year=", 500)
# _set_counter("/search?movie=monkeyshines&exact_year=", 40)


def log_search(query, title= "Many results"):
    try:
        query_hash = md5(query.encode()).hexdigest()
        
        with db_cursor() as cursor:
            cursor.execute(f"""
                INSERT INTO {STATS_DB_NAME}.popular_searches
                (query_hash, search_query, title, counter)
                VALUES (%s, %s, %s, 1) AS new
                ON DUPLICATE KEY UPDATE
                    title = new.title,
                    counter = popular_searches.counter + 1
            """, (query_hash, query, title.lower().capitalize()))
    except Exception as e:
        logger.error(f"Inside '{stack()[0][3]}' :{e}")
        return []


def get_popular_searches(limit=10):
    try:
        with db_cursor() as cursor:
            cursor.execute(f"""
                SELECT search_query, counter, title
                FROM {STATS_DB_NAME}.popular_searches
                ORDER BY counter DESC
                LIMIT %s
            """, (limit,))
            return cursor.fetchall()
    except mysql.connector.Error as e:
        logger.error(f"Inside '{stack()[0][3]}' :{e}")
        return []


def search_movies(valid_data):
    try:
        with db_cursor() as cursor:
            cursor.execute(*make_qerry(**valid_data))
            results = cursor.fetchall()
        return results
        
    except Exception as e:
        logger.error(f"Inside '{stack()[0][3]}' :{e}")
        return []