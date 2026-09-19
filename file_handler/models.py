from django.db import models
from django.utils import timezone
from django.conf import settings
from mptt.models import MPTTModel, TreeForeignKey
from shared_secret.models import ShamirSS
import os
import magic


class Folder(MPTTModel):
    name = models.CharField(max_length=200)
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='folders')

    class MPTTMeta:
        order_insertion_by = ['id']

    def __str__(self):
        return self.name

    @staticmethod
    def root_folders(user):
        """ Return the root folders owned by the given user """
        return Folder.objects.filter(parent__isnull=True, owner=user)

    def is_empty(self):
        """ Return true if the folder is empty """
        return self.is_leaf_node() and self.documents.count() == 0


class Document(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    creation_date = models.DateTimeField(default=timezone.now, blank=True)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, related_name='documents')
    scheme = models.ForeignKey(ShamirSS, on_delete=models.CASCADE, null=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='documents')

    def __str__(self):
        return self.name

    def file_url(self):
        """ Return the URL to the file (local media URL or a signed Spaces URL) """
        return self.file.url

    def file_path(self):
        """ Return the local filesystem path to the file (local storage only) """
        return settings.MEDIA_ROOT + self.file.name

    def filename(self):
        """ Return file name """
        return os.path.basename(self.file.name)

    def full_path(self):
        """ Return the Linux-like path of the document in the folder tree, e.g. /docs/report.txt """
        if self.folder is None:
            return '/' + self.name
        ancestors = self.folder.get_ancestors(include_self=True)
        return '/' + '/'.join(a.name for a in ancestors) + '/' + self.name

    def file_mime(self):
        """ Return the file mime type (reads a small buffer via the storage backend) """
        with self.file.open('rb') as f:
            return magic.from_buffer(f.read(2048), mime=True)
