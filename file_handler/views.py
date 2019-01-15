from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils.encoding import smart_str
from file_handler.forms import DocumentForm, FolderForm
from .models import Folder, Document
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    root_folders = Folder.root_folders()
    return render(request, 'file_handler/index.html', {
        'root_folders': root_folders
    })


@login_required
def upload(request, folder_id):
    folder = get_object_or_404(Folder, pk=folder_id)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('folder', folder_id=folder_id)
    else:
        form = DocumentForm()
    return render(request, 'file_handler/upload.html', {
        'form': form,
        'folder': folder
    })


@login_required
def folder(request, folder_id):
    root = get_object_or_404(Folder, pk=folder_id)
    children = Folder.objects.filter(parent=folder_id)
    documents = Document.objects.filter(folder=folder_id)
    return render(request, 'file_handler/folder.html', {
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
def create(request):
    if request.method == 'POST':
        form = FolderForm(request.POST)
        if form.is_valid():
            form.save()
            if form.instance.parent_id is None:
                return redirect('index')
            return redirect('folder', folder_id=form.instance.parent_id)
    else:
        form = FolderForm()
        return render(request, 'file_handler/new_folder.html', {
            'form': form,
        })


