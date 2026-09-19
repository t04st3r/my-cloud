import pytest

from file_handler.models import Folder
from file_handler.utils import get_earliest_objects_or_none
from tests.factories import FolderFactory

pytestmark = pytest.mark.django_db


def test_returns_earliest_by_id():
    first = FolderFactory()
    FolderFactory()
    assert get_earliest_objects_or_none(Folder) == first


def test_returns_none_when_empty():
    assert get_earliest_objects_or_none(Folder) is None


def test_raises_on_non_model():
    with pytest.raises(ValueError):
        get_earliest_objects_or_none(5)
