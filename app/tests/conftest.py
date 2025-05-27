import pytest
import sys
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True, scope="session")
def patch_everything_before_app():
    # Patch decorators and schema validation before any app/main/views import
    import importlib

    # Patch require_access_level and assert_valid_schema everywhere
    with patch("app.decorators.require_access_level", lambda *a, **kw: (lambda f: f)), \
            patch("app.main.views.require_access_level", lambda *a, **kw: (lambda f: f)), \
            patch("app.assertions.assert_valid_schema", lambda data, schema: True):

        # Remove views from sys.modules to force re-import with patched decorator
        if "app.main.views" in sys.modules:
            del sys.modules["app.main.views"]
        importlib.import_module("app.main.views")
        yield

@pytest.fixture(autouse=True)
def patch_s3_and_requests():
    with patch("app.extensions.boto3.client") as boto3_client, \
            patch("requests.post") as req_post, \
            patch("requests.get") as req_get:
        s3_mock = MagicMock()
        boto3_client.return_value = s3_mock
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {'success': True, 'user_id': 'test-user'}
        req_post.return_value = fake_resp
        req_get.return_value = fake_resp
        yield