from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('refresh/<int:scheme_id>/', views.refresh, name='refresh'),
    path('encrypt/<int:document_id>/<int:scheme_id>/', views.encrypt, name='encrypt'),
    path('decrypt/<int:document_id>/', views.decrypt, name='decrypt')
]