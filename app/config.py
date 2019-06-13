# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    # set app configs
    SECRET_KEY = os.getenv('SECRET_KEY')
    CHECK_ACCESS_URL = os.getenv('CHECK_ACCESS_URL')
    FOTO_LIMIT_PER_PAGE = os.getenv('ADDRESS_LIMIT_PER_PAGE')
    LOG_FILENAME = os.getenv('LOG_FILENAME')
    LOG_LEVEL = os.getenv('LOG_LEVEL')
    FERNET_KEY = os.getenv('FERNET_KEY')
    MONGO_AUTH_SOURCE = os.getenv('MONGO_AUTH_SOURCE')
    MONGO_HOST = os.getenv('MONGO_HOST')
    MONGO_PORT = os.getenv('MONGO_PORT')
    MONGO_USERNAME = os.getenv('MONGO_POPTAPE_ITEMS_USER')
    MONGO_PASSWORD = os.getenv('MONGO_POPTAPE_ITEMS_PASS')
    MONGO_DBNAME = os.getenv('MONGO_DBNAME')
    MONGO_CONNECT = os.getenv('MONGO_CONNECT')
    MONGO_URI = os.getenv('MONGO_URI')

class TestConfig(Config):
    FOTO_LIMIT_PER_PAGE = "2"
    LOG_LEVEL = "DEBUG"

