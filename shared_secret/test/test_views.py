from django.test import TestCase, Client
from django.contrib.auth.models import User
from shared_secret.models import ShamirSS
from file_handler.models import Document, Folder
from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist
import random
import os


class TestSharedSecretViews(TestCase):
    """ Test for shared_secret app views """

    DUMMY_USERNAME = 'dummy'
    DUMMY_PASSWORD = 'dummy_secret'
    DUMMY_EMAIL = 'dummy@dummy.com'

    @classmethod
    def setUpClass(cls):
        # create a test user
        User.objects.create_user(cls.DUMMY_USERNAME, cls.DUMMY_EMAIL, cls.DUMMY_PASSWORD)
        # create folder, document models and a test file
        cls.folder = Folder.objects.create(name='test_folder')
        with open('test_file.txt', 'w+') as file:
            file.write('something to fill this up\n\n')
            cls.document = Document.objects.create(name='test_doc', folder=cls.folder, file=File(file))
        os.remove('test_file.txt')

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.DUMMY_USERNAME, password=self.DUMMY_PASSWORD, enforce_csrf_checks=True)
        self.scheme_data = {'name': 'test', 'mers_exp': 107, 'k': 4, 'n': 18}

    def test_index(self):
        """ Test for index view """
        response = self.client.get('/s/')
        self.assertEqual(response.status_code, 200)
        # check for empty list if no scheme is created
        self.assertEqual(len(response.context['schemes']), 0)
        scheme = ShamirSS(**self.scheme_data)
        scheme.save()
        response = self.client.get('/s/')
        # check for created scheme
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['schemes']), 1)
        # check for correct scheme fields
        self.assertEqual(response.context['schemes'][0].name, scheme.name)
        self.assertEqual(response.context['schemes'][0].mers_exp, scheme.mers_exp)
        self.assertEqual(response.context['schemes'][0].k, scheme.k)
        self.assertEqual(response.context['schemes'][0].n, scheme.n)

    def test_create(self):
        """ Test for create view """
        create_url = '/s/create/'
        response = self.client.get(create_url)
        self.assertEqual(response.status_code, 200)
        # check for correct creation
        response = self.client.post(create_url, self.scheme_data)
        self.assertEqual(response.status_code, 200)
        # check for correct number of shares generation upon creation
        # (correctness of shares already tested on test_models.py)
        self.assertEqual(len(response.context['shares']), self.scheme_data['n'])

    def test_delete_related(self):
        """ Test for delete_related view """
        del_url = '/s/delete_related/{}/'
        response = self.client.get(del_url.format(random.randint(1, 100)))
        # check for non existent scheme
        self.assertEqual(response.status_code, 404)
        scheme = ShamirSS(**self.scheme_data)
        scheme.save()
        # check for scheme without related documents
        response = self.client.get(del_url.format(scheme.id))
        self.assertEqual(response.status_code, 404)
        # link a document
        self.document.scheme = scheme
        self.document.save()
        # check for scheme with related documents
        response = self.client.get(del_url.format(scheme.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['documents']), 1)

    def test_delete_scheme(self):
        """ Test for delete view """
        del_url = '/s/delete/{}/'
        response = self.client.post(del_url.format(random.randint(1, 100)))
        # check for delete non existent scheme
        self.assertEqual(response.status_code, 404)
        scheme = ShamirSS(**self.scheme_data)
        scheme.save()
        # check for wrong http method
        response = self.client.get(del_url.format(scheme.id))
        self.assertEqual(response.status_code, 405)
        # link a document
        self.document.scheme = scheme
        self.document.save()
        # check correct redirection to delete_related
        expected_url = '/s/delete_related/{}/'.format(scheme.id)
        response = self.client.post(del_url.format(scheme.id), follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        # unlink document
        self.document.scheme = None
        self.document.save()
        # check correct redirection after successful delete
        response = self.client.post(del_url.format(scheme.id), follow=True)
        self.assertRedirects(response, expected_url='/s/', status_code=302, target_status_code=200)
        self.assertRaises(ObjectDoesNotExist, lambda: ShamirSS.objects.get(pk=scheme.id))

    def test_refresh_scheme(self):
        """ Test for refresh scheme """
        refresh_url = '/s/refresh/{}/'
        response = self.client.post(refresh_url.format(random.randint(1, 100)))
        # check for delete non existent scheme
        self.assertEqual(response.status_code, 404)
        scheme = ShamirSS(**self.scheme_data)
        shares = scheme.get_shares()
        scheme.save()
        # check for wrong http method error
        response = self.client.get(refresh_url.format(scheme.id))
        self.assertEqual(response.status_code, 405)
        # link a document
        self.document.scheme = scheme
        self.document.save()
        # check correct redirection to delete_related
        expected_url = '/s/delete_related/{}/'.format(scheme.id)
        response = self.client.post(refresh_url.format(scheme.id), follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        # unlink document
        self.document.scheme = None
        self.document.save()
        # check correct shares refresh
        response = self.client.post(refresh_url.format(scheme.id), follow=True)
        self.assertEqual(response.status_code, 200)
        refreshed_shares = response.context['shares']
        # check number of shares generated
        self.assertEqual(scheme.n, len(refreshed_shares))
        # check generated shares different from the previous
        self.assertTrue(self.check_shares(shares, refreshed_shares))

    def test_encrypt(self):
        """ Test encrypt view """



    def check_shares(self, shares_1, shares_2):
        """ helper function: return True if shares are different """
        for i, j in zip(shares_1, shares_2):
            if i[1] == j[1]:
                return False
        return True

    @classmethod
    def tearDownClass(cls):
        cls.folder.delete()

