from django import forms
from file_handler.models import ShamirSS


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
            raise forms.ValidationError("The value of k cannot be greater than n !! (k = {} n = {})".format(k, n))


class DivErrorList(forms.utils.ErrorList):
    def __str__(self):
        return self.as_divs()

    def as_divs(self):
        if not self:
            return ''
        return '<div class="errorlist alert alert-danger">%s</div>' % ''.join(['<div class="error">%s</div>' % e for e in self])
