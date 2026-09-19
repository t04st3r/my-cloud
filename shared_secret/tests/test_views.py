import os

import pytest

from file_handler.models import Document
from shared_secret.models import ShamirSS
from tests.factories import DocumentFactory, ShamirSSFactory

pytestmark = pytest.mark.django_db

SCHEME_DATA = {'name': 'test', 'mers_exp': 107, 'k': 4, 'n': 18}


def _share_post(scheme, shares, **extra):
    """Build POST data with the first k shares plus the scheme id."""
    data = {'share_%d' % pos: value for pos, value in shares[:scheme.k]}
    data['scheme'] = scheme.id
    data.update(extra)
    return data


# ---- index / create -----------------------------------------------------------

def test_index_empty_then_one(auth_client):
    resp = auth_client.get('/s/')
    assert resp.status_code == 200
    assert len(resp.context['schemes']) == 0
    ShamirSSFactory(name='pizza')
    resp = auth_client.get('/s/')
    assert len(resp.context['schemes']) == 1
    assert resp.context['schemes'][0].name == 'pizza'


def test_index_shows_doc_count(auth_client):
    scheme = ShamirSSFactory()
    DocumentFactory(scheme=scheme)
    resp = auth_client.get('/s/')
    assert resp.context['schemes'][0].doc_count == 1


def test_create_get(auth_client):
    resp = auth_client.get('/s/create/')
    assert resp.status_code == 200
    assert 'form' in resp.context


def test_create_post_generates_shares(auth_client):
    resp = auth_client.post('/s/create/', SCHEME_DATA)
    assert resp.status_code == 200
    assert len(resp.context['shares']) == SCHEME_DATA['n']
    assert ShamirSS.objects.filter(name='test').exists()


# ---- delete -------------------------------------------------------------------

def test_create_post_invalid(auth_client):
    # k > n is invalid -> form errors, create.html re-rendered, nothing saved
    resp = auth_client.post('/s/create/', {'name': 'x', 'mers_exp': 89, 'k': 5, 'n': 3})
    assert resp.status_code == 200
    assert 'form' in resp.context
    assert not ShamirSS.objects.exists()


def test_delete_missing_scheme_404(auth_client):
    assert auth_client.post('/s/delete/999999/').status_code == 404


def test_delete_get_not_allowed(auth_client):
    scheme = ShamirSSFactory()
    assert auth_client.get('/s/delete/%d/' % scheme.id).status_code == 405


