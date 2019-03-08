from django import forms
from shared_secret.models import ShamirSS
from django.core.files import File
import os


class EncryptForm(forms.Form):
    """ dynamic number of shares fields based n_shares """

    scheme = forms.ModelChoiceField(queryset=ShamirSS.objects.all(), empty_label=None)

    def __init__(self, n_shares=None, *args, **kwargs):
        super(EncryptForm, self).__init__(*args, **kwargs)
        if n_shares is not None:
            for i in range(0, n_shares):
                field_name = "share_{}".format(i + 1)
                self.fields[field_name] = forms.IntegerField(required=False)
                self.fields[field_name].widget = forms.TextInput()

    def get_shares(self):
        """ return submitted shares and scheme """
        cleaned_data = super().clean()
        shares = []
        scheme = cleaned_data.get('scheme')
        for i in range(0, scheme.n):
            share = cleaned_data.get("share_{}".format(i + 1))
            if share is not None:
                shares.append((i + 1, share))
        return scheme, shares

    def clean(self):
        """ validate min number of shares and if shares can recover the secret """
        scheme, shares = self.get_shares()
        if len(shares) < scheme.k:
            raise forms.ValidationError("At least {} shares are needed to encrypt the file".format(scheme.k))
        if not scheme.validate_shares(shares):
            raise forms.ValidationError("Wrong shares values")

    def save(self, document):
        """ encrypt the document file and update its model, return True if everything goes smooth """
        scheme, shares = self.get_shares()
        enc_file_path = scheme.encrypt_file(document.file_path(), shares)
        if enc_file_path is None:
            return False
        os.remove(document.file_path())
        document.file = File(open(enc_file_path, 'r'))
        document.save()
        return True


class SSForm(forms.ModelForm):

    class Meta:
        model = ShamirSS
        fields = ('name', 'mers_exp', 'k', 'n')
        labels = {
            'name': 'Scheme name',
            'mers_exp': 'Field size exponent (Mersenne prime notation)',
            'k': 'Minimum number of shares to decrypt (k)',
            'n': 'Total shares to generate (n)'
        }

    def clean(self):
        cleaned_data = super().clean()
        n = cleaned_data.get('n')
        k = cleaned_data.get('k')
        if k and n and int(k) > int(n):
            raise forms.ValidationError("The value of k cannot be greater than n (k = {} n = {})".format(k, n))


class DivErrorList(forms.utils.ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return '<div class="errorlist alert alert-danger">%s</div>' % ''.join(['<div class="error">%s</div>' % e for e in self])
