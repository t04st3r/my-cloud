import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from file_handler.models import Document, Folder
from tests.factories import DocumentFactory, FolderFactory

pytestmark = pytest.mark.django_db


def test_index_lists_root_folders(auth_client, user):
    FolderFactory(owner=user)
    resp = auth_client.get('/')
    assert resp.status_code == 200
    assert len(resp.context['root_folders']) == 1
    FolderFactory(owner=user)
    resp = auth_client.get('/')
    assert len(resp.context['root_folders']) == 2


def test_index_shows_only_own_folders(auth_client, user):
    FolderFactory(owner=user)
    FolderFactory()                       # someone else's
    resp = auth_client.get('/')
    assert len(resp.context['root_folders']) == 1


def test_index_requires_login(client):
    resp = client.get('/')
    assert resp.status_code == 302
    assert '/login/' in resp['Location']


def test_upload_get_renders_form(auth_client, user):
    folder = FolderFactory(owner=user)
    resp = auth_client.get('/upload/%d/' % folder.id)
    assert resp.status_code == 200
    assert 'form' in resp.context


def test_upload_multiple_files(auth_client, user):
    folder = FolderFactory(owner=user)
    f1 = SimpleUploadedFile('a.txt', b'aaa', content_type='text/plain')
    f2 = SimpleUploadedFile('b.txt', b'bbb', content_type='text/plain')
    resp = auth_client.post('/upload/%d/' % folder.id,
                            {'folder': folder.id, 'file': [f1, f2]}, follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % folder.id
    docs = Document.objects.filter(folder=folder)
    assert docs.count() == 2
    for doc in docs:
        assert doc.name == doc.filename()
        assert doc.owner == user           # stamped with the uploader


def test_upload_invalid_without_file(auth_client, user):
    folder = FolderFactory(owner=user)
    resp = auth_client.post('/upload/%d/' % folder.id, {'folder': folder.id})
    assert resp.status_code == 200                       # re-renders with errors
    assert Document.objects.filter(folder=folder).count() == 0


def test_folder_view(auth_client, user):
    folder = FolderFactory(owner=user)
    child = FolderFactory(parent=folder, owner=user)
    document = DocumentFactory(folder=folder, owner=user)
    resp = auth_client.get('/folder/%d/' % folder.id)
    assert resp.status_code == 200
    assert resp.context['root'] == folder
    assert document in resp.context['documents']
    assert child in resp.context['children']


def test_folder_view_404(auth_client):
    assert auth_client.get('/folder/999999/').status_code == 404


def test_cannot_view_other_users_folder(auth_client):
    other = FolderFactory()               # different owner
    assert auth_client.get('/folder/%d/' % other.id).status_code == 404


def test_download(auth_client, user):
    document = DocumentFactory(owner=user)
    resp = auth_client.get('/download/%d/' % document.id)
    assert resp.status_code == 200
    cd = resp['Content-Disposition']
    assert cd.startswith('attachment')
    assert document.filename() in cd


def test_cannot_download_other_users_file(auth_client):
    other = DocumentFactory()             # different owner
    assert auth_client.get('/download/%d/' % other.id).status_code == 404


def test_create_root_folder(auth_client, user):
    resp = auth_client.post('/create', {'name': 'top'}, follow=True)
    assert resp.redirect_chain[-1][0] == '/'
    folder = Folder.objects.get(name='top', parent__isnull=True)
    assert folder.owner == user


def test_create_nested_folder(auth_client, user):
    parent = FolderFactory(owner=user)
    resp = auth_client.post('/create/%d/' % parent.id,
                            {'name': 'child', 'parent': parent.id}, follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % parent.id
    child = Folder.objects.get(name='child')
    assert child.parent == parent
    assert child.owner == user


def test_create_invalid_folder(auth_client):
    resp = auth_client.post('/create', {}, follow=True)
    assert resp.redirect_chain[-1][0] == '/'
    assert not Folder.objects.exists()


def test_create_get_renders(auth_client, user):
    parent = FolderFactory(owner=user)
    resp = auth_client.get('/create/%d/' % parent.id)
    assert resp.status_code == 200
    assert resp.context['parent'] == parent


def test_create_under_other_users_folder_404(auth_client):
    other = FolderFactory()
    assert auth_client.get('/create/%d/' % other.id).status_code == 404


def test_delete_doc(auth_client, user):
    document = DocumentFactory(owner=user)
    path = document.file_path()
    assert os.path.isfile(path)
    resp = auth_client.post('/delete_doc/%d/' % document.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % document.folder.id
    assert not Document.objects.filter(pk=document.id).exists()
    assert not os.path.isfile(path)          # file removed by post_delete signal


def test_delete_doc_get_not_allowed(auth_client, user):
    document = DocumentFactory(owner=user)
    assert auth_client.get('/delete_doc/%d/' % document.id).status_code == 405


def test_cannot_delete_other_users_doc(auth_client):
    other = DocumentFactory()
    assert auth_client.post('/delete_doc/%d/' % other.id).status_code == 404


def test_delete_folder_cascade(auth_client, user):
    parent = FolderFactory(owner=user)
    child = FolderFactory(parent=parent, owner=user)
    doc = DocumentFactory(folder=child, owner=user)
    path = doc.file_path()
    resp = auth_client.post('/delete/%d/' % child.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % parent.id
    assert not Folder.objects.filter(pk=child.id).exists()
    assert not os.path.isfile(path)


def test_delete_root_folder_redirects_home(auth_client, user):
    folder = FolderFactory(owner=user)
    resp = auth_client.post('/delete/%d/' % folder.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/'
    assert not Folder.objects.filter(pk=folder.id).exists()


def test_delete_folder_get_not_allowed(auth_client, user):
    folder = FolderFactory(owner=user)
    assert auth_client.get('/delete/%d/' % folder.id).status_code == 405


def test_cannot_delete_other_users_folder(auth_client):
    other = FolderFactory()
    assert auth_client.post('/delete/%d/' % other.id).status_code == 404
