from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ShamirSS
from file_handler.models import Document
from .forms import SSForm, EncryptDecryptForm, DivErrorList


@login_required
def index(request):
    """ list all scheme available """
    schemes = ShamirSS.objects.all()
    return render(request, 'shared_secret/index.html', {
        'schemes': schemes
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


def refresh(request, scheme_id):
    # TBD
    pass


@login_required
def encrypt(request, document_id, scheme_id):
    """ encrypt a document """
    document = get_object_or_404(Document, pk=document_id)
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    if request.method == 'POST':
        form = EncryptDecryptForm(scheme.n, True, request.POST, error_class=DivErrorList)
        if form.is_valid() and form.encrypt(document):
            return redirect('/folder/{}'.format(document.folder_id))
    else:
        form = EncryptDecryptForm(scheme.n, initial={'scheme': scheme}, error_class=DivErrorList)
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
        form = EncryptDecryptForm(scheme.n, False, request.POST, initial={'scheme': scheme}, error_class=DivErrorList)
        if form.is_valid() and form.decrypt(document):
            return redirect('/folder/{}'.format(document.folder_id))
    else:
        form = EncryptDecryptForm(scheme.n, False, initial={'scheme': scheme}, error_class=DivErrorList)
    return render(request, 'shared_secret/encdec.html', {
        'form': form,
        'document': document,
        'scheme': scheme,
        'enc': False
    })

