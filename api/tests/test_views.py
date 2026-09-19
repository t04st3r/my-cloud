import pytest

from file_handler.models import Folder
from tests.factories import DocumentFactory, FolderFactory

pytestmark = pytest.mark.django_db


def test_folder_list_requires_auth(api_client):
    assert api_client.get('/api/folder/').status_code == 401


def test_folder_list(api_client, user):
    api_client.force_authenticate(user)
    root = FolderFactory()
    FolderFactory(parent=root)          # child -> not a root
    resp = api_client.get('/api/folder/')
    assert resp.status_code == 200
    names = [f['name'] for f in resp.data['results']]
    assert root.name in names
    assert len(names) == 1              # only root folders listed


def test_folder_detail_nested(api_client, user):
    api_client.force_authenticate(user)
    root = FolderFactory()
    child = FolderFactory(parent=root)
    document = DocumentFactory(folder=root)
    resp = api_client.get('/api/folder/%d/' % root.id)
    assert resp.status_code == 200
    assert resp.data['name'] == root.name
    assert resp.data['children'][0]['id'] == child.id
    assert resp.data['documents'][0]['id'] == document.id


def test_folder_delete(api_client, user):
    api_client.force_authenticate(user)
    folder = FolderFactory()
    resp = api_client.delete('/api/folder/%d/' % folder.id)
    assert resp.status_code == 204
    assert not Folder.objects.filter(pk=folder.id).exists()
