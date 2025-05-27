import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True, scope="session")
def patch_access_level_and_external():
    # Patch require_access_level in both its definition and usage locations
    with patch("app.decorators.require_access_level", lambda *a, **kw: (lambda f: f)), \
            patch("app.main.views.require_access_level", lambda *a, **kw: (lambda f: f)), \
            patch("app.extensions.boto3.client") as boto3_client, \
            patch("requests.post") as req_post, \
            patch("requests.get") as req_get:
        # Mock boto3 client
        s3_mock = MagicMock()
        s3_mock.create_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_policy.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_cors.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.delete_public_access_block.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        boto3_client.return_value = s3_mock
        # Mock requests
        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {'success': True, 'user_id': 'test-user'}
        req_post.return_value = fake_resp
        req_get.return_value = fake_resp
        yield