import pytest
from django.forms import HiddenInput
from django.utils.safestring import SafeString

from shared_secret.forms import DivErrorList, EncryptDecryptForm, SSForm
from tests.factories import ShamirSSFactory

pytestmark = pytest.mark.django_db


# ---- SSForm -------------------------------------------------------------------

def test_ssform_valid():
    form = SSForm(data={'name': 'x', 'mers_exp': 89, 'k': 2, 'n': 3})
    assert form.is_valid()


def test_ssform_k_greater_than_n_invalid():
    form = SSForm(data={'name': 'x', 'mers_exp': 89, 'k': 3, 'n': 2})
    assert not form.is_valid()


# ---- EncryptDecryptForm -------------------------------------------------------

def test_no_fields_when_n_shares_none():
    form = EncryptDecryptForm()
    assert 'scheme' not in form.fields


def test_share_fields_and_visible_scheme_for_encrypt():
    scheme = ShamirSSFactory(k=2, n=3)
    form = EncryptDecryptForm(scheme.n, True, initial={'scheme': scheme})
    assert [bf.name for bf in form.share_fields()] == ['share_1', 'share_2', 'share_3']
    assert not isinstance(form.fields['scheme'].widget, HiddenInput)


def test_scheme_hidden_for_decrypt():
    scheme = ShamirSSFactory(k=2, n=3)
    form = EncryptDecryptForm(scheme.n, False, initial={'scheme': scheme})
    assert isinstance(form.fields['scheme'].widget, HiddenInput)


def test_requires_minimum_shares():
    scheme = ShamirSSFactory(k=2, n=3)
    scheme.get_shares()
    scheme.save()
    form = EncryptDecryptForm(scheme.n, True, {'scheme': scheme.id, 'share_1': 'x'})
    assert not form.is_valid()
    assert 'At least 2 shares' in ' '.join(form.non_field_errors())


# ---- DivErrorList (safe, escaped HTML) ---------------------------------------

def test_diverrorlist_empty():
    assert str(DivErrorList()) == ''


def test_diverrorlist_is_safe_html():
    out = str(DivErrorList(['Bad value']))
    assert isinstance(out, SafeString)
    assert '<div class="errorlist alert alert-danger">' in out
    assert 'Bad value' in out


def test_diverrorlist_escapes_content():
    out = str(DivErrorList(['<script>evil</script>']))
    assert '<script>' not in out
    assert '&lt;script&gt;' in out
