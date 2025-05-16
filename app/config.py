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
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION')
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')

class TestConfig(Config):
    FOTO_LIMIT_PER_PAGE = "2"
    LOG_LEVEL = "DEBUG"

