from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from file_handler.models import Folder
from file_handler.models import Document
from random import randint
from django.core.files import File
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
import os


class TestFileHandlerViews(TestCase):
    """ Test for file_handler app views """

    DUMMY_USERNAME = 'dummy'
    DUMMY_PASSWORD = 'dummy_secret'
    DUMMY_EMAIL = 'dummy@dummy.com'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create a test user
        User.objects.create_user(cls.DUMMY_USERNAME, cls.DUMMY_EMAIL, cls.DUMMY_PASSWORD)
        # Create a root folder
        cls.root = Folder.objects.create(name='root', parent=None)
        # create a list of test files, each file is a tuple (filename, file object)
        cls.files = [("test_{}.txt".format(idx), open("test_{}.txt".format(idx), 'w+')) for idx in range(1, 7)]
        for file in cls.files:
            file[1].write('something to fill this up\n')
            file[1].seek(0)

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.DUMMY_USERNAME, password=self.DUMMY_PASSWORD, enforce_csrf_checks=True)

    def test_index(self):
        """ Test for index view """
        response = self.client.get('/')
        self.assertEqual(len(response.context['root_folders']), 1)
        Folder.objects.create(name='root2', parent=None)
        response = self.client.get('/')
        self.assertEqual(len(response.context['root_folders']), 2)

    def test_upload(self):
        """ Test for the upload view """
        upload_url = '/upload/' + str(self.root.id) + '/'
        expected_url = '/folder/' + str(self.root.id) + '/'
        response = self.client.post(upload_url, {'name': self.files[1][0],
                                                 'folder': self.root.id,
                                                 'file': self.files[1][1]}, follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        root_docs = Document.objects.filter(folder=self.root)
        names = []
        for doc in root_docs:
            names.append(doc.name)
        self.assertIn(self.files[1][0], names)
        # remove file from filesystem
        uploaded_document = Document.objects.get(name=self.files[1][0])
        self.remove_file(uploaded_document.file.name)

    def test_folder(self):
        """ Test for folder view """
        response_1 = self.client.get('/folder/' + str(self.root.id) + '/')
        self.assertEqual(response_1.context['root'], self.root)
        root_child = Folder.objects.create(name='root_child', parent=self.root)
        document = Document.objects.create(name=self.files[0][0], folder=self.root, file=File(self.files[0][1]))
        response_2 = self.client.get('/folder/' + str(self.root.id) + '/')
        self.assertIn(document, response_2.context['documents'])
        self.assertIn(root_child, response_2.context['children'])
        response_404 = self.client.get('/folder/' + str(randint(-10, -1)) + '/')
        self.assertEqual(response_404.status_code, 404)
        # remove file from filesystem
        self.remove_file(document.file.name)

    def test_download(self):
        """ Test for download view """
        document = Document.objects.create(name=self.files[2][0], folder=self.root, file=File(self.files[2][1]))
        response = self.client.get('/download/' + str(document.id) + '/')
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.get('Content-Disposition'),
                          "attachment; filename=" + self.files[2][0])
        # remove file from filesystem
        self.remove_file(document.file.name)

    def test_create(self):
        """ Test for create (folder) view """
        create_url = '/create/'
        expected_url = '/folder/' + str(self.root.id) + '/'
        response_1 = self.client.post(create_url, {'name': 'test_folder', 'parent': self.root.id}, follow=True)
        self.assertRedirects(response_1, expected_url=expected_url, status_code=302, target_status_code=200)
        test_folder = Folder.objects.get(name='test_folder')
        self.assertEqual(test_folder.parent, self.root)
        response_2 = self.client.get('/folder/' + str(test_folder.id) + '/')
        self.assertEqual(test_folder, response_2.context['root'])

    def test_delete_doc(self):
        """ Test for delete_doc view """
        folder = Folder.objects.create(name="another folder", parent=self.root)
        doc_to_delete = Document.objects.create(name=self.files[3][0], folder=folder, file=File(self.files[3][1]))
        delete_url = '/delete_doc/' + str(doc_to_delete.id) + "/"
        expected_url = '/folder/' + str(folder.id) + '/'
        response = self.client.post(delete_url, follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        self.assertFalse(os.path.isfile(doc_to_delete.file_path()))
        self.assertRaises(ObjectDoesNotExist, lambda: Document.objects.get(pk=doc_to_delete.id))

    def test_delete(self):
        """ Test for (folder) delete view """
        parent_folder = Folder.objects.create(name="parent", parent=None)
        parent_doc = Document.objects.create(name=self.files[4][0], folder=parent_folder, file=File(self.files[4][1]))
        child_folder = Folder.objects.create(name="child", parent=parent_folder)
        child_doc = Document.objects.create(name=self.files[5][0], folder=child_folder, file=File(self.files[5][1]))
        delete_url = '/delete/' + str(child_folder.id) + "/"
        expected_url = '/folder/' + str(parent_folder.id) + '/'
        response_1 = self.client.post(delete_url, follow=True)
        self.assertRedirects(response_1, expected_url=expected_url, status_code=302, target_status_code=200)
        self.assertRaises(ObjectDoesNotExist, lambda: Folder.objects.get(pk=child_folder.id))
        self.assertFalse(os.path.isfile(child_doc.file_path()))
        self.assertRaises(ObjectDoesNotExist, lambda: Document.objects.get(pk=child_doc.id))
        delete_url = '/delete/' + str(parent_folder.id) + "/"
        expected_url = '/'
        response_2 = self.client.post(delete_url, follow=True)
        self.assertRedirects(response_2, expected_url=expected_url, status_code=302, target_status_code=200)
        self.assertRaises(ObjectDoesNotExist, lambda: Folder.objects.get(pk=parent_folder.id))
        self.assertFalse(os.path.isfile(parent_doc.file_path()))
        self.assertRaises(ObjectDoesNotExist, lambda: Document.objects.get(pk=parent_doc.id))



    @classmethod
    def tearDownClass(cls):
        # remove test files
        for file in cls.files:
            file[1].close()
            os.remove(file[0])
        super().tearDownClass()

    @classmethod
    def remove_file(cls, path):
        """ helper to remove a file from media folder given its path """
        absolute_path = settings.MEDIA_ROOT + path
        if os.path.isfile(absolute_path):
            os.remove(absolute_path)

