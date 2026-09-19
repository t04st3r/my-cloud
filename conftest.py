"""Shared pytest fixtures.

Key guarantee: every test that touches the filesystem does so inside a per-test
temporary ``MEDIA_ROOT``, so the real ``media/`` directory is never written to and
tests stay idempotent.
"""
import pytest
from rest_framework.test import APIClient

from tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _isolated_media(settings, tmp_path):
    """Point MEDIA_ROOT at an auto-cleaned temp dir for every test.

    The trailing slash matters: file_handler/shared_secret models build paths by
    string concatenation and prefix-slicing on MEDIA_ROOT.
    """
    media = tmp_path / "media"
    media.mkdir()
    settings.MEDIA_ROOT = str(media) + "/"
    return settings.MEDIA_ROOT


@pytest.fixture
def user(db):
    """A persisted user."""
    return UserFactory()


@pytest.fixture
def auth_client(client, user):
    """A Django test client already logged in as ``user``."""
    client.force_login(user)
    return client


@pytest.fixture
def api_client():
    """A DRF APIClient (use ``.force_authenticate(user)`` to authenticate)."""
    return APIClient()
