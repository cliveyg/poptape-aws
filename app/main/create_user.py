# app/main/create_user.py
from app import db
from app.models import AwsDetails 
from flask import current_app as app
import boto3
from botocore.client import Config
import os
import logging
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from botocore.exceptions import ClientError
import time

# a better hashing ting
from cryptography.fernet import Fernet

# -----------------------------------------------------------------------------

def create_aws_user(public_id):

    collection_name = 'z'+public_id.replace('-','')

    app.logger.debug("In create_aws_user function")

    #------------------------------------
    # personalise policy

    policy_data = None
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    #TODO: put this in separate function and/or get it from the db
    try:
        filepath = os.path.join(os.path.dirname(__file__), 'standardpolicy.txt')
        file = open(filepath, 'r')
        policy_data = file.read()
    except OSError as e:
        app.logger.error('Failed to open and/or read aws standard policy template. Check it exists and permissions are correct.')
        return False
    
    policy_data = policy_data.replace('XXXXXX',collection_name)

    app.logger.debug("Read standard policy text file")

    #------------------------------------
    # create user
    
    create_response = None
    app.logger.debug("Attempting to create iam user")
    try:
        create_response = app.iam.create_user(UserName=collection_name)
    except ClientError as e:
        app.logger.error('Failed to create AWS user: '+str(e))
        return False

    if create_response['ResponseMetadata']['HTTPStatusCode'] !=  200:
        app.logger.error('Problem creating AWS user. Status code is ['+create_response.status_code+']')
        return False

    app.logger.debug("user created ✓")

    #------------------------------------
    # set policy for user
    #TODO: get policy name from config/.env

    try:
        policy_response = app.iam.put_user_policy(
            UserName = collection_name,
            PolicyName = 'poptape_aws_standard_user_policy',
            PolicyDocument = policy_data
        )
    except ClientError as e:
        app.logger.error('Failed to create policy for AWS user: '+str(e))
        return False

    if policy_response['ResponseMetadata']['HTTPStatusCode'] !=  200:
        app.logger.error('Problem creating policy for AWS user. Status code is ['+policy_response.status_code+']')
        return False

    app.logger.debug("policy set for user ✓")

    #------------------------------------
    # create access key for user
    
    try:
        key_response = app.iam.create_access_key(UserName = collection_name)
    except ClientError as e:
        app.logger.error('Failed to create access key for AWS user: '+str(e))
        return False    
    
    if key_response['ResponseMetadata']['HTTPStatusCode'] != 200:
        app.logger.error('Problem creating access key for AWS user. \
                         Status code is ['+key_response.status_code+']')
        return False

    app.logger.debug("access key created for user ✓")

    #------------------------------------
    # create s3 bucket and add bucket policy to it

    try:
        filepath = os.path.join(os.path.dirname(__file__), 'bucket_policy.txt')
        file = open(filepath, 'r')
        bucket_policy = file.read()
    except OSError as e:
        app.logger.error('Failed to open and/or read bucket policy template. Check it exists and permissions are correct.')
        return False

    bucket_policy = bucket_policy.replace('XXXXXX',collection_name)
    bucket_policy = bucket_policy.replace('AAAAAA',create_response['User']['Arn'])

    app.logger.debug("attempting to create a bucket")

    try:
        buck_resp = app.s3.create_bucket(Bucket = collection_name.lower()) 
        #app.s3.put_bucket_policy(Bucket = collection_name.lower(), Policy = bucket_policy)
    except ClientError as e:
        app.logger.error('Failed to create bucket for AWS user: '+str(e))
        return False

    if buck_resp['ResponseMetadata']["HTTPStatusCode"] != 200:
        app.logger.error("Could not create bucket [%s] for user", collection_name.lower())
        return False

    app.logger.debug("bucket created for user ✓")
    #TODO: fix this - the delay is here as AWS says bucket created ok but sometimes
    #      when we try and create a bucket afterwards AWS says bucket doesn't exist.
    #      this is caused by the length of time AWS takes to propogate the new bucket
    #      info in it's systems. waiting whilst hacky and bad ux should help
    time.sleep(2)
    app.logger.debug("attempting to update bucket settings...")

    try:
        app.s3.delete_public_access_block(
            Bucket = collection_name.lower(),
            ExpectedBucketOwner = app.config['AWS_ACCOUNT_ID'],
        )
    except ClientError as e:
        app.logger.error('Failed to update bucket settings: '+str(e))
        return False
    app.logger.debug("updated bucket settings ✓")

    time.sleep(2)
    app.logger.debug("attempting to create a bucket policy")

    try:
        app.s3.put_bucket_policy(Bucket = collection_name.lower(), Policy = bucket_policy)
    except ClientError as e:
        app.logger.error('Failed to create bucket policy: '+str(e))
        return False        

    app.logger.debug("bucket policy created ✓")

    #------------------------------------
    # add cors policy to bucket
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'PUT', 'POST'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['GET', 'PUT', 'POST'],
            'MaxAgeSeconds': 300000
        }]
    }

    try:
        app.s3.put_bucket_cors(Bucket = collection_name.lower(),
                               CORSConfiguration = cors_configuration)
    except ClientError as e:
        app.logger.error('Failed to create cors config for bucket [%s]: %s',
                         collection_name,
                         str(e))
        return False
    
    app.logger.debug("cors config added to bucket ✓")

    #------------------------------------------------
    # save user after everything has completed okay
    #------------------------------------------------
    cipher_suite = Fernet(app.config['FERNET_KEY'])
    aws_AccessKeyId = cipher_suite.encrypt(key_response['AccessKey']['AccessKeyId'].encode('utf-8'))
    aws_SecretAccessKey = cipher_suite.encrypt(key_response['AccessKey']['SecretAccessKey'].encode('utf-8'))

    aws_user = AwsDetails(public_id = public_id,
                          aws_CreateUserRequestId = create_response['ResponseMetadata']['RequestId'],
                          aws_UserId = create_response['User']['UserId'],
                          aws_CreateDate = create_response['User']['CreateDate'],
                          aws_UserName = create_response['User']['UserName'],
                          aws_AccessKeyId = aws_AccessKeyId.decode('utf-8'),
                          aws_SecretAccessKey = aws_SecretAccessKey.decode('utf-8'),
                          aws_PolicyName = 'poptape_aws_standard_user_policy',
                          aws_Arn = create_response['User']['Arn'])
    try:
        db.session.add(aws_user)
        db.session.commit()
    except (SQLAlchemyError, DBAPIError) as e:
        db.session.rollback()
        app.logger.error('Database says no!:\n'+str(e))
        return False

    app.logger.debug("user saved in aws db ✓")

    return True

# -----------------------------------------------------------------------------

def create_presigned_url(bucket_name, object_name, expiration, public_id):

    aws_details = AwsDetails.query.filter_by(public_id=public_id).first()

    if not aws_details:
        return None

    # get access keys
    cipher_suite = Fernet(app.config['FERNET_KEY'])
    aws_AccessKeyId = cipher_suite.decrypt(aws_details.aws_AccessKeyId.encode('utf-8'))
    aws_SecretAccessKey = cipher_suite.decrypt(aws_details.aws_SecretAccessKey.encode('utf-8'))
  
    aws_AccessKeyId = aws_AccessKeyId.decode('utf-8')
    aws_SecretAccessKey = aws_SecretAccessKey.decode('utf-8')

    try:
        s3 = boto3.client('s3',
                          region_name='us-east-1',
                          aws_access_key_id=aws_AccessKeyId,
                          aws_secret_access_key=aws_SecretAccessKey,
                          config=Config(signature_version='s3v4'))

        #object_name = object_name + ".jpeg"

        response = s3.generate_presigned_post(bucket_name,
                                              object_name,
                                              Fields=None,
                                              Conditions=None,
                                              ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # response contains the presigned URL
    return response
