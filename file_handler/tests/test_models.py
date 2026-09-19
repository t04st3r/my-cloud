import os

import pytest

from file_handler.models import Document, Folder
from tests.factories import DocumentFactory, FolderFactory

pytestmark = pytest.mark.django_db


# ---- Folder -------------------------------------------------------------------

def test_root_folders():
    parent = FolderFactory()
    parent2 = FolderFactory()
    child = FolderFactory(parent=parent)
    roots = Folder.root_folders()
    assert parent in roots
    assert parent2 in roots
    assert child not in roots


def test_is_empty():
    parent = FolderFactory()
    child = FolderFactory(parent=parent)          # parent is not a leaf
    empty_leaf = FolderFactory()
    assert empty_leaf.is_empty() is True
    assert parent.is_empty() is False             # has a child (not a leaf)
    DocumentFactory(folder=child)
    assert child.is_empty() is False              # leaf but has a document


def test_folder_str():
    folder = FolderFactory(name='documents')
    assert str(folder) == 'documents'


# ---- Document -----------------------------------------------------------------

def test_document_str():
    document = DocumentFactory(name='report.txt')
    assert str(document) == 'report.txt'


def test_file_path_matches_storage_path():
    document = DocumentFactory()
    assert document.file_path() == document.file.path


def test_file_url():
    document = DocumentFactory()
    assert document.file_url() == '/media/' + document.file.name


def test_filename():
    document = DocumentFactory()
    assert document.filename() == os.path.basename(document.file.name)


def test_file_mime():
    document = DocumentFactory(file__data=b'plain text body\n')
    assert document.file_mime() == 'text/plain'


def test_full_path_nested():
    root = FolderFactory(name='root')
    sub = FolderFactory(name='etc', parent=root)
    document = DocumentFactory(name='conf.txt', folder=sub)
    assert document.full_path() == '/root/etc/conf.txt'


def test_full_path_without_folder():
    document = DocumentFactory(name='loose.txt', folder=None)
    assert document.full_path() == '/loose.txt'
