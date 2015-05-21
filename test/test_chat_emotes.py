import pytest

from pytwitcherapi import chat


def test_eq():
    e1 = chat.Emote(123, [(1, 2), (3, 4)])
    e2 = chat.Emote(123, [(1, 2), (3, 4)])
    e3 = chat.Emote(123, [(1, 2)])
    assert e1 == e2
    assert not (e1 == e3)


@pytest.mark.parametrize('estr,expected', [('123:0-2', chat.Emote(123, [(0, 2)])),
                                           ('5:0-4,12-16', chat.Emote(5, [(0, 4), (12, 16)]))])
def test_from_str(estr, expected):
    e = chat.Emote.from_str(estr)
    assert e == expected
