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


def test_filters_by_kwargs():
    from tests.factories import UserFactory
    a, b = UserFactory(), UserFactory()
    FolderFactory(owner=a)
    b_folder = FolderFactory(owner=b)
    assert get_earliest_objects_or_none(Folder, owner=b) == b_folder


def test_raises_on_non_model():
    with pytest.raises(ValueError):
        get_earliest_objects_or_none(5)
