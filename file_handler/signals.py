from django.db.models.signals import pre_save
from .models import Folder
from django.dispatch import receiver


@receiver(pre_save, sender=Folder)
def set_folder_path(instance, **kwargs):
    """ Set the folder path """
    if instance.parent is None:
        return
    if instance.parent.path is None:
        instance.path = instance.parent.id
    else:
        instance.path = instance.parent.path + ',' + str(instance.parent.id)
