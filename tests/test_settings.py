from importlib import reload

from grove import settings


def test_environment_variables(monkeypatch):
    monkeypatch.setenv('DATABASE_URL', 'sqlite:///test-db.sqlite3')
    monkeypatch.setenv('DEBUG', 'False')
    monkeypatch.setenv('SECRET_KEY', 'foobar')
    reload(settings)

    assert settings.DEBUG is False
    assert settings.SECRET_KEY == 'foobar'
    assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'
    assert settings.DATABASES['default']['NAME'] == 'test-db.sqlite3'
