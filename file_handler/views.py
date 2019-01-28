from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils.encoding import smart_str
from file_handler.forms import DocumentForm, FolderForm, DeleteDocumentForm, DeleteFolderForm
from .models import Folder, Document
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed


@login_required
def index(request):
    """ display root of the filesystem tree """
    root_folders = Folder.root_folders()
    form = DeleteFolderForm()
    return render(request, 'file_handler/index.html', {
        'root_folders': root_folders,
        'form': form
    })


@login_required
def upload(request, folder_id):
    """ upload a file on the specified folder """
    folder = get_object_or_404(Folder, pk=folder_id)
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('folder', folder_id=folder_id)
    else:
        form = DocumentForm(initial={'folder': folder})
    return render(request, 'file_handler/upload.html', {
        'form': form,
        'folder': folder
    })


@login_required
def folder(request, folder_id):
    """ Show content of a particular folder """
    root = get_object_or_404(Folder, pk=folder_id)
    children = Folder.objects.filter(parent=folder_id)
    documents = Document.objects.filter(folder=folder_id)
    dd_form = DeleteDocumentForm()
    df_form = DeleteFolderForm()
    return render(request, 'file_handler/folder.html', {
        'root': root,
        'children': children,
        'documents': documents,
        'dd_form': dd_form,
        'df_form': df_form
    })


@login_required
def download(request, file_id):
    """ download a specified file """
    document = get_object_or_404(Document, pk=file_id)
    response = HttpResponse(document.file, content_type=document.file_mime)
    response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(document.filename())
    response['X-Sendfile'] = smart_str(document.filename())
    return response


@login_required
def create(request):
    """ create a folder """
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


@login_required
def delete_doc(request, file_id):
    """ delete a document """
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=file_id)
        form = DeleteDocumentForm(request.POST, instance=document)
        if form.is_valid():
            folder = document.folder
            document.delete()
        return redirect('folder', folder_id=folder.id)
    return HttpResponseNotAllowed(['POST'])


@login_required()
def delete(request, folder_id):
    """ Delete a folder """
    if request.method == 'POST':
        folder = get_object_or_404(Folder, pk=folder_id)
        parent = folder.parent
        form = DeleteFolderForm(request.POST, instance=folder)
        if form.is_valid():
            folder.delete()
        if parent is None:
            return redirect('index')
        return redirect('folder', folder_id=parent.id)
