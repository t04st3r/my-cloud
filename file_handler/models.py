from django.db import models
from django.utils import timezone
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
import os
import magic


class Folder(MPTTModel):
    name = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['id']

    def __str__(self):
        return self.name

    @staticmethod
    def root_folders():
        """ Return all root folders """
        return Folder.objects.filter(parent__isnull=True)

    def is_empty(self):
        """ Return true if the folder is empty """
        return self.is_leaf_node() and self.document_set.count() == 0


class Document(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

    def file_path(self):
        """ Return complete path to the file """
        return settings.MEDIA_ROOT + self.file.name

    def filename(self):
        """ Return file name """
        return os.path.basename(self.file.name)

    def file_mime(self):
        """ Return file mime type """
        return magic.from_file(settings.MEDIA_ROOT + self.file.name, mime=True)
