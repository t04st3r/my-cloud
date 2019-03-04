from django.db import models


class ShamirSS(models.Model):

    MAX_N = 20

    MERSENNE_EXP_VALUES = (
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
