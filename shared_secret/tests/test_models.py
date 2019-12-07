from django.test import TestCase
from shared_secret.models import ShamirSS
from shared_secret.forms import SSForm
import django.contrib.auth.hashers as hashers
from django.conf import settings
import os
import hashlib
import random


class ShamirSSTestCase(TestCase):
    """ Test for shared secret Model """

    def setUp(self):
        self.form_data = {'name': 'test', 'mers_exp':  107, 'k': 4, 'n': 18}
        self.scheme = ShamirSS(**self.form_data)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_difference(self):
        """ Test difference method works """
        self.assertTrue(self.scheme.difference() == 14)

    def test_scheme_fileds(self):
        """ Test for correct fields validation with SSForm """
        valid_form = SSForm(data=self.form_data)
        self.assertTrue(valid_form.is_valid())
        # Test illegal value for mers_exp
        self.form_data['mers_exp'] = 3
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        # Test illegal value for k
        self.form_data['mers_exp'] = 107
        self.form_data['k'] = self.scheme.MAX_N + 1
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        # Test illegal value for n
        self.form_data['k'] = 4
        self.form_data['n'] = self.scheme.MAX_N + 1
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        # Test illegal value for n < k
        self.form_data['n'] = 3
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        self.form_data['n'] = 18

    def test_scheme_correctness(self):
        """ Test for successful shares generation and secret recovery """
        # check correct base64 encoding-decoding
        random_int = random.randint(10000000000, 100000000000)
        enc_dec = self.scheme.decode_shares(
            self.scheme.encode_shares([(0, random_int)]))
        self.assertTrue(random_int == enc_dec[0][1])
        # check all shares generated correctly
        shares = self.scheme.get_shares()
        encoded_secret = self.scheme.secret
        self.assertTrue(len(shares) == self.scheme.n)
        # check hashed secret is correct picking k random shares
        rnd_shares = self._pick_k_random_values(shares, self.scheme.k)
        rec_secret = self.scheme.get_secret(
            self.scheme.decode_shares(rnd_shares))
        self.assertTrue(hashers.check_password(
            str(rec_secret), encoded_secret))
        # check hashed secret is correct picking n random shares
        secret_all = self.scheme.get_secret(self.scheme.decode_shares(shares))
        self.assertTrue(hashers.check_password(
            str(secret_all), encoded_secret))
        # check value error if lower than k shares provided
        rnd_shares_2 = self._pick_k_random_values(shares, self.scheme.k - 1)
        self.assertRaises(ValueError, lambda: self.scheme.get_secret(
            self.scheme.decode_shares(rnd_shares_2)))
        # check for wrong shares
        rnd_shares_3 = self._pick_k_random_values(shares, self.scheme.k)
        rnd_shares_3[0] = (rnd_shares_3[0][0], rnd_shares_3[1][1])
        wrong_secret = self.scheme.get_secret(
            self.scheme.decode_shares(rnd_shares_3))
        self.assertFalse(hashers.check_password(
            str(wrong_secret), encoded_secret))

    def test_file_encryption_decryption(self):
        """ Test successful file encryption and decryption """
        # create two test files with same content
        file_name_1 = settings.MEDIA_ROOT + 'test_file_1.txt'
        file_name_2 = settings.MEDIA_ROOT + 'test_file_2.txt'
        content = 'some string just to fill this file up\n\n'
        test_file_1 = open(file_name_1, 'w+')
        test_file_1.write(content)
        test_file_1.close()
        test_file_2 = open(file_name_2, 'w+')
        test_file_2.write(content)
        test_file_2.close()
        # create shares for the scheme
        shares = self.scheme.get_shares()
        # encrypt/decrypt test file 1
        enc_dec_test_file_1 = self.scheme.decrypt_file(
            settings.MEDIA_ROOT + self.scheme.encrypt_file(file_name_1, shares), shares)
        # encrypt/decrypt test file 2
        enc_dec_test_file_2 = self.scheme.decrypt_file(
            settings.MEDIA_ROOT + self.scheme.encrypt_file(file_name_2, shares), shares)
        # create hashes of the two files
        hash_1 = self.hash_file(settings.MEDIA_ROOT + enc_dec_test_file_1)
        hash_2 = self.hash_file(settings.MEDIA_ROOT + enc_dec_test_file_2)
        # compare hashes
        self.assertTrue(hash_1 == hash_2)
        # remove encrypted files
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_1 + '.enc')
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_2 + '.enc')
        # test encryption with files having different content
        with open(file_name_2, 'a') as file:
            file.write('this make file 2 different\n')
        # encrypt/decrypt test file 1
        enc_dec_test_file_1 = self.scheme.decrypt_file(
            settings.MEDIA_ROOT + self.scheme.encrypt_file(file_name_1, shares), shares)
        # encrypt/decrypt test file 2
        enc_dec_test_file_2 = self.scheme.decrypt_file(
            settings.MEDIA_ROOT + self.scheme.encrypt_file(file_name_2, shares), shares)
        # create hashes of the two files
        hash_1 = self.hash_file(settings.MEDIA_ROOT + enc_dec_test_file_1)
        hash_2 = self.hash_file(settings.MEDIA_ROOT + enc_dec_test_file_2)
        # compare hashes
        self.assertTrue(hash_1 != hash_2)
        # remove test files
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_1 + '.enc')
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_2 + '.enc')
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_1)
        os.remove(settings.MEDIA_ROOT + enc_dec_test_file_2)

    def hash_file(self, file):
        """ return sha1 hash of a file """
        blocksize = 65536
        hasher = hashlib.sha1()
        with open(file, 'rb') as afile:
            buf = afile.read(blocksize)
            while len(buf) > 0:
                hasher.update(buf)
                buf = afile.read(blocksize)
        return hasher.hexdigest()

    def _pick_k_random_values(self, l, k):
        """ select k distinct random values from l """
        s = set()
        while len(s) != k:
            s.add(random.choice(l))
        return list(s)
