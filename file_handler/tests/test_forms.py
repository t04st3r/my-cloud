import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from file_handler.forms import MultipleFileField

pytestmark = pytest.mark.django_db


def test_multiplefilefield_wraps_single_file():
    """A single (non-list) upload is still cleaned into a list."""
    field = MultipleFileField()
    upload = SimpleUploadedFile('a.txt', b'data')
    cleaned = field.clean(upload)
    assert cleaned == [upload]


def test_multiplefilefield_cleans_list():
    field = MultipleFileField()
    uploads = [SimpleUploadedFile('a.txt', b'a'), SimpleUploadedFile('b.txt', b'b')]
    assert field.clean(uploads) == uploads
