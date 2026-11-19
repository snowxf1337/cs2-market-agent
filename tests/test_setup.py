import sys
import app


def test_python_version_is_supported():
    assert sys.version_info >= (3, 13)


def test_app_package_is_importable():
    assert app is not None