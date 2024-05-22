import pytest


@pytest.fixture
def vocab_uri() -> str:
    return 'http://example.com/foo#'


@pytest.fixture
def post(admin_client):
    def _post(url: str, **kwargs):
        return admin_client.post(url, follow=True, **kwargs)
    return _post
