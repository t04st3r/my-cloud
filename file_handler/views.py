from django.shortcuts import render, redirect, get_object_or_404
from file_handler.forms import DocumentForm
from .models import Folder, Document


def upload(request, folder_id):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = DocumentForm()
        return render(request, 'file_handler/upload.html', {
            'form': form,
            'folder_id': folder_id
        })


def index(request, folder_id=1):
    root = get_object_or_404(Folder, pk=folder_id)
    children = Folder.objects.filter(parent=folder_id)
    documents = Document.objects.filter(folder=folder_id)
    return render(request, 'file_handler/index.html', {
        'root': root,
        'children': children,
        'documents': documents
    })
