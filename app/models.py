# app/models.py
from app import db
import datetime

#-----------------------------------------------------------------------------#
# models match to tables in postgres
#-----------------------------------------------------------------------------#

class AwsDetails(db.Model):

    __tablename__ = 'aws_details'

    public_id = db.Column(db.String(36), primary_key=True, nullable=False)
    aws_CreateUserRequestId = db.Column(db.String(300))
    aws_UserId = db.Column(db.String(300), unique=True)
    aws_UserName = db.Column(db.String(300), unique=True)
    aws_AccessKeyId = db.Column(db.String(300), unique=True)
    aws_SecretAccessKey = db.Column(db.String(300), unique=True)
    aws_PolicyName = db.Column(db.String(100))
    aws_Arn = db.Column(db.String(500), unique=True)
    aws_CreateDate = db.Column(db.TIMESTAMP(), nullable=False)
