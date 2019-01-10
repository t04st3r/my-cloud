from django.test import TestCase
from file_handler.models import Document, Folder
from django.core.files import File
import os, shutil


class FolderTestCases(TestCase):
    """ Test for Folder Model """

    def setUp(self):
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

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_file = open('test.txt', 'w+')
        folder = Folder.objects.create(name='Test Folder')
        Document.objects.create(name='Test File', file=File(test_file), folder=folder)
        test_file.close()

    def test_document_name(self):
        """ Test string representation of a document """
        document = Document.objects.get(name='Test File')
        self.assertEqual(document.name, str(document))

    def test_filename(self):
        """ Test document filename """
        document = Document.objects.get(name='Test File')
        self.assertEqual(document.filename(), 'test.txt')

    @classmethod
    def tearDownClass(cls):
        document = Document.objects.get(name='Test File')
        os.remove('test.txt')
        path = document.file.path.replace('test.txt', '')
        shutil.rmtree(path, ignore_errors=True)
        super().tearDownClass()
