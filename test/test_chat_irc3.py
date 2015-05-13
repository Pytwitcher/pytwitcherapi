import pytest

from pytwitcherapi import chat


@pytest.mark.parametrize('message,tags,prefix,command,argument', [
    (':nick!ident@host.com PRIVMSG me :Hello', None, 'nick!ident@host.com', 'PRIVMSG', ' me :Hello'),
    ('USER storax_dev 0 * :storax_dev', None, None, 'USER', ' storax_dev 0 * :storax_dev'),
    ('@color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod \
:joe_user!joe_user@joe_user.tmi.twitch.tv PRIVMSG #somerandomchannel:lirikMLG is awesome!',
     'color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod',
     'joe_user!joe_user@joe_user.tmi.twitch.tv', 'PRIVMSG', ' #somerandomchannel:lirikMLG is awesome!')])
def test_rfc_regex(message, tags, prefix, command, argument):
    m = chat._rfc_1459_command_regexp.match(message)
    assert m.group('prefix') == prefix
    assert m.group('command') == command
    assert m.group('argument') == argument
    assert m.group('tags') == tags
