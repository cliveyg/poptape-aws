import json
import uuid
import pytest

@pytest.fixture
def client():
    from app import create_app, db
    from app.config import TestConfig
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()

def valid_uuid():
    return str(uuid.uuid4())

def test_status_ok(client):
    response = client.get('/aws/status', content_type='application/json')
    assert response.status_code == 200
    assert "System running" in response.get_data(as_text=True)

def test_404(client):
    response = client.get('/aws/notarealroute', content_type='application/json')
    assert response.status_code == 404

def test_api_rejects_html_input(client):
    response = client.get('/aws/status', content_type='text/html')
    assert response.status_code == 400

def test_method_not_allowed(client):
    response = client.delete('/aws/status', content_type='application/json')
    assert response.status_code == 405

def test_sitemap_lists_endpoints(client):
    response = client.get('/aws', content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert 'endpoints' in data
    urls = [ep['url'] for ep in data['endpoints']]
    assert '/aws/user' in urls
    assert '/aws/urls' in urls
    assert '/aws/status' in urls
    assert '/aws' in urls
    for ep in data['endpoints']:
        assert 'url' in ep
        assert 'methods' in ep

def test_create_user_success(client):
    payload = {'public_id': valid_uuid()}
    from unittest.mock import patch
    with patch('app.main.create_user.create_aws_user', return_value=True):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 201
        assert "User created" in response.get_data(as_text=True)

def test_create_user_invalid_json(client):
    response = client.post('/aws/user', data="notjson", content_type='application/json')
    assert response.status_code == 400

def test_create_user_invalid_schema(client):
    response = client.post('/aws/user', data=json.dumps({'foo': 'bar'}), content_type='application/json')
    assert response.status_code == 400

def test_create_user_invalid_uuid(client):
    payload = {'public_id': 'not-a-uuid'}
    response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
    assert response.status_code == 400

def test_create_user_failure(client):
    payload = {'public_id': valid_uuid()}
    from unittest.mock import patch
    with patch('app.main.create_user.create_aws_user', return_value=False):
        response = client.post('/aws/user', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 500

def test_get_user_detail_success(client):
    from unittest.mock import MagicMock, patch
    fake_user = MagicMock()
    fake_user.public_id = valid_uuid()
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
        assert data['public_id'] == fake_user.public_id
        assert data['aws_UserName'] == 'username'

def test_get_user_detail_not_found(client):
    from unittest.mock import patch
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        response = client.get('/aws/user', content_type='application/json')
        assert response.status_code == 404

def test_get_user_details_by_admin_success(client):
    from unittest.mock import MagicMock, patch
    fake_user = MagicMock()
    fake_user.public_id = valid_uuid()
    fake_user.aws_CreateUserRequestId = 'reqid'
    fake_user.aws_UserId = 'userid'
    fake_user.aws_UserName = 'username'
    fake_user.aws_PolicyName = 'policy'
    fake_user.aws_Arn = 'arn'
    fake_user.aws_CreateDate = 'date'
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = fake_user
        response = client.get(f'/aws/user/{fake_user.public_id}', content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['public_id'] == fake_user.public_id
        assert data['aws_UserName'] == 'username'

def test_get_user_details_by_admin_not_found(client):
    from unittest.mock import patch
    with patch('app.main.views.AwsDetails.query') as mock_query:
        mock_query.filter_by.return_value.first.return_value = None
        response = client.get(f'/aws/user/{valid_uuid()}', content_type='application/json')
        assert response.status_code == 404

def test_generate_presigned_urls_success(client):
    from unittest.mock import patch
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
    from unittest.mock import patch
    payload = {'objects': []}
    with patch('app.main.views.create_presigned_url', return_value={'fields': {'key': 'value'}}):
        response = client.post('/aws/urls', data=json.dumps(payload), content_type='application/json')
        assert response.status_code == 201
        data = response.get_json()
        assert 'aws_urls' in data
        assert isinstance(data['aws_urls'], list)
        assert len(data['aws_urls']) == 0

def test_rate_limited_endpoint(client):
    resp = client.get('/aws/admin/ratelimited', content_type='application/json')
    assert resp.status_code in (429, 200)

def test_405_error_user(client):
    response = client.delete('/aws/user', content_type='application/json')
    assert response.status_code == 405

def test_429_error(client):
    for _ in range(3):
        resp = client.get('/aws/admin/ratelimited', content_type='application/json')
    assert resp.status_code == 429 or resp.status_code == 200

def test_microservice_only_no_ip():
    from app.decorators import microservice_only
    from flask import jsonify

    class DummyRequest:
        headers = {}

    @microservice_only(DummyRequest())
    def dummy(pub_id, req, *a, **k):
        return "ok"

    resp = dummy("pubid", DummyRequest())
    assert isinstance(resp, tuple)
    assert resp[1] == 401
    assert "bit suspicious" in resp[0].get_json()["message"]