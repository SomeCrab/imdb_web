# Movie Search Engine

Web application for searching movies with various filtering capabilities.
The project includes a request logging system and displays popular search queries.

## Project Description

The application allows you to:
- Search movies by title, release year, and genres
- Exclude adult content (NSFW)
- View popular search statistics
- Work via both web interface and API

## Features

**Key capabilities:**
- Partial title match search
- Filter by year range or exact year
- Exclude NC-17 rated content
- Selection from 16 genres
- Top popular search queries
- Responsive web interface

## Technologies

**Tech stack:**
- Python 3.12.4
- Python http.server module
- Python logging module
- Jinja2 module
- MySQL


## Structure

```bash
project_root/
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── handler.py
│   ├── server.py
│   └── validation.py
├── logs/
│   ├── app_config.py
│   └── logging_config/
│       └── config.json
├── core/
│   ├── __init__.py
│   └── logger.py
├── templates/
│   ├── about.html
│   ├── base.html
│   ├── error.html
│   ├── index.html
│   └── not_found.html
├── .env
├── .gitignore
├── docker-compose.yml
├── dockerfile
├── README.md
├── requirements.txt
└── run.py
```

## Dependencies

**Required packages:**
Contained in `requirements.txt`

## Installation

**Step-by-step guide:**
```bash
git clone https://github.com/SomeCrab/imdb_web
pip install -r requirements.txt
# Set up database configuration in .env file
python run.py
```
You're awesome!
