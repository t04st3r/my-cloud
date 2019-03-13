import random
import functools
import base64
from django.db import models
from django.conf import settings
import django.contrib.auth.hashers as hashers
from cryptography.fernet import Fernet
from pathlib import Path


class ShamirSS(models.Model):

    MAX_N = 20

    MERSENNE_EXP_VALUES = (
        # see https://oeis.org/A000043 mersenne prime sequence
        (89, '89'),
        (107, '107'),
        (127, '127'),
    )

    K_CHOICES = (
        zip(range(2, MAX_N + 1), range(2,  MAX_N + 1))
    )

    N_CHOICES = (
        zip(range(2,  MAX_N + 1), range(2,  MAX_N + 1))
    )

    name = models.CharField(max_length=200)
    mers_exp = models.IntegerField(choices=MERSENNE_EXP_VALUES)
    k = models.IntegerField(choices=K_CHOICES)
    n = models.IntegerField(choices=N_CHOICES)
    secret = models.CharField(max_length=128)

    def __str__(self):
        return "{} ({}, {})".format(self.name, self.k, self.n)

    def get_shares(self):
        """ generate n shares and store hashed secret """
        prime = (2**self.mers_exp) - 1
        shares = self._generate_shares(self.k, self.n, prime)
        secret = str(shares[-1])
        del shares[-1]
        hashed_secret = hashers.make_password(secret)
        self.secret = hashed_secret
        return self.encode_shares(shares)

    def validate_shares(self, shares):
        """ return true if shares match with secret """
        if not isinstance(shares, list):
            raise ValueError('unrecognized data')
        try:
            shares = self.decode_shares(shares)
            secret = self.get_secret(shares)
            return hashers.check_password(str(secret), self.secret)
        except:
            return False

    def get_secret(self, shares):
        """ recover the secret given at least k shares """
        prime = (2**self.mers_exp) - 1
        if len(shares) < self.k:
            raise ValueError('Not enough shares to recover the secret')
        return self._recover_secret(shares, prime)

    def get_key(self, secret):
        """ return a base64 encoded 32 bytes string of the secret """
        str_secret = str(secret)
        while len(str_secret) != 32:
            if len(str_secret) < 32:
                # insert 0 padding
                str_secret += '0'
            elif len(str_secret) > 32:
                # truncate if too long
                str_secret = str_secret[:-1]
        byte_secret = bytes(str_secret, 'utf-8')
        return base64.b64encode(byte_secret)

    def encode_shares(self, shares):
        """ encode shares as base 64 bytes string """
        ret_list = []
        for share in shares:
            b_share = bytes(str(share[1]), 'utf-8')
            b_encoded = base64.b64encode(b_share)
            ret_list.append((share[0], b_encoded.decode('utf-8')))
        return ret_list

    def decode_shares(self, shares):
        """ decode shares as integers """
        ret_list = []
        for share in shares:
            b_share = base64.b64decode(bytes(share[1], 'utf-8'))
            ret_list.append((share[0], int(b_share.decode('utf-8'))))
        return ret_list

    def encrypt_file(self, file_path, shares):
        """ encrypt a file using secret as key, return encrypted file path or None if file doesn't exists """
        check_file = Path(file_path)
        if check_file.is_file():
            output_file = file_path + '.enc'
            secret = self.get_secret(self.decode_shares(shares))
            key = self.get_key(secret)
            with open(file_path, 'rb') as f:
                data = f.read()
            fernet = Fernet(key)
            encrypted = fernet.encrypt(data)
            with open(output_file, 'wb') as f:
                f.write(encrypted)
            # return relative path to MEDIA path
            remove_len = len(settings.MEDIA_ROOT)
            return output_file[remove_len:]
        return None

    def decrypt_file(self, file_path, shares):
        """ decrypt a file using secret as key, return decrypted file path or None if file doesn't exists """
        check_file = Path(file_path)
        if check_file.is_file():
            output_file = file_path[:-4]
            secret = self.get_secret(self.decode_shares(shares))
            key = self.get_key(secret)
            with open(file_path, 'rb') as f:
                data = f.read()
            fernet = Fernet(key)
            encrypted = fernet.decrypt(data)
            with open(output_file, 'wb') as f:
                f.write(encrypted)
            # return relative path to MEDIA path
            remove_len = len(settings.MEDIA_ROOT)
            return output_file[remove_len:]
        return None

    # https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing#Python_example

    def _eval_at(self, poly, x, prime):
        """evaluates polynomial (coefficient tuple) at x, used to generate a
        shamir pool in make_random_shares below. """
        accum = 0
        for coeff in reversed(poly):
            accum *= x
            accum += coeff
            accum %= prime
        return accum

    def _generate_shares(self, minimum, shares, prime):
        """ Generates a random shamir pool, returns the secret and the share
        points as a list where the last item is the secret."""
        _RINT = functools.partial(random.SystemRandom().randint, 0)
        if minimum > shares:
            raise ValueError("pool secret would be irrecoverable")
        poly = [_RINT(prime) for i in range(minimum)]
        points = [(i, self._eval_at(poly, i, prime))
                  for i in range(1, shares + 1)]
        points.append(poly[0])
        return points

    def _extended_gcd(self, a, b):
        """
        division in integers modulus p means finding the inverse of the
        denominator modulo p and then multiplying the numerator by this
        inverse (Note: inverse of A is B such that A*B % p == 1) this can
        be computed via extended Euclidean algorithm
        http://en.wikipedia.org/wiki/Modular_multiplicative_inverse#Computation
        """
        x = 0
        last_x = 1
        y = 1
        last_y = 0
        while b != 0:
            quot = a // b
            a, b = b, a % b
            x, last_x = last_x - quot * x, x
            y, last_y = last_y - quot * y, y
        return last_x, last_y

    def _divmod(self, num, den, p):
        """compute num / den modulo prime p

        To explain what this means, the return value will be such that
        the following is true: den * _divmod(num, den, p) % p == num
        """
        inv, _ = self._extended_gcd(den, p)
        return num * inv

    def _lagrange_interpolate(self, x, x_s, y_s, p):
        """
        Find the y-value for the given x, given n (x, y) points;
        k points will define a polynomial of up to kth order
        """
        k = len(x_s)
        assert k == len(set(x_s)), "points must be distinct"

        def PI(vals):  # upper-case PI -- product of inputs
            accum = 1
            for v in vals:
                accum *= v
            return accum

        nums = []  # avoid inexact division
        dens = []
        for i in range(k):
            others = list(x_s)
            cur = others.pop(i)
            nums.append(PI(x - o for o in others))
            dens.append(PI(cur - o for o in others))
        den = PI(dens)
        num = sum([self._divmod(nums[i] * den * y_s[i] % p, dens[i], p)
                   for i in range(k)])
        return (self._divmod(num, den, p) + p) % p

    def _recover_secret(self, shares, prime):
        """
        Recover the secret from share points
        (x,y points on the polynomial)
        """
        if len(shares) < 2:
            raise ValueError("need at least two shares")
        x_s, y_s = zip(*shares)
        return self._lagrange_interpolate(0, x_s, y_s, prime)
