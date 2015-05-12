import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('text,expected', [('hallo!', 'hallo!'),
                                           ('ciao bella', 'ciao ...')])
def test_repr(text, expected):
    source = chat.Chatter('me')
    target = '#you'
    message = chat.Message(source=source, target=target, text=text)
    assert repr(message) == '<Message me to #you: %s>' % expected
