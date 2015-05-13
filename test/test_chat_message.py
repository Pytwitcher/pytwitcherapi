import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('text,expected', [('hallo!', 'hallo!'),
                                           ('ciao bella', 'ciao ...')])
def test_repr(text, expected):
    source = chat.Chatter('me')
    target = '#you'
    message = chat.Message(source=source, target=target, text=text)
    assert repr(message) == '<Message me to #you: %s>' % expected


def test_set_tags():
    tags = [chat.Tag('color', '#0000FF'),
            chat.Tag('emotes', 'emotes=36031:0-7,22-30/40894:9-18'),
            chat.Tag('subscriber', '1'),
            chat.Tag('turbo', '1'),
            chat.Tag('user-type', 'mod')]
    m = chat.Message3('', '', '', tags)
    assert m.color == '#0000FF'
    assert m.emotes == ['emotes=36031:0-7,22-30/40894:9-18']
    assert m.subscriber is True
    assert m.turbo is True
    assert m.user_type == 'mod'

    tags = [chat.Tag('display-name', 'haha')]
    m = chat.Message3('', '', '', tags)
    assert m.color is None
    assert m.emotes == []
    assert m.subscriber is False
    assert m.turbo is False
    assert m.user_type is None
