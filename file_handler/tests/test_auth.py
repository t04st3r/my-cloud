import pytest

from my_cloud.authentication import CustomAuthentication
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def backend():
    return CustomAuthentication()


def test_authenticate_by_username(backend):
    user = UserFactory(username='alice')
    assert backend.authenticate(None, username='alice', password='pass12345') == user


def test_authenticate_by_email(backend):
    user = UserFactory(username='bob', email='bob@example.com')
    assert backend.authenticate(None, username='bob@example.com', password='pass12345') == user


def test_authenticate_unknown_user(backend):
    assert backend.authenticate(None, username='ghost', password='pass12345') is None


def test_authenticate_wrong_password(backend):
    UserFactory(username='carol')
    assert backend.authenticate(None, username='carol', password='nope') is None


def test_help_page_is_public(client):
    resp = client.get('/help/')
    assert resp.status_code == 200            # no login required
    assert b'Shamir' in resp.content


def test_login_page_uses_bootstrap_form(client):
    resp = client.get('/login/')
    assert resp.status_code == 200
    # BootstrapAuthenticationForm styles its inputs
    assert 'form-control' in resp.content.decode()


# ---- logout view is POST-only in Django 5 ------------------------------------

def test_logout_get_not_allowed(auth_client):
    assert auth_client.get('/logout/').status_code == 405


def test_logout_post_logs_out(auth_client):
    assert auth_client.post('/logout/').status_code == 302
    # session cleared -> protected page now redirects to login
    resp = auth_client.get('/')
    assert '/login/' in resp['Location']
