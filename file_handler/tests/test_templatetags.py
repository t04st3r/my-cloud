import pytest

from file_handler.templatetags.file_handler_extras import breadcrumb
from tests.factories import FolderFactory

pytestmark = pytest.mark.django_db


def test_breadcrumb_none():
    assert breadcrumb(None) == {'ancestors': []}


def test_breadcrumb_nested():
    root = FolderFactory(name='root')
    child = FolderFactory(name='etc', parent=root)
    ctx = breadcrumb(child)
    assert list(ctx['ancestors']) == [root, child]
