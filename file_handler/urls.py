from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('folder/<int:folder_id>/', views.folder, name='folder'),
    path('upload', views.upload, name='upload'),
    path('upload/<int:folder_id>/', views.upload, name='upload'),
    path('create/', views.create, name='create'),
    path('download/<int:file_id>/', views.download, name='download'),
]
