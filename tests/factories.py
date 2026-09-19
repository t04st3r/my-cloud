"""factory_boy factories for the test suite.

All file content is created in-memory (``factory.django.FileField(data=...)``) and
written into the per-test temporary ``MEDIA_ROOT`` set up by the autouse
``_isolated_media`` fixture in ``conftest.py`` — nothing touches the real media dir.
"""
import factory
from django.contrib.auth.models import User

from file_handler.models import Document, Folder
from shared_secret.models import ShamirSS


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: 'user%d' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.com' % o.username)

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or 'pass12345')
        if create:
            self.save()


class FolderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Folder

    name = factory.Sequence(lambda n: 'folder%d' % n)
    parent = None
    owner = factory.SubFactory(UserFactory)


class ShamirSSFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShamirSS

    name = factory.Sequence(lambda n: 'scheme%d' % n)
    mers_exp = 89
    k = 2
    n = 3
    secret = ''
    owner = factory.SubFactory(UserFactory)


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    name = factory.Sequence(lambda n: 'doc%d.txt' % n)
    owner = factory.SubFactory(UserFactory)
    # a document's folder defaults to one owned by the same user
    folder = factory.SubFactory(FolderFactory, owner=factory.SelfAttribute('..owner'))
    file = factory.django.FileField(filename='doc.txt', data=b'test file content\n')
    scheme = None
