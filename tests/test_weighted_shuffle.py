# coding: utf-8
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
])
def test_weighted_shuffle(choices):
    total = sum([w for __, w in choices])
    expect = {k: w/float(total) for k, w in choices}

    N = 10**6
    result = {k: 0 for k, __ in choices}
    for i in range(N):
        key = list(weighted_shuffle(choices))[0]
        result[key] += 1
    result = {k: v/float(N) for k, v in result.items()}

    for k in expect:
        assert result[k] == approx(expect[k], rel=1e-2)


def test_weighted_shuffle_empty():
    assert weighted_shuffle([]) == []


def test_weighted_shuffle_balance():
    """权重相同时，任何元素在任何位置的概率都应当是一样的"""
    choices = [
        ('A', 1),
        ('B', 1),
        ('C', 1),
        ('D', 1),
        ('E', 1),
    ]
    N = 10**6
    result = {k: [0]*len(choices) for k, __ in choices}
    for i in range(N):
        items = weighted_shuffle(choices)
        for i, k in enumerate(items):
            result[k][i] += 1
    for k in result:
        for n in result[k]:
            assert n/float(N) == approx(1.0/len(choices), rel=1e-2)
