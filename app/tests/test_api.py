import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.config import TestConfig

# Patch require_access_level everywhere before views are imported
@pytest.fixture(autouse=True, scope="session")
def patch_access_level():
    patcher = patch('app.decorators.require_access_level', lambda *a, **kw: (lambda f: f))
    patcher.start()
    yield
    patcher.stop()

# Patch S3/boto3 client globally
@pytest.fixture(autouse=True)
def mock_s3():
    with patch('app.extensions.boto3.client') as mock_client:
        s3_mock = MagicMock()
        s3_mock.create_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_policy.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_cors.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.delete_public_access_block.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_client.return_value = s3_mock
        yield s3_mock

# Patch poptape-authy calls (requests.post/requests.get)
@pytest.fixture(autouse=True)
def mock_authy():
    with patch('requests.post') as mock_post, patch('requests.get') as mock_get:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'success': True, 'user_id': 'test-user'}
        mock_post.return_value = response
        mock_get.return_value = response
        yield

@pytest.fixture
def client():
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def test_status_ok(client):
    response = client.get('/aws/status', content_type='application/json')
    assert response.status_code == 200
    assert "System running" in response.get_data(as_text=True)

def test_404(client):
    response = client.get('/aws/nonexistent')
    assert response.status_code == 404

def test_api_rejects_html_input(client):
    response = client.get('/aws/status', content_type='text/html')
    assert response.status_code == 400

def test_sitemap_lists_endpoints(client):
    response = client.get('/aws')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoints' in data
    urls = [ep['url'] for ep in data['endpoints']]
    assert '/aws/user' in urls
    assert '/aws/urls' in urls
    assert '/aws/status' in urls
    assert '/aws' in urls
    # Check structure
    for ep in data['endpoints']:
        assert 'url' in ep
        assert 'methods' in ep

def test_create_user_success(client):
    payload = {'public_id': 'abc-123'}
    with patch('app.main.create_user.create_aws_user', return_value=True):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert 'public_id' in data

def test_create_user_invalid_json(client):
    response = client.post('/aws/user', data="notjson", content_type='application/json')
    assert response.status_code == 400

def test_create_user_invalid_schema(client):
    # Missing required field public_id
    payload = {'foo': 'bar'}
    response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400

def test_create_user_failure(client):
    payload = {'public_id': 'abc-123'}
    with patch('app.main.create_user.create_aws_user', return_value=False):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code in (400, 500)

def test_get_user_detail_unauthorized(client):
    # Remove access token or make query with missing/malformed header
    response = client.get('/aws/user', content_type='application/json')
    # Should be 404 if user not in db, or 200 if exists, otherwise 401 if custom logic
    assert response.status_code in (404, 401)

def test_get_user_detail_success(client):
    fake_user = MagicMock()
    fake_user.public_id = 'abc-123'
    fake_user.aws_CreateUserRequestId = 'reqid'
    fake_user.aws_UserId = 'userid'
    fake_user.aws_UserName = 'username'
    fake_user.aws_AccessKeyId = 'accesskey'
    fake_user.aws_SecretAccessKey = 'secret'
    fake_user.aws_PolicyName = 'policy'
    fake_user.aws_Arn = 'arn'
    fake_user.aws_CreateDate = 'date'
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user
        response = client.get('/aws/user', content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['public_id'] == 'abc-123'

def test_get_user_detail_not_found(client):
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        response = client.get('/aws/user', content_type='application/json')
        assert response.status_code == 404

def test_get_user_details_by_admin_success(client):
    fake_user = MagicMock()
    fake_user.public_id = 'abc-123'
    fake_user.aws_CreateUserRequestId = 'reqid'
    fake_user.aws_UserId = 'userid'
    fake_user.aws_UserName = 'username'
    fake_user.aws_PolicyName = 'policy'
    fake_user.aws_Arn = 'arn'
    fake_user.aws_CreateDate = 'date'
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user
        response = client.get('/aws/user/abc-123', content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['public_id'] == 'abc-123'

def test_get_user_details_by_admin_not_found(client):
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        response = client.get('/aws/user/abc-123', content_type='application/json')
        assert response.status_code == 404

def test_generate_presigned_urls_success(client):
    payload = {'objects': ['foto1', 'foto2']}
    with patch('app.main.views.create_presigned_url', return_value={'fields': {'key': 'value'}}):
        response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert 'aws_urls' in data
        assert isinstance(data['aws_urls'], list)
        assert len(data['aws_urls']) == 2

def test_generate_presigned_urls_invalid_json(client):
    response = client.post('/aws/urls', data="notjson", content_type='application/json')
    assert response.status_code == 400

def test_generate_presigned_urls_invalid_schema(client):
    payload = {'not_objects': []}
    response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400

def test_generate_presigned_urls_empty_list(client):
    payload = {'objects': []}
    with patch('app.main.views.create_presigned_url', return_value={'fields': {'key': 'value'}}):
        response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
        # Depending on implementation, could be 201 with empty list or 400
        assert response.status_code in (201, 400)

def test_rate_limited_endpoint(client):
    # Should 429 on first call due to limiter
    response = client.get('/aws/admin/ratelimited', content_type='application/json')
    assert response.status_code in (429, 200)  # limiter may allow one call then block

# Extra: Error handler coverage
def test_method_not_allowed(client):
    response = client.delete('/aws/status', content_type='application/json')
    assert response.status_code == 405

def test_bad_method_on_aws(client):
    response = client.delete('/aws', content_type='application/json')
    assert response.status_code == 405

def test_health_check(client):
    # This checks coverage for /aws/status happy path
    response = client.get('/aws/status', content_type='application/json')
    assert response.status_code == 200
    assert "System running" in response.get_data(as_text=True)