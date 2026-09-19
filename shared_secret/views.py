from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http.response import HttpResponseNotAllowed
from .models import ShamirSS
from file_handler.models import Document
from .forms import SSForm, EncryptDecryptForm, DivErrorList


@login_required
def index(request):
    """ list all schemes available, annotated with the number of files each encrypts """
    schemes = ShamirSS.objects.annotate(doc_count=Count('document')).prefetch_related('document_set__folder')
    return render(request, 'shared_secret/index.html', {
        'schemes': schemes,
    })


@login_required
def create(request):
    """ create a new scheme """
    if request.method == 'POST':
        form = SSForm(request.POST, error_class=DivErrorList)
        if form.is_valid():
            # get shares and store hashed secret
            shares = form.instance.get_shares()
            form.save()
            return render(request, 'shared_secret/generate.html', {
                'shares': shares,
                'scheme': form.instance
            })
    else:
        form = SSForm()
    return render(request, 'shared_secret/create.html', {
        'form': form
    })


@login_required
def delete(request, scheme_id):
    """ delete a scheme.

    ``mode`` (POST) decides what happens to the files the scheme encrypts:
      * ``with_files``  -> delete the scheme and its encrypted files (cascade)
      * ``scheme_only`` -> keep the (now unrecoverable) files, detaching them first
    A scheme that has encrypted files requires an explicit mode (the JS modal).
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    mode = request.POST.get('mode')
    has_docs = Document.objects.filter(scheme=scheme).exists()
    if has_docs and mode not in ('with_files', 'scheme_only'):
        return redirect('/s')
    if mode == 'scheme_only':
        # Detach the documents so the cascade does not delete their files.
        Document.objects.filter(scheme=scheme).update(scheme=None)
    scheme.delete()
    return redirect('/s')


@login_required
def refresh(request, scheme_id):
    """ regenerate shares for a given scheme.

    ``mode`` (POST) decides what happens to the files the scheme encrypts:
      * ``with_files``  -> delete the affected files, then regenerate
      * ``scheme_only`` -> regenerate only (the existing files become unrecoverable)
    A scheme that has encrypted files requires an explicit mode (the JS modal).
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    mode = request.POST.get('mode')
    has_docs = Document.objects.filter(scheme=scheme).exists()
    if has_docs and mode not in ('with_files', 'scheme_only'):
        return redirect('/s')
    if mode == 'with_files':
        # Deleting the documents removes their files from disk (post_delete signal).
        Document.objects.filter(scheme=scheme).delete()
    shares = scheme.get_shares()
    scheme.save()
    return render(request, 'shared_secret/generate.html', {
        'shares': shares,
        'scheme': scheme
    })


@login_required
def encrypt(request, document_id, scheme_id):
    """ encrypt a document """
    document = get_object_or_404(Document, pk=document_id)
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    if request.method == 'POST':
        form = EncryptDecryptForm(
            scheme.n, True, request.POST, error_class=DivErrorList)
        if form.is_valid() and form.encrypt(document):
            return redirect('/folder/{}'.format(document.folder_id))
    else:
        form = EncryptDecryptForm(
            scheme.n, initial={'scheme': scheme}, error_class=DivErrorList)
    return render(request, 'shared_secret/encdec.html', {
        'form': form,
        'document': document,
        'scheme': scheme,
        'enc': True
    })


@login_required
def decrypt(request, document_id):
    """ encrypt a document """
    document = get_object_or_404(Document, pk=document_id)
    scheme = get_object_or_404(ShamirSS, pk=document.scheme_id)
    if request.method == 'POST':
        form = EncryptDecryptForm(scheme.n, False, request.POST, initial={
                                  'scheme': scheme}, error_class=DivErrorList)
        if form.is_valid() and form.decrypt(document):
            return redirect('/folder/{}'.format(document.folder_id))
    else:
        form = EncryptDecryptForm(scheme.n, False, initial={
                                  'scheme': scheme}, error_class=DivErrorList)
    return render(request, 'shared_secret/encdec.html', {
        'form': form,
        'document': document,
        'scheme': scheme,
        'enc': False
    })
