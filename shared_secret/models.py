from django.db import models
import random
import functools


class ShamirSS(models.Model):

    MAX_N = 20

    MERSENNE_EXP_VALUES = (
        # see https://oeis.org/A000043 mersenne prime sequence
        (89, '89'),
        (107, '107'),
        (127, '127'),
        (521, '521'),
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

    def get_shares(self, include_secret=False):
        """ return the n shares and the secret if enabled """
        prime = (2**self.mers_exp) - 1
        shares = self._generate_shares(self.k, self.n, prime)
        return shares if include_secret else shares[:-1]

    def get_secret(self, shares):
        """ recover the secret given at least k shares """
        prime = (2**self.mers_exp) - 1
        if len(shares) < self.k:
            raise ValueError('Not enough shares to recover the secret')
        return self._recover_secret(shares, prime)

    # code from https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing#Python_example

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
