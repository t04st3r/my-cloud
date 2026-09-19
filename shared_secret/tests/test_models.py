import base64
import os

import django.contrib.auth.hashers as hashers
import pytest
from cryptography.fernet import Fernet
from django.conf import settings

from shared_secret.models import ShamirSS
from tests.factories import ShamirSSFactory

pytestmark = pytest.mark.django_db


def _pick(shares, k):
    """Return the first k shares (distinct positions)."""
    return list(shares[:k])


def test_str_and_difference():
    scheme = ShamirSSFactory(name='pizza', k=4, n=18)
    assert str(scheme) == 'pizza (4, 18)'
    assert scheme.difference() == 14


def test_encode_decode_roundtrip():
    scheme = ShamirSSFactory()
    value = 123456789012345
    decoded = scheme.decode_shares(scheme.encode_shares([(1, value)]))
    assert decoded[0] == (1, value)


@pytest.mark.parametrize('secret', [1, 12345, 2 ** 127 - 1])
def test_get_key_is_a_valid_fernet_key(secret):
    scheme = ShamirSSFactory()
    key = scheme.get_key(secret)
    # 32 uniform bytes (SHA-256 digest), url-safe base64 encoded
    assert len(base64.urlsafe_b64decode(key)) == 32
    Fernet(key)                      # raises if the key is not a valid Fernet key
    assert scheme.get_key(secret) == key   # deterministic


def test_get_key_differs_per_secret():
    scheme = ShamirSSFactory()
    assert scheme.get_key(1) != scheme.get_key(2)


def test_shares_generation_and_secret_recovery():
    scheme = ShamirSSFactory(mers_exp=107, k=4, n=18)
    shares = scheme.get_shares()
    assert len(shares) == scheme.n

    # any k shares recover the stored secret
    rec = scheme.get_secret(scheme.decode_shares(_pick(shares, scheme.k)))
    assert hashers.check_password(str(rec), scheme.secret)

    # all n shares recover it too
    rec_all = scheme.get_secret(scheme.decode_shares(shares))
    assert hashers.check_password(str(rec_all), scheme.secret)


def test_get_secret_requires_k_shares():
    scheme = ShamirSSFactory(k=4, n=18)
    shares = scheme.get_shares()
    too_few = scheme.decode_shares(_pick(shares, scheme.k - 1))
    with pytest.raises(ValueError):
        scheme.get_secret(too_few)


def test_wrong_shares_do_not_recover_secret():
    scheme = ShamirSSFactory(k=4, n=18)
    shares = scheme.get_shares()
    picked = _pick(shares, scheme.k)
    # corrupt one share's value
    picked[0] = (picked[0][0], picked[1][1])
    wrong = scheme.get_secret(scheme.decode_shares(picked))
    assert not hashers.check_password(str(wrong), scheme.secret)


def test_generate_shares_irrecoverable_pool():
    scheme = ShamirSSFactory(k=5, n=3)   # k > n
    with pytest.raises(ValueError):
        scheme.get_shares()


def test_recover_secret_needs_two_shares():
    scheme = ShamirSSFactory()
    prime = (2 ** scheme.mers_exp) - 1
    with pytest.raises(ValueError):
        scheme._recover_secret([(1, 5)], prime)


def test_validate_shares():
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()   # already base64-encoded shares
    scheme.save()
    assert scheme.validate_shares(_pick(shares, scheme.k)) is True
    # not a list -> ValueError
    with pytest.raises(ValueError):
        scheme.validate_shares('not-a-list')
    # malformed shares -> caught, returns False
    assert scheme.validate_shares([(1, 'not-base64!!')]) is False


def _make_file(name, content=b'content to encrypt\n'):
    path = settings.MEDIA_ROOT + name
    with open(path, 'wb') as fh:
        fh.write(content)
    return path


def test_encrypt_decrypt_file_roundtrip():
    scheme = ShamirSSFactory(k=2, n=3)
    shares = scheme.get_shares()
    original = b'top secret payload\n'
    path = _make_file('secret.txt', original)

    enc_rel = scheme.encrypt_file(path, shares)
    assert enc_rel.endswith('.enc')
    assert os.path.isfile(settings.MEDIA_ROOT + enc_rel)

    dec_rel = scheme.decrypt_file(settings.MEDIA_ROOT + enc_rel, shares)
    with open(settings.MEDIA_ROOT + dec_rel, 'rb') as fh:
        assert fh.read() == original


def test_encrypt_decrypt_missing_file_returns_none():
    scheme = ShamirSSFactory()
    shares = scheme.get_shares()
    assert scheme.encrypt_file(settings.MEDIA_ROOT + 'nope.txt', shares) is None
    assert scheme.decrypt_file(settings.MEDIA_ROOT + 'nope.enc', shares) is None
