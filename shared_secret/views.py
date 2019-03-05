from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ShamirSS
from .forms import SSForm, DivErrorList


@login_required
def index(request):
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
            form.save()
            return redirect('index')
    else:
        form = SSForm()
    return render(request, 'shared_secret/create.html', {
        'form': form
    })

@login_required
def generate(request, scheme_id):
    scheme = get_object_or_404(ShamirSS, pk=scheme_id)
    shares = scheme.get_shares()
    return render(request, 'shared_secret/generate.html', {
        'shares': shares,
        'scheme': scheme
    })
