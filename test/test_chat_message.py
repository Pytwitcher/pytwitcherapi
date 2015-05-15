import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('text,expected', [('hallo!', 'hallo!'),
                                           ('ciao bella', 'ciao ...')])
def test_repr(text, expected):
    source = chat.Chatter('me')
    target = '#you'
    message = chat.Message(source=source, target=target, text=text)
    assert repr(message) == '<Message me to #you: %s>' % expected


def assert_message_attrs(message, **kwargs):
    """Assert that the given message has the expected attribute values

    :param message: the message to test
    :type message: :class:`chat.Message`
    :param kwargs: keyword is the attribute to check,
                   value the expected attribute value
    """
    for attr, expected in kwargs.items():
        messagevalue = getattr(message, attr)
        assert messagevalue == expected


TAGS1 = [chat.Tag('color', '#0000FF'),
         chat.Tag('emotes', '36031:0-7,22-30/40894:9-18'),
         chat.Tag('subscriber', '1'),
         chat.Tag('turbo', '1'),
         chat.Tag('user-type', 'mod')]

TAGS2 = [chat.Tag('display-name', 'haha'),
         chat.Tag('emotes', None)]

EMOTES1 = [chat.Emote(36031, [(0, 7), (22, 30)]),
           chat.Emote(40894, [(9, 18)])]

ATTRS1 = {'color': '#0000FF',
          'emotes': EMOTES1,
          'subscriber': True,
          'turbo': True,
          'user_type': 'mod'}

ATTRS2 = {'color': None,
          'emotes': [],
          'subscriber': False,
          'turbo': False,
          'user_type': None}


@pytest.mark.parametrize('tags,attrs', [(TAGS1, ATTRS1),
                                        (TAGS2, ATTRS2)])
def test_set_tags(tags, attrs):
    m = chat.Message3('', '', '', tags)
    assert_message_attrs(m, **attrs)
