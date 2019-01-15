from rest_framework import serializers
from file_handler.models import Folder


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
