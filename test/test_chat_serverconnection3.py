import sys

import irc.client
import mock
import pytest

from pytwitcherapi import chat


def reraise(exc_info, preppendmsg):
    if sys.version_info[0] == 2:
        # preserve stacktrace
        exc_info[1].args = (('%s\n' % preppendmsg) + exc_info[1].args[0],)
        exec('raise exc_info[0], exc_info[1], exc_info[2]')
    else:
        raise exc_info[0](('%s\n' % preppendmsg) + exc_info[1].args[0]).with_traceback(exc_info[2])


@pytest.fixture(scope='function')
def con(monkeypatch):
    monkeypatch.setattr(irc.client.ServerConnection, '_process_line', mock.Mock())
    con = chat.ServerConnection3(None)
    con.real_server_name = ''
    con._handle_event = mock.Mock()
    return con


@pytest.mark.parametrize('tags,expected', [(None, []),
                                           ('aaa=bbb;ccc;example.com/ddd=eee',
                                            [chat.Tag(name='aaa', value='bbb', vendor=None),
                                             chat.Tag(name='ccc', value=None, vendor=None),
                                             chat.Tag(name='ddd', value='eee', vendor='example.com')])])
def test_process_tags(tags, expected, con):
    tags = con._process_tags(tags)
    assert tags == expected


@pytest.mark.parametrize('prefixstr, expected', [(None, None),
                                                 ('test', irc.client.NickMask('test'))])
def test_process_prefix(prefixstr, expected, con):
    prefix = con._process_prefix(prefixstr)
    assert prefix == expected


def test_process_command(con):
    cmdstr = 'PRIVMSG'
    cmd = con._process_command(cmdstr)
    assert cmd == 'privmsg'
    cmd2 = con._process_command(None)
    assert cmd2 is None


@pytest.mark.parametrize('argstr,expected', [(None, None),
                                             ('jojo :hey was geht', ['jojo', 'hey was geht']),
                                             ('coool', ['coool'])])
def test_process_arguments(argstr, expected, con):
    args = con._process_arguments(argstr)
    assert args == expected


@pytest.mark.parametrize('message,tags,prefix,command,argument', [
    (':nick!ident@host.com PRIVMSG me :Hello', None, 'nick!ident@host.com', 'PRIVMSG', ' me :Hello'),
    ('USER storax_dev 0 * :storax_dev', None, None, 'USER', ' storax_dev 0 * :storax_dev'),
    ('@color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod \
:joe_user!joe_user@joe_user.tmi.twitch.tv PRIVMSG #somerandomchannel:lirikMLG is awesome!',
     'color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod',
     'joe_user!joe_user@joe_user.tmi.twitch.tv', 'PRIVMSG', ' #somerandomchannel:lirikMLG is awesome!')])
def test_rfc_regex(message, tags, prefix, command, argument):
    m = chat.ServerConnection3._rfc_1459_command_regexp.match(message)
    assert m.group('prefix') == prefix
    assert m.group('command') == command
    assert m.group('argument') == argument
    assert m.group('tags') == tags


def test_process_line_other_cmd(con):
    l = '@aaa;bbb :#somechannel PART nick1!nick1@somehost'
    con._process_line(l)
    try:
        irc.client.ServerConnection._process_line.assert_called_with(l)
        assert not con._handle_event.called
    except AssertionError:
        raise AssertionError('If the command is not \
privmsg or notice, the old method should be used!')


@pytest.mark.parametrize('cmd,target,event', [('PRIVMSG', '#somechannel', 'pubmsg'),
                                              ('PRIVMSG', 'nick2!nick2@somehost', 'privmsg'),
                                              ('NOTICE', '#somechannel', 'pubnotice'),
                                              ('NOTICE', 'nick2!nick2@somehost', 'privnotice')])
def test_process_line_notctcp(cmd, target, event, con):
    l = '@aaa;bbb :nick1!nick1@somehost %s %s :Hallo' % (cmd, target)
    con._process_line(l)
    try:
        calls = con._handle_event.call_args_list
        c1event = calls[0][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == 'all_raw_messages'
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target is None
        assert c1event.arguments == [l]
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the all_raw_messages event incorrectly.')

    try:
        calls = con._handle_event.call_args_list
        c1event = calls[1][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == event
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target == target
        assert c1event.arguments == ['Hallo']
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the privmsg event incorrectly.')


@pytest.mark.parametrize('cmd,target,event', [('NOTICE', 'nick2!nick2@somehost', 'ctcpreply'),
                                              ('PRIVMSG', 'nick2!nick2@somehost', 'ctcp')])
def test_process_line_ctcp(cmd, target, event, con):
    l = '@aaa;bbb :nick1!nick1@somehost %s %s :\001Hallo\001' % (cmd, target)
    con._process_line(l)
    try:
        calls = con._handle_event.call_args_list
        c1event = calls[0][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == 'all_raw_messages'
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target is None
        assert c1event.arguments == [l]
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the all_raw_messages event incorrectly.')

    try:
        calls = con._handle_event.call_args_list
        c1event = calls[1][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == event
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target == target
        assert c1event.arguments == ['Hallo']
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the ctcp event incorrectly.')


@pytest.mark.parametrize('cmd,target,event', [('PRIVMSG', 'nick2!nick2@somehost', 'ctcp')])
def test_process_line_ctcpaction(cmd, target, event, con):
    l = '@aaa;bbb :nick1!nick1@somehost %s %s :\001ACTION hahaha\001' % (cmd, target)
    con._process_line(l)
    try:
        calls = con._handle_event.call_args_list
        c1event = calls[0][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == 'all_raw_messages'
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target is None
        assert c1event.arguments == [l]
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the all_raw_messages event incorrectly.')

    try:
        calls = con._handle_event.call_args_list
        c1event = calls[1][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == event
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target == target
        assert c1event.arguments == ['ACTION', 'hahaha']
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the ctcp event incorrectly.')

    try:
        calls = con._handle_event.call_args_list
        c1event = calls[2][0][0]
        assert c1event.tags == [chat.Tag('aaa'), chat.Tag('bbb')]
        assert c1event.type == 'action'
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target == target
        assert c1event.arguments == ['hahaha']
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the action event incorrectly.')


@pytest.mark.parametrize('cmd,target,event', [('PRIVMSG', '#somechannel', 'pubmsg'),
                                              ('PRIVMSG', 'nick2!nick2@somehost', 'privmsg'),
                                              ('NOTICE', '#somechannel', 'pubnotice'),
                                              ('NOTICE', 'nick2!nick2@somehost', 'privnotice')])
def test_process_line_notags(cmd, target, event, con):
    l = ':nick1!nick1@somehost %s %s :Hallo' % (cmd, target)
    con._process_line(l)
    try:
        calls = con._handle_event.call_args_list
        c1event = calls[0][0][0]
        assert c1event.tags == []
        assert c1event.type == 'all_raw_messages'
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target is None
        assert c1event.arguments == [l]
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the all_raw_messages event incorrectly.')

    try:
        calls = con._handle_event.call_args_list
        c1event = calls[1][0][0]
        assert c1event.tags == []
        assert c1event.type == event
        assert c1event.source == 'nick1!nick1@somehost'
        assert c1event.target == target
        assert c1event.arguments == ['Hallo']
    except AssertionError:
        ei = sys.exc_info()
        reraise(ei, 'Sent the privmsg event incorrectly.')
