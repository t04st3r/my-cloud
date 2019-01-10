from django.db import models
from django.utils import timezone
from django.conf import settings
import os
import magic


class Folder(models.Model):
    name = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.name

    @staticmethod
    def root_folders():
        return Folder.objects.filter(parent__isnull=True)


class Document(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name

    def filename(self):
        return os.path.basename(self.file.name)

    def file_mime(self):
        return magic.from_file(settings.MEDIA_ROOT + self.file.name, mime=True)
