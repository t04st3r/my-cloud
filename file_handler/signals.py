from django.db.models.signals import post_delete
from .models import Document
from django.dispatch import receiver
import os


@receiver(post_delete, sender=Document)
def delete_file(instance, **kwargs):
    """ delete file physically after removal from db """
    file_name = instance.file_path()
    os.remove(file_name)
