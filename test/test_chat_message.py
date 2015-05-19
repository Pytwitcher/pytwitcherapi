import pytest

from pytwitcherapi.chat import message


@pytest.mark.parametrize('text,expected', [('hallo!', 'hallo!'),
                                           ('ciao bella', 'ciao ...')])
def test_repr(text, expected):
    source = message.Chatter('me')
    target = '#you'
    msg = message.Message(source=source, target=target, text=text)
    assert repr(msg) == '<Message me to #you: %s>' % expected


def assert_message_attrs(message, **kwargs):
    """Assert that the given message has the expected attribute values

    :param message: the message to test
    :type message: :class:`message.Message`
    :param kwargs: keyword is the attribute to check,
                   value the expected attribute value
    """
    for attr, expected in kwargs.items():
        messagevalue = getattr(message, attr)
        assert messagevalue == expected


TAGS1 = [message.Tag('color', '#0000FF'),
         message.Tag('emotes', '36031:0-7,22-30/40894:9-18'),
         message.Tag('subscriber', '1'),
         message.Tag('turbo', '1'),
         message.Tag('user-type', 'mod')]

TAGS2 = [message.Tag('display-name', 'haha'),
         message.Tag('emotes', None)]

EMOTES1 = [message.Emote(36031, [(0, 7), (22, 30)]),
           message.Emote(40894, [(9, 18)])]

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
    m = message.Message3('', '', '', tags)
    assert_message_attrs(m, **attrs)
