import pytest

from pytwitcherapi.chat import message


def test_eq():
    e1 = message.Emote(123, [(1, 2), (3, 4)])
    e2 = message.Emote(123, [(1, 2), (3, 4)])
    e3 = message.Emote(123, [(1, 2)])
    assert e1 == e2
    assert not (e1 == e3)


@pytest.mark.parametrize('estr,expected', [('123:0-2', message.Emote(123, [(0, 2)])),
                                           ('5:0-4,12-16', message.Emote(5, [(0, 4), (12, 16)]))])
def test_from_str(estr, expected):
    e = message.Emote.from_str(estr)
    assert e == expected
