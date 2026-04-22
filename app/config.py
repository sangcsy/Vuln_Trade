import os


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    DB_HOST = os.getenv("DB_HOST", "db")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("MYSQL_DATABASE", "vulntrade")
    DB_USER = os.getenv("MYSQL_USER", "vulntrade")
    DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "vulntrade123")
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "src", "static", "uploads")
