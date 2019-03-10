from django import forms
from shared_secret.models import ShamirSS
import os


class EncryptDecryptForm(forms.Form):
    """ dynamic number of shares fields based n_shares """
    def __init__(self, n_shares=None, enc=True, *args, **kwargs):
        super(EncryptDecryptForm, self).__init__(*args, **kwargs)
        if n_shares is not None:
            self.fields['scheme'] = forms.ModelChoiceField(queryset=ShamirSS.objects.all(), empty_label=None)
            if not enc:
                self.fields['scheme'].widget = forms.HiddenInput()
            for i in range(0, n_shares):
                field_name = "share_{}".format(i + 1)
                self.fields[field_name] = forms.CharField(required=False)
                self.fields[field_name].widget = forms.PasswordInput()

    def get_shares(self):
        """ return submitted shares and scheme """
        cleaned_data = super().clean()
        shares = []
        scheme = cleaned_data.get('scheme')
        for i in range(0, scheme.n):
            share = cleaned_data.get("share_{}".format(i + 1))
            if len(share) > 0:
                shares.append((i + 1, share))
        return scheme, shares

    def clean(self):
        """ validate min number of shares and if shares can recover the secret """
        scheme, shares = self.get_shares()
        if len(shares) < scheme.k:
            raise forms.ValidationError("At least {} shares are needed to encrypt the file".format(scheme.k))
        if not scheme.validate_shares(shares):
            raise forms.ValidationError("Wrong shares values")

    def encrypt(self, document):
        """ encrypt the document file and update its model, return True if everything goes smooth """
        if document.scheme is not None:
            return False
        scheme, shares = self.get_shares()
        enc_file_path = scheme.encrypt_file(document.file_path(), shares)
        if enc_file_path is None:
            return False
        os.remove(document.file_path())
        document.file.name = enc_file_path
        document.scheme = scheme
        document.save()
        return True

    def decrypt(self, document):
        """ decrypt the document file and update its model, return True if everything goes smooth """
        if document.scheme is None:
            return False
        scheme, shares = self.get_shares()
        dec_file_path = scheme.decrypt_file(document.file_path(), shares)
        if dec_file_path is None:
            return False
        os.remove(document.file_path())
        document.file.name = dec_file_path
        document.scheme = None
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


class DeleteSchemeForm(forms.ModelForm):
    class Meta:
        model = ShamirSS
        fields = []


class DeleteRelatedForm(forms.Form):
    pass


class RefreshForm(forms.Form):
    pass
