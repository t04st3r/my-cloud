from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:folder_id>/', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('upload/<int:folder_id>/', views.upload, name='upload'),
]