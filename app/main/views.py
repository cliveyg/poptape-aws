# app/main/views.py
from app import db, limiter, flask_uuid
from flask import jsonify, request, abort, url_for
from flask import current_app as app
from app.main import bp
from app.main.create_user import create_aws_user
from app.decorators import require_access_level, microservice_only
from app.assertions import assert_valid_schema
from jsonschema.exceptions import ValidationError as JsonValidationError
import uuid

# reject any non-json requests
@bp.before_request
def only_json():
    if not request.is_json:
        return jsonify({ 'message': 'Input must be json'}), 400

# -----------------------------------------------------------------------------
# create aws user
@bp.route('/aws/user', methods=['POST'])
@limiter.limit("100/minute")
@require_access_level(10, request)
def create_user_on_aws(public_id, request):

    if create_aws_user(public_id):
        return jsonify({ 'message': 'User created on AWS' }), 201

    return jsonify({ 'message': 'Failed to create user on AWS' }), 500

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

