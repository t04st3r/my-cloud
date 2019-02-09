from rest_framework import serializers
from file_handler.models import Folder, Document


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ('id', 'name', 'creation_date', 'filename', 'file')


class FolderSerializer(serializers.ModelSerializer):
    documents = DocumentSerializer(many=True)

    class Meta:
        model = Folder
        fields = ('id', 'name', 'creation_date', 'parent', 'children', 'documents')



