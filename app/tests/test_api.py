# app/tests/test_api.py
# from unittest import mock
import uuid
import pytest

from mock import patch, MagicMock
from functools import wraps
from .fixtures import getPublicID, getSpecificPublicID
from flask import jsonify
from moto import mock_iam, mock_s3

import datetime

# have to mock the require_access_level decorator here before it
# gets attached to any classes or functions


def mock_dec(access_level, request):
    def actual_decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):

            token = request.headers.get('x-access-token')

            if not token:
                return jsonify({'message': 'Naughty one!'}), 401
            pub_id = getSpecificPublicID()
            return f(pub_id, request, *args, **kwargs)

        return decorated
    return actual_decorator


patch('app.decorators.require_access_level', mock_dec).start()

# from app import create_app, db
from app import create_app, db
from app.config import TestConfig
from flask_testing import TestCase as FlaskTestCase


###############################################################################
#                         flask test case instance                            #
###############################################################################

def is_valid_uuid(uuid_to_test, version=4):
    try:
        # check for validity of Uuid
        uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True

class MyTest(FlaskTestCase):

    def create_app(self):
        app = create_app(TestConfig)
        return app

        def setUp(self):
            db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

###############################################################################
#                                tests                                        #
###############################################################################

    def test_status_ok(self):
        headers = { 'Content-type': 'application/json' }
        response = self.client.get('/aws/status', headers=headers)
        self.assertEqual(response.status_code, 200)

    # -----------------------------------------------------------------------------

    def test_404(self):
        # this behaviour is slightly different to live as we've mocked the
        headers = { 'Content-type': 'application/json' }
        response = self.client.get('/aws/resourcenotfound', headers=headers)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.is_json)

    # -----------------------------------------------------------------------------

    def test_api_rejects_html_input(self):
        headers = { 'Content-type': 'text/html' }
        response = self.client.get('/aws/status', headers=headers)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.is_json)

    # -----------------------------------------------------------------------------

    def test_wrong_method_error_returns_json(self):
        headers = { 'Content-type': 'application/json' }
        response = self.client.post('/aws/status', json={ 'test': 1 }, headers=headers)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.is_json)

    # -----------------------------------------------------------------------------

    def test_generate_presigned_urls_invalid_json(self):
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post('/aws/urls', data="notjson", headers=headers)
        self.assertEqual(response.status_code, 400)

    # -----------------------------------------------------------------------------

    #def test_create_user_success(self):
    #    pub_id = str(uuid.uuid4())
    #    payload = {'public_id': pub_id}
    #    headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
    #    with patch('app.main.create_user.create_aws_user', return_value=True):
    #        response = self.client.post('/aws/user', json=payload, headers=headers)
    #        self.assertEqual(response.status_code,201)
    #        data = response.get_json()
    #        self.assertEqual(pub_id, data.get('public_id'))

    @mock_iam
    @mock_s3
    def test_create_user_with_moto(self):
        # Setup moto-mocked IAM and S3
        iam = boto3.client("iam", region_name="us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")

        # Prepare valid payload with a random UUID
        payload = {"public_id": str(uuid.uuid4())}
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            json=payload,
            headers=headers,
        )

        self.assertTrue(response.status_code, 201)
        self.assertTrue(response.get('message'), "User created on AWS"
