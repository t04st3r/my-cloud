from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:folder_id>/', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('upload/<int:folder_id>/', views.upload, name='upload'),
    path('create/<int:parent_id>/', views.create, name='create'),
    path('download/<int:file_id>/', views.download, name='download'),
]