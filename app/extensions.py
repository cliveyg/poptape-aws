# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_uuid import FlaskUUID
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
import os

# -----------------------------------------------------------------------------
# set up rate limiting
limiter = Limiter(key_func=get_remote_address,
                  default_limits=["50 per minute", "5 per second"])

# -----------------------------------------------------------------------------
# set up flask uuid regex in url finder
flask_uuid = FlaskUUID()

# -----------------------------------------------------------------------------
# set up SQL alchemy
db = SQLAlchemy()

# -----------------------------------------------------------------------------
# c r e a t e    a m a z o n    b o t o    c l i e n t 
# -----------------------------------------------------------------------------

def create_aws_client(service):

    # setup aws
    try:
        aws = boto3.client(service,
                           aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                           aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                           config=Config(signature_version='s3v4'))
    except ClientError as e:
        return None, e
    
    return aws, None

# -----------------------------------------------------------------------------