def test_delete_scheme_without_files(auth_client):
    scheme = ShamirSSFactory()
    resp = auth_client.post('/s/delete/%d/' % scheme.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/s/'
    assert not ShamirSS.objects.filter(pk=scheme.id).exists()


def test_delete_with_files_needs_mode(auth_client):
    scheme = ShamirSSFactory()
    DocumentFactory(scheme=scheme)
    resp = auth_client.post('/s/delete/%d/' % scheme.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/s/'
    assert ShamirSS.objects.filter(pk=scheme.id).exists()   # nothing happened


def test_delete_with_files(auth_client):
    scheme = ShamirSSFactory()
    doc = DocumentFactory(scheme=scheme)
    path = doc.file_path()
    auth_client.post('/s/delete/%d/' % scheme.id, {'mode': 'with_files'})
    assert not ShamirSS.objects.filter(pk=scheme.id).exists()
    assert not Document.objects.filter(pk=doc.id).exists()
    assert not os.path.isfile(path)


def test_delete_scheme_only_keeps_files(auth_client):
    scheme = ShamirSSFactory()
    doc = DocumentFactory(scheme=scheme)
    path = doc.file_path()
    auth_client.post('/s/delete/%d/' % scheme.id, {'mode': 'scheme_only'})
    assert not ShamirSS.objects.filter(pk=scheme.id).exists()
    doc.refresh_from_db()
    assert doc.scheme_id is None            # detached, not deleted
    assert os.path.isfile(path)             # file kept


# ---- refresh ------------------------------------------------------------------

def test_refresh_missing_scheme_404(auth_client):
    assert auth_client.post('/s/refresh/999999/').status_code == 404


def test_refresh_get_not_allowed(auth_client):
    scheme = ShamirSSFactory()
    assert auth_client.get('/s/refresh/%d/' % scheme.id).status_code == 405


def test_refresh_without_files(auth_client):
    scheme = ShamirSSFactory(**SCHEME_DATA)
    old = scheme.get_shares()
    scheme.save()
    resp = auth_client.post('/s/refresh/%d/' % scheme.id)
    assert resp.status_code == 200
    new = resp.context['shares']
    assert len(new) == scheme.n
    assert [v for _, v in new] != [v for _, v in old]


def test_refresh_with_files_needs_mode(auth_client):
    scheme = ShamirSSFactory()
    DocumentFactory(scheme=scheme)
    resp = auth_client.post('/s/refresh/%d/' % scheme.id, follow=True)
    assert resp.redirect_chain[-1][0] == '/s/'


def test_refresh_with_files(auth_client):
    scheme = ShamirSSFactory()
    doc = DocumentFactory(scheme=scheme)
    path = doc.file_path()
    resp = auth_client.post('/s/refresh/%d/' % scheme.id, {'mode': 'with_files'})
    assert resp.status_code == 200
    assert not Document.objects.filter(pk=doc.id).exists()
    assert not os.path.isfile(path)


def test_refresh_scheme_only_keeps_files(auth_client):
    scheme = ShamirSSFactory()
    doc = DocumentFactory(scheme=scheme)
    resp = auth_client.post('/s/refresh/%d/' % scheme.id, {'mode': 'scheme_only'})
    assert resp.status_code == 200
    doc.refresh_from_db()
    assert doc.scheme_id == scheme.id       # still linked


# ---- encrypt / decrypt --------------------------------------------------------

def test_encrypt_missing_404(auth_client):
    assert auth_client.get('/s/encrypt/999998/999999/').status_code == 404
    assert auth_client.post('/s/encrypt/999998/999999/').status_code == 404


def test_encrypt_flow(auth_client):
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    scheme.save()
    doc = DocumentFactory()

    assert auth_client.get('/s/encrypt/%d/%d/' % (doc.id, scheme.id)).status_code == 200

    resp = auth_client.post('/s/encrypt/%d/%d/' % (doc.id, scheme.id),
                            _share_post(scheme, shares), follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % doc.folder.id
    doc.refresh_from_db()
    assert doc.scheme_id == scheme.id
    assert doc.filename().endswith('.enc')

    # encrypting again reports the error
    resp = auth_client.post('/s/encrypt/%d/%d/' % (doc.id, scheme.id),
                            _share_post(scheme, shares))
    assert 'Document already encrypted' in resp.context['form'].non_field_errors()


def test_encrypt_wrong_shares(auth_client):
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    scheme.save()
    doc = DocumentFactory()
    # enough shares by count, but a wrong value -> recovery fails
    data = {'scheme': scheme.id, 'share_1': shares[0][1], 'share_2': shares[0][1]}
    resp = auth_client.post('/s/encrypt/%d/%d/' % (doc.id, scheme.id), data)
    assert 'Wrong shares values' in resp.context['form'].non_field_errors()


def test_encrypt_missing_file_error(auth_client):
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    scheme.save()
    doc = DocumentFactory()
    os.remove(doc.file_path())          # file gone -> encrypt_file returns None
    resp = auth_client.post('/s/encrypt/%d/%d/' % (doc.id, scheme.id),
                            _share_post(scheme, shares))
    assert 'Encryption error' in resp.context['form'].non_field_errors()


def test_decrypt_plaintext_404(auth_client):
    doc = DocumentFactory()      # scheme is None
    assert auth_client.get('/s/decrypt/%d/' % doc.id).status_code == 404


def test_decrypt_flow(auth_client):
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    scheme.save()
    doc = DocumentFactory()
    # encrypt it first
    enc = scheme.encrypt_file(doc.file_path(), shares)
    os.remove(doc.file_path())
    doc.file.name = enc
    doc.scheme = scheme
    doc.save()

    assert auth_client.get('/s/decrypt/%d/' % doc.id).status_code == 200

    resp = auth_client.post('/s/decrypt/%d/' % doc.id,
                            _share_post(scheme, shares), follow=True)
    assert resp.redirect_chain[-1][0] == '/folder/%d/' % doc.folder.id
    doc.refresh_from_db()
    assert doc.scheme_id is None
    assert not doc.filename().endswith('.enc')


def test_decrypt_missing_file_returns_to_form(auth_client):
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    scheme.save()
    doc = DocumentFactory()
    os.remove(doc.file_path())
    doc.file.name = 'documents/missing.enc'   # marked encrypted, file absent
    doc.scheme = scheme
    doc.save()
    resp = auth_client.post('/s/decrypt/%d/' % doc.id, _share_post(scheme, shares))
    assert resp.status_code == 200            # re-rendered, not redirected
    doc.refresh_from_db()
    assert doc.scheme_id == scheme.id         # still encrypted
