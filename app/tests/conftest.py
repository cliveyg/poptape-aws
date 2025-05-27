import pytest

@pytest.fixture(autouse=True)
def patch_require_access_level(monkeypatch):
    from app.main import views
    monkeypatch.setattr(views, 'require_access_level', lambda *a, **kw: (lambda f: f))