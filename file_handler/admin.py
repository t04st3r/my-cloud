from django.contrib import admin

from .models import Document, Folder

admin.site.register((Document, Folder))
