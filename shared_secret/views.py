from django.shortcuts import render, redirect
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
