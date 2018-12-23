from django.db import models


class Folder(models.Model):
    name = models.CharField(max_length=200)
    creation_date = models.DateTimeField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True)


class Document(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    creation_date = models.DateTimeField()
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True)
