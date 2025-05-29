# app/tests/test_api.py
# from unittest import mock
import json
import os

import uuid

from mock import patch
from functools import wraps
from .fixtures import getPublicID, getSpecificPublicID
from flask import jsonify
from moto import mock_aws
from pathlib import Path

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


@mock_aws
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

    def test_create_user_success(self):

        # valid payload with a random UUID
        payload = {"public_id": str(uuid.uuid4())}
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            data=json.dumps(payload),
            headers=headers,
        )

        self.assertTrue(response.status_code, 201)
        self.assertTrue("User created on AWS" in response.get_data(as_text=True))

    # -----------------------------------------------------------------------------

    def test_create_user_fail_invalid_input(self):

        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            data='notjson',
            headers=headers,
        )

        self.assertTrue(response.status_code, 400)
        self.assertTrue("Check ya inputs mate. Yer not valid, Jason" in response.get_data(as_text=True))

    # -----------------------------------------------------------------------------

    def test_create_user_fail_json_schema_check_1(self):

        payload = {"validjson": "some stuff"}
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            data=json.dumps(payload),
            headers=headers,
        )

        self.assertTrue(response.status_code, 400)
        returned_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(returned_data['message'], "Check ya inputs mate.")
        self.assertEqual(returned_data['error'], "Additional properties are not allowed ('validjson' was unexpected)")

    # -----------------------------------------------------------------------------

    def test_create_user_fail_json_schema_check_2(self):

        payload = {"public_id": "not a uuid"}
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            data=json.dumps(payload),
            headers=headers,
        )

        self.assertTrue(response.status_code, 400)
        returned_data = json.loads(response.get_data(as_text=True))
        self.assertEqual(returned_data['message'], "Check ya inputs mate.")
        self.assertEqual(returned_data['error'], "'not a uuid' is too short")

    # -----------------------------------------------------------------------------

    def test_create_user_fail_missing_standard_policy_file(self):

        # rename the standardpolicy file so the api call fails
        mod_path = Path(__file__).parent
        relpath = '../main/standardpolicy.txt'
        renamed = '../main/_standardpolicy.txt'
        relative_filepath = (mod_path / relpath).resolve()
        renamed_filepath = (mod_path / renamed).resolve()

        if Path.exists(relative_filepath):
            os.rename(relative_filepath, renamed_filepath)

        # valid payload with a random UUID
        payload = {"public_id": str(uuid.uuid4())}
        headers = { 'Content-type': 'application/json', 'x-access-token': 'somefaketoken' }
        response = self.client.post(
            "/aws/user",
            data=json.dumps(payload),
            headers=headers,
        )

        self.assertTrue(response.status_code, 500)
        self.assertTrue("Failed to create user on AWS" in response.get_data(as_text=True))

        os.rename(renamed_filepath, relative_filepath)