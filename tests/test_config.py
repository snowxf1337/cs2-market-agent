from app.config import Settings 

def make_settings() -> Settings:
    return Settings(
        _env_file=None,
        db_user="user",
        db_password="secret",
        db_name="main_db",
        db_test_name="test_db",
    )


def test_database_url_uses_main_database_by_default():
    url = make_settings().database_url()
    assert url.database == "main_db"


def test_database_url_uses_test_database_when_requested():
        url = make_settings().database_url(test=True)
        assert url.database == "test_db"


def test_password_is_hidden_when_settings_are_printed():
     settings = make_settings()
     assert "secret" not in repr(settings)