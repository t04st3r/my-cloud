from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotAllowed
from .models import ShamirSS
from file_handler.models import Document
from .forms import SSForm, EncryptDecryptForm, DeleteRelatedForm, DeleteSchemeForm, DivErrorList, RefreshForm


@login_required
def index(request):
    """ list all schemes available """
    schemes = ShamirSS.objects.all()
    delete_form = DeleteSchemeForm()
    refresh_form = RefreshForm()
    return render(request, 'shared_secret/index.html', {
        'schemes': schemes,
        'd_form': delete_form,
        'r_form': refresh_form
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
def delete_related(request, scheme_id):
    """ delete all related documents to a given scheme """
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    documents = get_list_or_404(Document, scheme=scheme)
    form = DeleteRelatedForm()
    if request.method == 'POST':
        Document.objects.filter(scheme=scheme).delete()
        return redirect('/s')
    else:
        return render(request, 'shared_secret/del_related.html', {
            'scheme': scheme,
            'documents': documents,
            'form': form
        })


@login_required
def delete(request, scheme_id):
    """ delete a scheme """
    if request.method == 'POST':
        scheme = get_object_or_404(ShamirSS, pk=scheme_id)
        documents = scheme.document_set.all()
        if len(documents) > 0:
            return redirect('/s/delete_related/{}'.format(scheme.id))
        scheme.delete()
        return redirect('/s')
    return HttpResponseNotAllowed([request.method])


@login_required
def refresh(request, scheme_id):
    """ regenerate shares for a given scheme """
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    if request.method == 'POST':
        documents = scheme.document_set.all()
        if len(documents) > 0:
            return redirect('/s/delete_related/{}'.format(scheme.id))
        shares = scheme.get_shares()
        scheme.save()
        return render(request, 'shared_secret/generate.html', {
            'shares': shares,
            'scheme': scheme
        })
    return HttpResponseNotAllowed([request.method])


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
