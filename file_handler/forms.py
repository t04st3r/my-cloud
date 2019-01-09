from django import forms
from file_handler.models import Document, Folder


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ('name', 'file', 'folder')


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name', 'parent')

