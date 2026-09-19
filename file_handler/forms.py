from django import forms
from file_handler.models import Document, Folder


class MultipleFileInput(forms.ClearableFileInput):
    """ File input that accepts several files at once (Django 5 pattern). """
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """ FileField that cleans a list of uploaded files. """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not isinstance(data, (list, tuple)):
            return [single_clean(data, initial)]
        if not data:
            # empty list: let the parent enforce required/empty validation
            return [single_clean(None, initial)]
        return [single_clean(item, initial) for item in data]


class UploadForm(forms.Form):
    """ Upload one or more files into a folder owned by the user. """
    file = MultipleFileField(label='Files')
    folder = forms.ModelChoiceField(
        queryset=Folder.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['folder'].queryset = Folder.objects.filter(owner=user)


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ('name', 'parent')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # a folder's parent can only be one of the user's own folders
        self.fields['parent'].queryset = Folder.objects.filter(owner=user)


class DeleteDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = []


class DeleteFolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = []

