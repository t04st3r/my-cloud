from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Document


@receiver(post_delete, sender=Document)
def delete_file(instance, **kwargs):
    """ delete the underlying file from storage after the document row is removed """
    # FieldFile.delete() is a safe no-op when there is no associated file.
    instance.file.delete(save=False)
