from django.test import TestCase
from shared_secret.models import ShamirSS
from shared_secret.forms import SSForm
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
        secret, shares = self.scheme.get_shares()
        self.assertTrue(len(shares) == self.scheme.n)
        rnd_shares = self._pick_k_random_values(shares, self.scheme.k)
        rec_secret = self.scheme.get_secret(rnd_shares)
        self.assertTrue(secret, rec_secret)
        rnd_shares_2 = self._pick_k_random_values(shares, self.scheme.k - 1)
        self.assertRaises(ValueError, lambda: self.scheme.get_secret(rnd_shares_2))

    def _pick_k_random_values(self, l, k):
        """ select k distinct random values from l"""
        s = set()
        while len(s) < k:
            s = s.union(set(random.choices(population=l, k=k)))
        return list(s)
