# app/main/views.py
from app import db, limiter, flask_uuid
from flask import jsonify, request, abort, url_for
from flask import current_app as app
from app.main import bp
from app.main.create_user import create_aws_user, create_presigned_url
from app.models import AwsDetails 
from app.decorators import require_access_level, microservice_only
from app.assertions import assert_valid_schema
from jsonschema.exceptions import ValidationError as JsonValidationError
import uuid
from urllib.parse import unquote

# reject any non-json requests
@bp.before_request
def only_json():
    if not request.is_json:
        return jsonify({ 'message': 'Input must be json'}), 400

# -----------------------------------------------------------------------------
# create aws user
@bp.route('/aws/user', methods=['POST'])
@limiter.limit("100/minute")
#TODO: fix circular calls about access level
#WARNING: fix this
#@require_access_level(10, request)
#def create_user_on_aws(public_id, request):
def create_user_on_aws():

    app.logger.info("arrived at /aws/user create_user_on_aws route")

    # check input is valid json
    try:
        data = request.get_json()
    except:
        return jsonify({ 'message': 'Check ya inputs mate. Yer not valid, Jason'}), 400

    # validate input against json schemas
    try:
        assert_valid_schema(data, 'uuid')
    except JsonValidationError as err:
        return jsonify({ 'message': 'Check ya inputs mate.', 'error': err.message }), 400

    public_id = data['public_id']

    if create_aws_user(public_id):
        return jsonify({ 'message': 'User created on AWS' }), 201

    return jsonify({ 'message': 'Failed to create user on AWS' }), 500

# -----------------------------------------------------------------------------
# get aws user details
@bp.route('/aws/user', methods=['GET'])
@limiter.limit("100/minute")
@require_access_level(10, request)
def get_user_detail(public_id, request):

    aws_details = AwsDetails.query.filter_by(public_id=public_id).first()

    if not aws_details:
        return jsonify({ 'message': 'Where dey gone' }), 404

    user_data = {}
    user_data['public_id'] = aws_details.public_id
    user_data['aws_CreateUserRequestId'] = aws_details.aws_CreateUserRequestId
    user_data['aws_UserId'] = aws_details.aws_UserId
    user_data['aws_UserName'] = aws_details.aws_UserName
    user_data['aws_AccessKeyId'] = aws_details.aws_AccessKeyId
    user_data['aws_SecretAccessKey'] = aws_details.aws_SecretAccessKey
    user_data['aws_PolicyName'] = aws_details.aws_PolicyName
    user_data['aws_Arn'] = aws_details.aws_Arn
    user_data['aws_CreateDate'] = aws_details.aws_CreateDate

    return jsonify(user_data)

# -----------------------------------------------------------------------------
# get aws user details for particular user
@bp.route('/aws/user/<user_id>', methods=['GET'])
@limiter.limit("10/minute")
@require_access_level(5, request)
def get_user_details_by_admin(public_id, request, user_id):

    aws_details = AwsDetails.query.filter_by(public_id=user_id).first()

    if not aws_details:
        return jsonify({ 'message': 'Where dey gone' }), 404

    user_data = {}
    user_data['public_id'] = aws_details.public_id
    user_data['aws_CreateUserRequestId'] = aws_details.aws_CreateUserRequestId
    user_data['aws_UserId'] = aws_details.aws_UserId
    user_data['aws_UserName'] = aws_details.aws_UserName
    user_data['aws_PolicyName'] = aws_details.aws_PolicyName
    user_data['aws_Arn'] = aws_details.aws_Arn
    user_data['aws_CreateDate'] = aws_details.aws_CreateDate

    return jsonify(user_data)

# -----------------------------------------------------------------------------
# generate presigned urls
@bp.route('/aws/urls', methods=['POST'])
@limiter.limit("100/minute")
@require_access_level(10, request)
def generate_presigned_urls(public_id, request):

    # check input is valid json
    try:
        data = request.get_json()
    except:
        return jsonify({ 'message': 'Check ya inputs mate. Yer not valid, Jason'}), 400

    # validate input against json schemas
    try:
        assert_valid_schema(data, 'urls')
    except JsonValidationError as err:
        return jsonify({ 'message': 'Check ya inputs mate.', 'error': err.message }), 400

    objects = data['objects']
    expiration = 3600 #TODO: put this in .env
    collection_name = 'z'+public_id.replace('-','')
    bucket_name = collection_name.lower()
    urls = []

    for object_id in objects:
        resp = None
        response = {}
        resp = create_presigned_url(bucket_name, object_id, expiration, public_id)
        if resp:
            response['foto_id'] = object_id
            response['fields']  = resp['fields']
            #response[object_id] = resp    
            urls.append(response)

    return jsonify({ 'aws_urls': urls }), 201

# -----------------------------------------------------------------------------
# helper route - useful for checking status of api in api_server application

@bp.route('/aws/status', methods=['GET'])
@limiter.limit("100/hour")
def system_running():
    app.logger.info("Praise the FSM! The sauce is ready")
    return jsonify({ 'message': 'System running...' }), 200

# -----------------------------------------------------------------------------
# route for testing rate limit works - generates 429 if more than two calls
# per minute to this route - restricted to admin users and above
@bp.route('/aws/admin/ratelimited', methods=['GET'])
@require_access_level(5, request)
@limiter.limit("0/minute")
def rate_limted(public_id, request):
    return jsonify({ 'message': 'should never see this' }), 200

# -----------------------------------------------------------------------------
# route for returning all routes on microservice

@bp.route('/aws', methods=['GET'])
def sitemap():

    output = []
    for rule in app.url_map.iter_rules():

        options = {}
        for arg in rule.arguments:
            options[arg] = "<{0}>".format(arg)

        url = url_for(rule.endpoint, **options)
        methods = list(rule.methods)
        if "static" not in url and "rate" not in url:
            output.append({ 'url': unquote(url), 'methods': methods })

    return jsonify({ 'endpoints': output }), 200
