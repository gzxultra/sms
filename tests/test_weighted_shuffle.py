# coding: utf-8
import random

from pytest import approx, mark
from smsserver.utils.weighted_shuffle import weighted_shuffle


@mark.parametrize('choices', [
    [('A', 1)],
    [
        ('A', 1),
        ('B', 2),
    ],
    [
        ('C', 3),
        ('B', 2),
        ('A', 1),
    ],
    [('key{}'.format(x), random.randint(0, 10)) for x in range(10)]
])
def test_weighted_shuffle(choices):
    total = sum([w for __, w in choices])
    expect = {k: w/float(total) for k, w in choices}

    N = 100000
    result = {k: 0 for k, __ in choices}
    for i in range(N):
        key = list(weighted_shuffle(choices))[0]
        result[key] += 1
    result = {k: v/float(N) for k, v in result.items()}

    for k in expect:
        assert result[k] == approx(expect[k], rel=1e-1)


def test_weighted_shuffle_empty():
    assert weighted_shuffle([]) == []
