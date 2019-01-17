from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from file_handler.models import Folder
from file_handler.models import Document
from random import randint
from django.core.files import File
import os
import filecmp


class TestFileHandlerViews(TestCase):
    """ Test for file_handler app views """

    DUMMY_USERNAME = 'dummy'
    DUMMY_PASSWORD = 'dummy_secret'
    DUMMY_EMAIL = 'dummy@dummy.com'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(cls.DUMMY_USERNAME, cls.DUMMY_EMAIL, cls.DUMMY_PASSWORD)
        # Create a root folder
        cls.root = Folder.objects.create(name='root', parent=None)
        # create a list of test files
        cls.files = [("test_{}.txt".format(idx), open("test_{}.txt".format(idx), 'w+')) for idx in range(1, 3)]
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


    @classmethod
    def tearDownClass(cls):
        for file in cls.files:
            file[1].close()
            os.remove(file[0])
            os.system('rm -f media/documents/2019/01/13/'+file[0])
        super().tearDownClass()
