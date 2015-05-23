import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('tagstr,tag', [('aaa', chat.Tag('aaa')),
                                        ('bbb=ccc', chat.Tag('bbb', 'ccc')),
                                        ('example.com/ddd=eee', chat.Tag('ddd', 'eee', 'example.com'))])
def test_from_str(tagstr, tag):
    parsedtag = chat.Tag.from_str(tagstr)
    assert parsedtag.name == tag.name
    assert parsedtag.value == tag.value
    assert parsedtag.vendor == tag.vendor


def test_eq():
    t1 = chat.Tag('aaa', 'bbb', 'example.com')
    t2 = chat.Tag('aaa', 'bbb', 'example.com')
    assert t1 == t2

    t3 = chat.Tag('aaa', 'bbb', None)
    assert not (t1 == t3)
