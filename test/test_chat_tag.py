import pytest

from pytwitcherapi.chat import message


@pytest.mark.parametrize('tagstr,tag', [('aaa', message.Tag('aaa')),
                                        ('bbb=ccc', message.Tag('bbb', 'ccc')),
                                        ('example.com/ddd=eee', message.Tag('ddd', 'eee', 'example.com'))])
def test_from_str(tagstr, tag):
    parsedtag = message.Tag.from_str(tagstr)
    assert parsedtag.name == tag.name
    assert parsedtag.value == tag.value
    assert parsedtag.vendor == tag.vendor


def test_eq():
    t1 = message.Tag('aaa', 'bbb', 'example.com')
    t2 = message.Tag('aaa', 'bbb', 'example.com')
    assert t1 == t2

    t3 = message.Tag('aaa', 'bbb', None)
    assert not (t1 == t3)
