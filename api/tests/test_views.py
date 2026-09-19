import pytest

from file_handler.models import Folder
from tests.factories import DocumentFactory, FolderFactory

pytestmark = pytest.mark.django_db


def test_folder_list_requires_auth(api_client):
    assert api_client.get('/api/folder/').status_code == 401


def test_folder_list(api_client, user):
    api_client.force_authenticate(user)
    root = FolderFactory(owner=user)
    FolderFactory(parent=root, owner=user)   # child -> not a root
    resp = api_client.get('/api/folder/')
    assert resp.status_code == 200
    names = [f['name'] for f in resp.data['results']]
    assert root.name in names
    assert len(names) == 1                    # only root folders listed


def test_folder_list_only_own(api_client, user):
    api_client.force_authenticate(user)
    FolderFactory(owner=user)
    FolderFactory()                           # another user's root
    resp = api_client.get('/api/folder/')
    assert len(resp.data['results']) == 1


def test_folder_detail_nested(api_client, user):
    api_client.force_authenticate(user)
    root = FolderFactory(owner=user)
    child = FolderFactory(parent=root, owner=user)
    document = DocumentFactory(folder=root, owner=user)
    resp = api_client.get('/api/folder/%d/' % root.id)
    assert resp.status_code == 200
    assert resp.data['name'] == root.name
    assert resp.data['children'][0]['id'] == child.id
    assert resp.data['documents'][0]['id'] == document.id


def test_folder_detail_other_user_404(api_client, user):
    api_client.force_authenticate(user)
    other = FolderFactory()                   # different owner
    assert api_client.get('/api/folder/%d/' % other.id).status_code == 404


def test_folder_create_sets_owner(api_client, user):
    api_client.force_authenticate(user)
    resp = api_client.post('/api/folder/', {'name': 'via-api'})
    assert resp.status_code == 201
    folder = Folder.objects.get(name='via-api')
    assert folder.owner == user            # perform_create stamps the caller


def test_folder_delete(api_client, user):
    api_client.force_authenticate(user)
    folder = FolderFactory(owner=user)
    resp = api_client.delete('/api/folder/%d/' % folder.id)
    assert resp.status_code == 204
    assert not Folder.objects.filter(pk=folder.id).exists()
