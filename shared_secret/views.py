from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ShamirSS

@login_required
def index(request):
    """ display  a list of available sss schemes """
    return ShamirSS.objects.all()
