from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('folder/', views.RootFolderList.as_view()),
    path('folder/<int:pk>/', views.FolderDetail.as_view()),
]

urlpatterns += format_suffix_patterns(urlpatterns)
