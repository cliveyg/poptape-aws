from flask import Flask
from flask_migrate import Migrate
from app.extensions import limiter, db, flask_uuid
from app.extensions import create_aws_client
from app.config import Config
from app.errors import handle_429_request, handle_wrong_method, handle_not_found

import logging
from logging.handlers import RotatingFileHandler

def create_app(config_class=Config):

    app = Flask(__name__)
    # set app configs
    app.config.from_object(config_class)

    # initial flask extensions
    limiter.init_app(app)
    flask_uuid.init_app(app)
    db.init_app(app)
    migrate = Migrate(app, db)
    migrate.init_app(app, db)

    # blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # register custom errors
    app.register_error_handler(429, handle_429_request)
    app.register_error_handler(405, handle_wrong_method)
    app.register_error_handler(404, handle_not_found)

    # logging stuff
    formatter = logging.Formatter("[%(asctime)s] [%(pathname)s:%(lineno)d] %(levelname)s - %(message)s")
    handler = RotatingFileHandler(app.config['LOG_FILENAME'], maxBytes=10000000, backupCount=5)
    log_level = app.config['LOG_LEVEL']

    if log_level == 'DEBUG': # pragma: no cover
        app.logger.setLevel(logging.DEBUG) # pragma: no cover
    elif log_level == 'INFO': # pragma: no cover
        app.logger.setLevel(logging.INFO) # pragma: no cover
    elif log_level == 'WARNING': # pragma: no cover
        app.logger.setLevel(logging.WARNING) # pragma: no cover
    elif log_level == 'ERROR': # pragma: no cover
        app.logger.setLevel(logging.ERROR) # pragma: no cover
    else: # pragma: no cover
        app.logger.setLevel(logging.CRITICAL) # pragma: no cover

    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # aws stuff
    iam, iam_error = create_aws_client("iam")
    if iam_error:
        app.logger.error("Could not create AWS 'iam' client [%s]", str(iam_error))
    app.iam = iam

    s3, s3_error = create_aws_client("s3")
    if s3_error:
        app.logger.error("Could not create AWS 's3' client [%s]", str(s3_error))
    app.s3 = s3

    return app

