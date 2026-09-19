from rest_framework import generics
from file_handler.models import Folder
from .serializers import FolderSerializer


class RootFolderList(generics.ListCreateAPIView):
    serializer_class = FolderSerializer

    def get_queryset(self):
        return Folder.root_folders(self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FolderDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FolderSerializer

    def get_queryset(self):
        return Folder.objects.filter(owner=self.request.user)
