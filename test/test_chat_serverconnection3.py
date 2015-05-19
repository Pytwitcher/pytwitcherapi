import irc.client
import mock
import pytest

from pytwitcherapi.chat import connection, message


@pytest.fixture(scope='function')
def con(monkeypatch):
    monkeypatch.setattr(irc.client.ServerConnection, '_process_line', mock.Mock())
    con = connection.ServerConnection3(None)
    con.real_server_name = ''
    con._handle_event = mock.Mock()
    return con


TESTTAGS1 = [message.Tag(name='aaa', value='bbb', vendor=None),
             message.Tag(name='ccc', value=None, vendor=None),
             message.Tag(name='ddd', value='eee', vendor='example.com')]


@pytest.mark.parametrize('tags,expected', [(None, []),
                                           ('aaa=bbb;ccc;example.com/ddd=eee', TESTTAGS1)])
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


msg1 = ':nick!ident@host.com PRIVMSG me :Hello'
msg2 = 'USER storax_dev 0 * :storax_dev'
msg3 = '@color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod \
:joe_user!joe_user@joe_user.tmi.twitch.tv PRIVMSG #somerandomchannel:lirikMLG is awesome!'
rfc_regex_params = [
    (msg1, None, 'nick!ident@host.com', 'PRIVMSG', ' me :Hello'),
    (msg2, None, None, 'USER', ' storax_dev 0 * :storax_dev'),
    (msg3, 'color=#0000FF;emotes=16156:0-7;subscriber=1;turbo=0;user_type=mod',
     'joe_user!joe_user@joe_user.tmi.twitch.tv', 'PRIVMSG',
     ' #somerandomchannel:lirikMLG is awesome!')]


@pytest.mark.parametrize('message,tags,prefix,command,argument', rfc_regex_params)
def test_rfc_regex_prefix(message, tags, prefix, command, argument):
    m = connection.ServerConnection3._rfc_1459_command_regexp.match(message)
    assert m.group('prefix') == prefix, 'Parsing prefix incorrect.'


@pytest.mark.parametrize('message,tags,prefix,command,argument', rfc_regex_params)
def test_rfc_regex_command(message, tags, prefix, command, argument):
    m = connection.ServerConnection3._rfc_1459_command_regexp.match(message)
    assert m.group('command') == command, 'Parsing command incorrect.'


@pytest.mark.parametrize('message,tags,prefix,command,argument', rfc_regex_params)
def test_rfc_regex_argument(message, tags, prefix, command, argument):
    m = connection.ServerConnection3._rfc_1459_command_regexp.match(message)
    assert m.group('argument') == argument, 'Parsing argument incorrect.'


@pytest.mark.parametrize('message,tags,prefix,command,argument', rfc_regex_params)
def test_rfc_regex_tags(message, tags, prefix, command, argument):
    m = connection.ServerConnection3._rfc_1459_command_regexp.match(message)
    assert m.group('tags') == tags, 'Parsing tags incorrect.'


def test_process_line_other_cmd(con):
    l = '@aaa;bbb :#somechannel PART nick1!nick1@somehost'
    con._process_line(l)
    try:
        irc.client.ServerConnection._process_line.assert_called_with(l)
        assert not con._handle_event.called
    except AssertionError:
        raise AssertionError('If the command is not \
privmsg or notice, the old method should be used!')


def _process_line(connection, line):
    """Returns all events that were created in calling _handle_event during processing"""
    connection._process_line(line)
    calls = connection._handle_event.call_args_list
    events = [c[0][0] for c in calls]
    return events


actionline = '@aaa;bbb :%s %s %s :\001ACTION hahaha\001'
msgline = '@aaa;bbb :%s %s %s :Hallo'
ctcpline = '@aaa;bbb :%s %s %s :\001Hallo\001'
tags = [message.Tag('aaa'), message.Tag('bbb')]
notagline = ':%s %s %s :Hallo'


@pytest.fixture(scope='function', params=[
    (msgline, 'PRIVMSG', '#somechannel', 'pubmsg', tags),
    (msgline, 'PRIVMSG', 'nick2!nick2@somehost', 'privmsg', tags),
    (msgline, 'NOTICE', '#somechannel', 'pubnotice', tags),
    (msgline, 'NOTICE', 'nick2!nick2@somehost', 'privnotice', tags),
    (ctcpline, 'NOTICE', 'nick2!nick2@somehost', 'ctcpreply', tags),
    (ctcpline, 'PRIVMSG', 'nick2!nick2@somehost', 'ctcp', tags),
    (notagline, 'PRIVMSG', '#somechannel', 'pubmsg', []),
    (notagline, 'PRIVMSG', 'nick2!nick2@somehost', 'privmsg', []),
    (notagline, 'NOTICE', '#somechannel', 'pubnotice', []),
    (notagline, 'NOTICE', 'nick2!nick2@somehost', 'privnotice', [])])
def msgargs(request):
    line, cmd, target, event, tags = request.param
    source = 'nick1!nick!@somehost'
    line = line % (source, cmd, target)
    expectedevents = [
        connection.Event3('all_raw_messages', source, None, [line], tags),
        connection.Event3(event, source, target, ['Hallo'], tags)]
    return line, cmd, source, target, expectedevents


def test_process_line(con, msgargs):
    line, cmd, source, target, expectedevents = msgargs
    events = _process_line(con, line)
    assert events == expectedevents, 'Did not call _handle_event with the right events or order'


@pytest.fixture(scope='function', params=[(actionline, 'PRIVMSG', 'nick2!nick2@somehost', 'ctcp', tags)])
def actionmsgargs(request):
    line, cmd, target, event, tags = request.param
    source = 'nick1!nick!@somehost'
    line = line % (source, cmd, target)
    expectedevents = [
        connection.Event3('all_raw_messages', source, None, [line], tags),
        connection.Event3(event, source, target, ['ACTION', 'hahaha'], tags),
        connection.Event3('action', source, target, ['hahaha'], tags)]
    return line, cmd, source, target, expectedevents


def test_process_line_actionmsg(con, actionmsgargs):
    line, cmd, source, target, expectedevents = actionmsgargs
    events = _process_line(con, line)
    assert events == expectedevents, 'Did not call _handle_event with the right events or order'


@pytest.fixture(scope='function')
def mock_time_module(monkeypatch):
    m = mock.Mock()
    monkeypatch.setattr(connection, 'time', m)


@pytest.fixture(scope='function')
def mock_time(monkeypatch):
    m = mock.Mock()
    m.side_effect = range(50)
    monkeypatch.setattr(connection.time, 'time', m)
    return m


def test_wait_for_limit(mock_time):
    con = connection.ServerConnection3(None)
    for i in range(20):
        waittime = con.get_waittime()
        assert waittime == 0, 'The first 20 messages should not have to wait'
    for i in range(20):
        waittime = con.get_waittime()
        # assert we waited 11 seconds
        # because we send 20 messages in 1 second intervals
        # and the limit is 20 messages in 30 seconds
        # one second is buffer
        assert waittime == 11
