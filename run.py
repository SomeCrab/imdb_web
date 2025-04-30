from core.logger import setup_logging
from app.server import run_server

def main():
    setup_logging()
    run_server()

if __name__ == "__main__":
    main()