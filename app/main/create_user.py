# app/main/create_user.py
#import botocore.client
from app import db
from app.models import AwsDetails 
from flask import current_app as app

import os
import logging
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from botocore.exceptions import ClientError

# a better hashing ting
from cryptography.fernet import Fernet

def create_aws_user(public_id):

    collection_name = 'Z'+public_id.replace('-','')
    app.logger.debug('Creating AWS user ['+collection_name+']...')

    #------------------------------------
    # personalise policy

    policy_data = None
    
    try:
        filepath = os.path.join(os.path.dirname(__file__), 'standardpolicy.txt')
        file = open(filepath, 'r')
        policy_data = file.read()
    except OSError as e:
        app.logger.error('Failed to open and/or read aws standard policy template. Check it exists and permissions are correct.')
        return False
    
    policy_data = policy_data.replace('XXXXXX',collection_name)

    #app.logger.debug('Opened standardpolicy.txt...')

    #------------------------------------
    # create user
    
    create_response = None

    try:
        create_response = app.iam.create_user(UserName=collection_name)
    except ClientError as e:
        app.logger.error('Failed to create AWS user: '+str(e))
        return False

    if create_response['ResponseMetadata']['HTTPStatusCode'] !=  200:
        app.logger.debug('Problem creating AWS user. Status code is ['+create_response.status_code+']')
        return False

    app.logger.debug('AWS user ['+collection_name+'] created for user ['+public_id+']')
    app.logger.debug('AWS Response is '+str(create_response))

    #------------------------------------
    # set policy for user

    try:
        policy_response = app.iam.put_user_policy(
            UserName=collection_name,
            PolicyName='poptape_aws_standard_user_policy',
            PolicyDocument=policy_data
        )
    except ClientError as e:
        app.logger.error('Failed to create policy for AWS user: '+str(e))
        app.logger.error('Policy document is:\n'+policy_data) 
        return False

    if policy_response['ResponseMetadata']['HTTPStatusCode'] !=  200:
        app.logger.info('Problem creating policy for AWS user. Status code is ['+policy_response.status_code+']')
        return False

    app.logger.debug('AWS policy created for AWS user ['+collection_name+']')

    #------------------------------------
    # create access key for user
    
    try:
        key_response = app.iam.create_access_key(UserName=collection_name)
    except ClientError as e:
        app.logger.error('Failed to create access key for AWS user: '+str(e))
        return False    
    
    if key_response['ResponseMetadata']['HTTPStatusCode'] !=  200:
        app.logger.info('Problem creating access key for AWS user. \
                         Status code is ['+key_response.status_code+']')
        return False

    cipher_suite = Fernet(app.config['FERNET_KEY'].encode('utf-8'))
    aws_AccessKeyId = cipher_suite.encrypt(key_response['AccessKey']['AccessKeyId'].encode('utf-8'))
    aws_SecretAccessKey = cipher_suite.encrypt(key_response['AccessKey']['SecretAccessKey'].encode('utf-8'))
   
    app.logger.debug('AWS access key created for AWS user ['+collection_name+']')

    aws_user = AwsDetails(public_id = public_id,
                          aws_CreateUserRequestId = create_response['ResponseMetadata']['RequestId'],
                          aws_UserId = create_response['User']['UserId'],
                          aws_CreateDate = create_response['User']['CreateDate'],
                          aws_UserName = create_response['User']['UserName'],
                          aws_AccessKeyId = aws_AccessKeyId,
                          aws_SecretAccessKey = aws_SecretAccessKey,
                          aws_PolicyName = 'poptape_aws_standard_user_policy',
                          aws_Arn = create_response['User']['Arn'])
    try:
        db.session.add(aws_user)
        db.session.commit()
    except (SQLAlchemyError, DBAPIError) as e:
        db.session.rollback()
        app.logger.error('Database says no!:\n'+str(e))
        return False 

    app.logger.debug('AWS data successfully created for user ['+public_id+']')

    #------------------------------------
    # create s3 folder/object

    return True

