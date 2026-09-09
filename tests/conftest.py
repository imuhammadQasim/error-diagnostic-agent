import pytest

from app.config import get_settings


@pytest.fixture
def data_dir():
    return get_settings().data_dir
