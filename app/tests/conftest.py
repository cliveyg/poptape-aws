from unittest.mock import patch, MagicMock

# Patch all decorators and validators globally BEFORE importing anything else
patch("app.decorators.require_access_level", lambda *a, **kw: (lambda f: f)).start()
patch("app.main.views.require_access_level", lambda *a, **kw: (lambda f: f)).start()
patch("app.assertions.assert_valid_schema", lambda data, schema: True).start()
patch("app.extensions.boto3.client").start()
patch("requests.post").start()
patch("requests.get").start()