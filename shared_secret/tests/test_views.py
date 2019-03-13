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
    TEST_FILE_NAME = 'test_file.txt'

    @classmethod
    def setUpClass(cls):
        # create a test user
        User.objects.create_user(cls.DUMMY_USERNAME, cls.DUMMY_EMAIL, cls.DUMMY_PASSWORD)

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.DUMMY_USERNAME, password=self.DUMMY_PASSWORD, enforce_csrf_checks=True)
        self.scheme_data = {'name': 'test', 'mers_exp': 107, 'k': 4, 'n': 18}
        # create folder, document models and a test file
        self.folder = Folder.objects.create(name='test_folder')
        with open(self.TEST_FILE_NAME, 'w+') as file:
            file.write('something to fill this up\n\n')
            self.document = Document.objects.create(name='test_doc', folder=self.folder, file=File(file))
        os.remove('test_file.txt')

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
        enc_url = '/s/encrypt/{}/{}/'
        # check non existent document and scheme
        response = self.client.get(enc_url.format(random.randint(2, 100), random.randint(1, 100)))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(enc_url.format(random.randint(2, 100), random.randint(1, 100)))
        self.assertEqual(response.status_code, 404)
        scheme = ShamirSS(**self.scheme_data)
        shares = scheme.get_shares()
        scheme.save()
        # check get on existing scheme and document
        response = self.client.get(enc_url.format(self.document.id, scheme.id))
        self.assertEqual(response.status_code, 200)
        # check successful redirect after encryption
        random_shares = self._pick_k_random_values(shares, scheme.k)
        post_data = {'share_' + str(share[0]): share[1] for share in random_shares}
        post_data['scheme'] = scheme.id
        expected_url = '/folder/{}/'.format(self.document.folder.id)
        response = self.client.post(enc_url.format(self.document.id, scheme.id), post_data, follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        # check document model changes
        self.document.refresh_from_db()
        self.assertTrue(os.path.isfile(self.document.file_path()))
        self.assertIsNotNone(self.document.scheme)
        self.assertEqual(self.document.filename(), self.TEST_FILE_NAME + '.enc')
        # check document already encrypted
        response = self.client.post(enc_url.format(self.document.id, scheme.id), post_data, follow=True)
        self.assertFormError(response, 'form', None, 'Document already encrypted')
        
    def test_decrypt(self):
        dec_url = '/s/decrypt/{}/'
        # check non existent document
        response = self.client.get(dec_url.format(random.randint(2, 100)))
        self.assertEqual(response.status_code, 404)
        response = self.client.post(dec_url.format(random.randint(2, 100)))
        self.assertEqual(response.status_code, 404)
        # check get on plaintext document
        response = self.client.get(dec_url.format(self.document.id))
        self.assertEqual(response.status_code, 404)
        # check post on plaintext document
        response = self.client.post(dec_url.format(self.document.id))
        self.assertEqual(response.status_code, 404)
        # encrypt file
        scheme = ShamirSS(**self.scheme_data)
        shares = scheme.get_shares()
        scheme.save()
        enc_file_path = scheme.encrypt_file(self.document.file_path(), shares)
        os.remove(self.document.file_path())
        self.document.file.name = enc_file_path
        self.document.scheme = scheme
        self.document.save()
        # check successful get
        response = self.client.get(dec_url.format(self.document.id))
        self.assertEqual(response.status_code, 200)
        # check successful redirect after decryption
        random_shares = self._pick_k_random_values(shares, scheme.k)
        post_data = {'share_' + str(share[0]): share[1] for share in random_shares}
        post_data['scheme'] = scheme.id
        expected_url = '/folder/{}/'.format(self.document.folder.id)
        response = self.client.post(dec_url.format(self.document.id), post_data, follow=True)
        self.assertRedirects(response, expected_url=expected_url, status_code=302, target_status_code=200)
        self.document.refresh_from_db()
        self.assertTrue(os.path.isfile(self.document.file_path()))
        self.assertIsNone(self.document.scheme)
        self.assertEqual(self.document.filename(), self.TEST_FILE_NAME)

    def check_shares(self, shares_1, shares_2):
        """ helper function: return True if shares are different """
        for i, j in zip(shares_1, shares_2):
            if i[1] == j[1]:
                return False
        return True

    def _pick_k_random_values(self, l, k):
        """ select k distinct random values from l """
        s = set()
        while len(s) != k:
            s.add(random.choice(l))
        return list(s)

    @classmethod
    def tearDownClass(cls):
        pass

    def tearDown(self):
        os.remove(self.document.file_path())
