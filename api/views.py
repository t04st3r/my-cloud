from rest_framework import generics
from file_handler.models import Folder
from .serializers import FolderSerializer


class RootFolderList(generics.ListCreateAPIView):
    queryset = Folder.root_folders()
    serializer_class = FolderSerializer


class FolderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
