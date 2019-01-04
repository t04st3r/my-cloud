from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils.encoding import smart_str
from file_handler.forms import DocumentForm, FolderForm
from .models import Folder, Document
from django.contrib.auth.decorators import login_required


@login_required
def upload(request, folder_id):
    folder = get_object_or_404(Folder, pk=folder_id)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('index', folder_id=folder_id)
    else:
        form = DocumentForm()
        return render(request, 'file_handler/upload.html', {
            'form': form,
            'folder': folder
        })


@login_required
def index(request, folder_id=1):
    root = get_object_or_404(Folder, pk=folder_id)
    children = Folder.objects.filter(parent=folder_id)
    documents = Document.objects.filter(folder=folder_id)
    return render(request, 'file_handler/index.html', {
        'root': root,
        'children': children,
        'documents': documents
    })


@login_required
def download(request, file_id):
    document = get_object_or_404(Document, pk=file_id)
    response = HttpResponse(document.file, content_type=document.file_mime)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(document.filename())
    response['X-Sendfile'] = smart_str(document.filename())
    return response


@login_required
def create(request, parent_id):
    parent = get_object_or_404(Folder, pk=parent_id)
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            new_folder.parent_id = parent.id
            new_folder.save()
            return redirect('index', folder_id=parent_id)
    else:
        form = FolderForm()
        return render(request, 'file_handler/new_folder.html', {
            'form': form,
            'folder': parent
        })


