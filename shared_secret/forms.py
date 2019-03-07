from django import forms
from file_handler.models import ShamirSS


class EncryptForm(forms.Form):
    """ dynamic number of fields based on scheme """
    def __init__(self, n_shares=None, *args, **kwargs):
        super(EncryptForm, self).__init__(*args, **kwargs)
        if n_shares is not None:
            for i in range(0, n_shares):
                fieldname = "share_{}".format(i + 1)
                self.fields[fieldname] = forms.IntegerField()
                self.fields[fieldname].widget = forms.TextInput()

    scheme = forms.ModelChoiceField(queryset=ShamirSS.objects.all(), empty_label=None)

    def clean(self):
        cleaned_data = super().clean()
        # TBD


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
