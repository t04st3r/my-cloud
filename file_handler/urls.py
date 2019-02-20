from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('folder/<int:folder_id>/', views.folder, name='folder'),
    path('upload', views.upload, name='upload'),
    path('upload/<int:folder_id>/', views.upload, name='upload'),
    path('create/<int:folder_id>/', views.create, name='create'),
    path('create', views.create, name='create'),
    path('download/<int:file_id>/', views.download, name='download'),
    path('delete_doc/<int:file_id>/', views.delete_doc, name='delete_doc'),
    path('delete/<int:folder_id>/', views.delete, name='delete'),
]
