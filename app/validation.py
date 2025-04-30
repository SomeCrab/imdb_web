from configs.app_config import MIN_ALLOWED_YEAR, MAX_ALLOWED_YEAR
import logging
from inspect import stack

logger = logging.getLogger(__name__)

def validate_year(value, name):
    """
    Преобразует строку в int и проверяет, что год в [YEAR_MIN, YEAR_MAX].
    Возвращает (год, сообщение об ошибке).
    """
    if not value:
        return None, None
    try:
        year = int(value)
    except ValueError as e:
        logger.debug(f"Inside '{stack()[0][3]}', value '{name}': {value} != 'int' :{e}")
        return None, f"Некорректный формат '{name}': {value}"
    if not (MIN_ALLOWED_YEAR <= year <= MAX_ALLOWED_YEAR):
        logger.debug(f"Inside '{stack()[0][3]}', value '{name}': {value} out of range")
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
        logger.debug(f"Inside '{stack()[0][3]}', пользователь пытается вводить данные прямо в query")
        errors.append("Нельзя указывать конкретный год вместе с диапазоном")

    if exact_y is None and min_y is not None and max_y is not None:
        if min_y > max_y:
            logger.debug(f"Inside '{stack()[0][3]}', не корректно {min_y} > {max_y}")
            errors.append("Минимальный год должен быть меньше максимального года")

    valid_cats = []
    for cid in categories:
        if cid.isdigit():
            valid_cats.append(int(cid))
        else:
            logger.debug(f"Inside '{stack()[0][3]}', id {cid} must be 'int' not {type(cid)}")
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