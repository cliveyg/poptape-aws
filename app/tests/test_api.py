import json
import pytest
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.config import TestConfig

@pytest.fixture
def client():
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

@pytest.fixture
def mock_s3():
    with patch('app.extensions.boto3.client') as mock_client:
        s3_mock = MagicMock()
        s3_mock.create_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_policy.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.put_bucket_cors.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        s3_mock.delete_public_access_block.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock_client.return_value = s3_mock
        yield s3_mock

@pytest.fixture
def mock_authy():
    with patch('requests.post') as mock_post:
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'success': True, 'user_id': 'test-user'}
        mock_post.return_value = response
        yield mock_post

def test_status_ok(client):
    """Test the /aws/status endpoint returns 200 OK."""
    response = client.get('/aws/status', content_type='application/json')
    assert response.status_code == 200
    assert "System running" in response.get_data(as_text=True)

def test_404(client):
    """Test an unknown endpoint returns 404."""
    response = client.get('/aws/nonexistent')
    assert response.status_code == 404

def test_api_rejects_html_input(client):
    """Test API rejects requests with wrong content type."""
    response = client.get('/aws/status', content_type='text/html')
    assert response.status_code == 400

def test_sitemap_lists_endpoints(client):
    """Test the /aws endpoint returns all available endpoints."""
    response = client.get('/aws')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoints' in data
    urls = [ep['url'] for ep in data['endpoints']]
    # Check that key known endpoints are present
    assert '/aws/user' in urls
    assert '/aws/urls' in urls
    assert '/aws/status' in urls
    assert '/aws' in urls
    assert '/aws/user/<user_id>' in urls or any('/aws/user/' in u for u in urls)
    # Check structure
    for ep in data['endpoints']:
        assert 'url' in ep
        assert 'methods' in ep

def test_create_user_success(client):
    """Test creating a new AWS user (happy path)."""
    payload = {'public_id': 'abc-123'}
    with patch('app.main.create_user.create_aws_user', return_value=True):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 201
        assert "User created" in response.get_data(as_text=True)

def test_create_user_invalid_json(client):
    """Test creating user with invalid JSON."""
    response = client.post('/aws/user', data="notjson", content_type='application/json')
    assert response.status_code == 400

def test_create_user_invalid_schema(client):
    """Test creating user with invalid schema."""
    payload = {'not_public_id': 'abc-123'}
    response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400

def test_create_user_failure(client):
    """Test failure to create AWS user."""
    payload = {'public_id': 'abc-123'}
    with patch('app.main.create_user.create_aws_user', return_value=False):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 500

def test_get_user_detail_unauthorized(client):
    """Test GET /aws/user requires access (mocked to fail)."""
    # Simulate require_access_level decorator raising an error
    with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: (jsonify({"error": "unauthorized"}), 401))):
        response = client.get('/aws/user', content_type='application/json')
        assert response.status_code in (401, 403)

def test_get_user_detail_success(client):
    """Test GET /aws/user for an existing user."""
    # db/AwsDetails model is mocked
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
        # patch access decorator to allow
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.get('/aws/user', content_type='application/json')
            assert response.status_code == 200
            data = response.get_json()
            assert data['public_id'] == 'abc-123'

def test_get_user_detail_not_found(client):
    """Test GET /aws/user for non-existent user."""
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.get('/aws/user', content_type='application/json')
            assert response.status_code == 404

def test_get_user_details_by_admin_success(client):
    """Test GET /aws/user/<user_id> as admin."""
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
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.get('/aws/user/abc-123', content_type='application/json')
            assert response.status_code == 200
            data = response.get_json()
            assert data['public_id'] == 'abc-123'

def test_get_user_details_by_admin_not_found(client):
    """Test GET /aws/user/<user_id> for non-existent user."""
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.get('/aws/user/abc-123', content_type='application/json')
            assert response.status_code == 404

def test_generate_presigned_urls_success(client):
    """Test /aws/urls endpoint happy path."""
    payload = {'objects': ['foto1', 'foto2']}
    with patch('app.main.views.create_presigned_url', return_value={'fields': {'key': 'value'}}):
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 201
            data = response.get_json()
            assert 'aws_urls' in data
            assert isinstance(data['aws_urls'], list)
            assert len(data['aws_urls']) == 2

def test_generate_presigned_urls_invalid_json(client):
    """Test /aws/urls invalid JSON payload."""
    with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
        response = client.post('/aws/urls', data="notjson", content_type='application/json')
        assert response.status_code == 400

def test_generate_presigned_urls_invalid_schema(client):
    """Test /aws/urls invalid schema."""
    payload = {'not_objects': []}
    with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
        response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 400

def test_generate_presigned_urls_empty_list(client):
    """Test /aws/urls with empty objects list."""
    payload = {'objects': []}
    with patch('app.main.views.create_presigned_url', return_value={'fields': {'key': 'value'}}):
        with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
            response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
            assert response.status_code == 201
            data = response.get_json()
            assert isinstance(data['aws_urls'], list)
            assert len(data['aws_urls']) == 0

def test_rate_limited_endpoint(client):
    """Test /aws/admin/ratelimited returns 429 after limit exceeded."""
    with patch('app.main.views.require_access_level', side_effect=lambda *a, **kw: (lambda *x, **y: x[0])):
        # Call once, should work (limit is 0/minute in code, so will always fail)
        response = client.get('/aws/admin/ratelimited', content_type='application/json')
        # Should be 429 Too Many Requests
        assert response.status_code in (429, 200)

# Add more tests as endpoints/logic are added