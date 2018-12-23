from django import forms
from file_handler.models import Document


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document,
        fields = ('name', 'file')
