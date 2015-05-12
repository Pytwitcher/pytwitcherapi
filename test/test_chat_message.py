import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('text,expected', [('hallo!', 'hallo!'),
                                           ('ciao bella', 'ciao ...')])
def test_repr(text, expected):
    me = chat.Chatter('me')
    you = chat.Chatter('you')
    message = chat.Message(source=me, target=you, text=text)
    assert repr(message) == '<Message me to you: %s>' % expected
