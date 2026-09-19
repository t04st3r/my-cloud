from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils.encoding import smart_str
from file_handler.forms import UploadForm, FolderForm, DeleteDocumentForm, DeleteFolderForm
from .models import Folder, Document
from shared_secret.models import ShamirSS
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from .utils import get_earliest_objects_or_none


@login_required
def index(request):
    """ display root of the filesystem tree """
    root_folders = Folder.root_folders(request.user)
    form = DeleteFolderForm()
    return render(request, 'file_handler/index.html', {
        'root_folders': root_folders,
        'form': form
    })


@login_required
def upload(request, folder_id):
    """ upload one or more files on the specified folder """
    folder = get_object_or_404(Folder, pk=folder_id, owner=request.user)
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            target = form.cleaned_data['folder']
            for uploaded in form.cleaned_data['file']:
                document = Document(folder=target, file=uploaded, owner=request.user)
                # Persist first so the storage backend resolves a unique file name,
                # then use that reliable name as the document's display name.
                document.save()
                document.name = document.filename()
                document.save(update_fields=['name'])
            return redirect('folder', folder_id=target.id)
    else:
        form = UploadForm(initial={'folder': folder}, user=request.user)
    return render(request, 'file_handler/upload.html', {
        'form': form,
        'folder': folder
    })


@login_required
def folder(request, folder_id):
    """ Show content of a particular folder """
    root = get_object_or_404(Folder, pk=folder_id, owner=request.user)
    children = Folder.objects.filter(parent=folder_id, owner=request.user)
    documents = Document.objects.filter(folder=folder_id, owner=request.user)
    scheme = get_earliest_objects_or_none(ShamirSS, owner=request.user)
    dd_form = DeleteDocumentForm()
    df_form = DeleteFolderForm()
    return render(request, 'file_handler/folder.html', {
        'root': root,
        'children': children,
        'documents': documents,
        'dd_form': dd_form,
        'df_form': df_form,
        'scheme': scheme
    })


@login_required
def download(request, file_id):
    """ download a specified file """
    document = get_object_or_404(Document, pk=file_id, owner=request.user)
    response = HttpResponse(document.file, content_type=document.file_mime)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(document.filename())
    response['X-Sendfile'] = smart_str(document.filename())
    return response


@login_required
def create(request, folder_id=None):
    """ create a folder """
    parent = get_object_or_404(Folder, pk=folder_id, owner=request.user) if folder_id is not None else None
    if request.method == 'POST':
        form = FolderForm(request.POST, user=request.user)
        if form.is_valid():
            folder = form.save(commit=False)
            folder.owner = request.user
            folder.save()
        if form.instance.parent_id is None:
            return redirect('/')
        return redirect('folder', folder_id=form.instance.parent_id)
    else:
        form = FolderForm(initial={'parent': parent}, user=request.user)
        return render(request, 'file_handler/new_folder.html', {
            'form': form,
            'parent': parent
        })


@login_required
def delete_doc(request, file_id):
    """ delete a document """
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=file_id, owner=request.user)
        form = DeleteDocumentForm(request.POST, instance=document)
        if form.is_valid():  # pragma: no branch - empty form is always valid
            folder = document.folder
            document.delete()
        return redirect('folder', folder_id=folder.id)
    return HttpResponseNotAllowed(['POST'])


@login_required()
def delete(request, folder_id):
    """ Delete a folder """
    if request.method == 'POST':
        folder = get_object_or_404(Folder, pk=folder_id, owner=request.user)
        parent = folder.parent
        form = DeleteFolderForm(request.POST, instance=folder)
        if form.is_valid():  # pragma: no branch - empty form is always valid
            folder.delete()
        if parent is None:
            return redirect('/')
        return redirect('folder', folder_id=parent.id)
    return HttpResponseNotAllowed(['POST'])
