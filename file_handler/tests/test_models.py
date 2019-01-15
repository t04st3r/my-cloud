from django.test import TestCase
from file_handler.models import Document, Folder
from django.core.files import File
from django.conf import settings
from django.utils import timezone
import os


class FolderTestCases(TestCase):
    """ Test for Folder Model """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        parent = Folder.objects.create(name='parent')
        Folder.objects.create(name='parent2')
        Folder.objects.create(name='child', parent=parent)

    def test_is_parent_folder(self):
        """ Test parent-child relationship between two folders """
        parent = Folder.objects.get(name='parent')
        child = Folder.objects.get(name='child')
        self.assertEqual(parent.parent, None)
        self.assertEqual(child.parent, parent)

    def test_root_folders(self):
        """ Test lists of root folders """
        parent = Folder.objects.get(name='parent')
        parent2 = Folder.objects.get(name='parent2')
        child = Folder.objects.get(name='child')
        root_folders = Folder.root_folders()
        self.assertIn(parent, root_folders)
        self.assertIn(parent2, root_folders)
        self.assertNotIn(child, root_folders)

    def test_folder_name(self):
        """ Test string representation of a folder """
        parent = Folder.objects.get(name='parent')
        self.assertEqual(parent.name, str(parent))


class DocumentTestCases(TestCase):
    """ Test for Document model """

    TEST_FILE_NAME = 'test.xml'
    TEST_FILE_MIME_TYPE = 'text/xml'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        folder = Folder.objects.create(name='Test Folder')
        with open(cls.TEST_FILE_NAME, 'w+') as test_file:
            test_file.write('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
            Document.objects.create(name='Test File', file=File(test_file), folder=folder)

    def test_file_save(self):
        """ Test successful file save """
        path = settings.MEDIA_ROOT + 'documents/%Y/%m/%d/'
        file_path = timezone.now().strftime(path + self.TEST_FILE_NAME)
        self.assertTrue(os.path.isfile(file_path))

    def test_document_name(self):
        """ Test string representation of a document """
        document = Document.objects.get(name='Test File')
        self.assertEqual(document.name, str(document))

    def test_filename(self):
        """ Test document filename """
        document = Document.objects.get(name='Test File')
        self.assertEqual(document.filename(), self.TEST_FILE_NAME)

    def test_mime_type(self):
        """ Test correct file mime type """
        document = Document.objects.get(name='Test File')
        self.assertEqual(self.TEST_FILE_MIME_TYPE, document.file_mime())

    @classmethod
    def tearDownClass(cls):
        document = Document.objects.get(name='Test File')
        os.remove(cls.TEST_FILE_NAME)
        os.remove(document.file.path)
        super().tearDownClass()
