from django.test import TestCase
from shared_secret.models import ShamirSS
from shared_secret.forms import SSForm
import django.contrib.auth.hashers as hashers
from string import digits
import random


class ShamirSSTestCase(TestCase):
    """ Test for shared secret Model """

    def setUp(self):
        self.form_data = {'name': 'test', 'mers_exp':  107, 'k': 4, 'n': 18}
        self.scheme = ShamirSS(**self.form_data)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_scheme_fileds(self):
        """ Test for correct fields validation with SSForm """
        valid_form = SSForm(data=self.form_data)
        self.assertTrue(valid_form.is_valid())
        """ Test illegal value for mers_exp """
        self.form_data['mers_exp'] = 3
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        """ Test illegal value for k """
        self.form_data['mers_exp'] = 107
        self.form_data['k'] = self.scheme.MAX_N + 1
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        """ Test illegal value for n """
        self.form_data['k'] = 4
        self.form_data['n'] = self.scheme.MAX_N + 1
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        """ Test illegal value for n < k """
        self.form_data['n'] = 3
        invalid_form = SSForm(data=self.form_data)
        self.assertFalse(invalid_form.is_valid())
        self.form_data['n'] = 18

    def test_scheme_correctness(self):
        """ Test for successful shares generation and secret recovery """
        # check all shares generated correctly
        shares = self.scheme.get_shares()
        encoded_secret = self.scheme.secret
        self.assertTrue(len(shares) == self.scheme.n)
        # check hashed secret is correct picking k random shares
        rnd_shares = self._pick_k_random_values(shares, self.scheme.k)
        rec_secret = self.scheme.get_secret(rnd_shares)
        self.assertTrue(hashers.check_password(str(rec_secret), encoded_secret))
        # check hashed secret is correct picking n random shares
        secret_all = self.scheme.get_secret(shares)
        self.assertTrue(hashers.check_password(str(secret_all), encoded_secret))
        # check value error if lower tha k shares provided
        rnd_shares_2 = self._pick_k_random_values(shares, self.scheme.k - 1)
        self.assertRaises(ValueError, lambda: self.scheme.get_secret(rnd_shares_2))
        # check for wrong shares
        rnd_shares_3 = self._pick_k_random_values(shares, self.scheme.k)
        rnd_shares_3[0] = (rnd_shares_3[0][0], int(
            ''.join(random.choice(digits) for i in range(len(str(rnd_shares_3[0][1])))))
        )
        wrong_secret = self.scheme.get_secret(rnd_shares_3)
        self.assertFalse(hashers.check_password(str(wrong_secret), encoded_secret))

    def _pick_k_random_values(self, l, k):
        """ select k distinct random values from l """
        s = set()
        while len(s) != k:
            s.add(random.choice(l))
        return list(s)
