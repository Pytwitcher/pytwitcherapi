import sys
import threading

import irc.server
import mock
import pytest

from pytwitcherapi import chat, exceptions
from pytwitcherapi.chat import message, connection

if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue


class IRCChatClient(chat.IRCClient):
    """Little client that displays, when he joined a channel,
    so we can wait until sending messages"""
    def __init__(self, session, channel, queuesize=0, signalat=0):
        super(IRCChatClient, self).__init__(session, channel, queuesize)
        self.joined = threading.Event()
        self.joined_nicks = set()
        self.signalat = signalat
        self.messagecount = 0  # total received messaged
        self.received = threading.Event()

    def on_join(self, connection, event):
        self.joined_nicks.add(event.source.nick)
        if self.in_connection.nickname in self.joined_nicks and\
           self.out_connection.nickname in self.joined_nicks:
            self.joined.set()

    def _connect(self, connection, ip, port, nickname, password):
        # we have to fake her
        # the test server cannot handle 2 connections from the same
        # client
        # so we use 2 different nicknames for in and out connections
        if connection is self.in_connection:
            nickname = nickname + 'in'
        else:
            nickname = nickname + 'out'
        super(IRCChatClient, self)._connect(connection, ip, port,
                                            nickname, password)

    def store_message(self, *args, **kwargs):
        super(IRCChatClient, self).store_message(*args, **kwargs)
        self.messagecount += 1
        if self.messagecount == self.signalat:
            self.received.set()


class IRCServerClient(irc.server.IRCClient):
    """A simple handler for the server. Tracks a view
    events, so they can be checked later.

    Remember to reset him after each use, by setting the class
    variables to their default.
    """
    password = queue.Queue()
    joined = queue.Queue()
    quited = queue.Queue()
    messages = queue.Queue()

    def handle_quit(self, params):
        IRCServerClient.quited.put((self.client_ident(), params))
        return irc.server.IRCClient.handle_quit(self, params)

    def handle_join(self, params):
        IRCServerClient.joined.put((self.client_ident(), params))
        return irc.server.IRCClient.handle_join(self, params)

    def handle_pass(self, params):
        IRCServerClient.password.put((self.client_ident(), params))

    def handle_privmsg(self, params):
        IRCServerClient.messages.put((self.client_ident(), params))
        return irc.server.IRCClient.handle_privmsg(self, params)


@pytest.fixture(scope='function')
def mock_get_waittime(monkeypatch):
    m = mock.Mock()
    m.return_value = 0
    monkeypatch.setattr(connection.ServerConnection3, 'get_waittime', m)


@pytest.fixture(scope='function')
def ircserver(request):
    ircserver = irc.server.IRCServer(('0.0.0.0', 0), IRCServerClient)

    def fin():
        IRCServerClient.password = queue.Queue()
        IRCServerClient.joined = queue.Queue()
        IRCServerClient.quited = queue.Queue()
        IRCServerClient.messages = queue.Queue()
    request.addfinalizer(fin)
    return ircserver


@pytest.fixture(scope='function')
def mock_get_chat_server(ircserver, authts):
    def get_chat_server(channel):
        return ircserver.socket.getsockname()
    authts.get_chat_server = get_chat_server
    user = mock.Mock()
    authts.current_user = user
    return authts


@pytest.fixture(scope='function')
def ircclient(ircserver, mock_get_chat_server, channel1, mock_get_waittime):
    authts = mock_get_chat_server
    authts.current_user.name = 'testuser'
    client = IRCChatClient(authts, channel1)
    return client


@pytest.fixture(scope='function')
def ircclient2(ircserver, mock_get_chat_server, channel1, mock_get_waittime):
    authts = mock_get_chat_server
    authts.current_user.name = 'testuser2'
    client = IRCChatClient(authts, channel1, queuesize=10)
    return client


@pytest.fixture(scope='function')
def ircclient2thread(request, ircclient2):
    t = threading.Thread(target=ircclient2.process_forever)
    t.setDaemon(True)

    def fin():
        ircclient2.shutdown()
        t.join()
        pass

    request.addfinalizer(fin)
    t.start()


@pytest.fixture(scope='function')
def ircthreads(request, ircserver, ircclient):
    t1 = threading.Thread(target=ircserver.serve_forever)
    t2 = threading.Thread(target=ircclient.process_forever,
                          kwargs={'timeout': 0.2})
    t1.setDaemon(True)
    t2.setDaemon(True)

    def fin():
        ircclient.shutdown()
        ircserver.shutdown()
        t2.join()
        t1.join()
        pass

    request.addfinalizer(fin)
    t1.start()
    t2.start()


def simulate_client_server_interaction(ircserver, ircclient):
    """Wait for the client to join, then send messages, then quit."""
    ircclient.joined.wait()  # wait for in and out connection

    ircclient.send_msg('hahaha')
    ircclient.send_msg('hihihi')

    # wait till messages have arrived at the server
    messages = set()
    for i in range(2):
        messages.add(IRCServerClient.messages.get())

    ircclient.shutdown()
    # wait till the client (in other thread) is actually shut down
    # wait for in and out connection
    quited = set()
    for i in range(2):
        quited.add(IRCServerClient.quited.get())
    return messages, quited


@pytest.mark.timeout(6)
def test_client(ircserver, ircclient, ircthreads, access_token):
    messages, quited = simulate_client_server_interaction(ircserver, ircclient)
    testchannel = '#test_channel'
    testuser = 'testuser%s!testuser%s@localhost'
    testuserin = testuser % ('in', 'in')
    testuserout = testuser % ('out', 'out')
    expectedpw = (('None!None@localhost', 'oauth:%s' % access_token),
                  ('None!None@localhost', 'oauth:%s' % access_token))
    expectedjoin = ((testuserin, testchannel),
                    (testuserout, testchannel))
    expectedmessages = ((testuserout, '#test_channel :hahaha'),
                        (testuserout, '#test_channel :hihihi'))
    passwords = set()
    joined = set()
    for i in range(2):
        passwords.add(IRCServerClient.password.get())
        joined.add(IRCServerClient.joined.get())

    assert passwords == set(expectedpw)
    assert joined == set(expectedjoin)
    assert quited == set(((testuserin, ''),
                          (testuserout, '')))
    assert messages == set(expectedmessages)


def test_disconnect(ircserver, ircclient):
    ircclient.channel = None
    for c in [ircclient.in_connection, ircclient.out_connection]:
        assert not c.connected, 'The client should disconnect the connection, \
when you set the channel to None'


def assert_client_got_message(client, message):
    """Assert that the client has a message in the message queue,
    that is eqaul to the given one

    :param client: an irc client
    :type client: :class:`chat.IRCClient`
    :param message: the message to test against
    :type message: :class:`pytwitcherapi.chat.message.Message`
    :raises: :class:`AssertionError`
    """
    try:
        msg = client.messages.get(timeout=1)
        assert msg == message
    except queue.Empty:
        raise AssertionError('ircclient did not store the message in the message queue')


@pytest.mark.timeout(10)
def test_message_queue(ircclient, ircclient2, ircthreads, ircclient2thread):
    c = message.Chatter('testuser2out!testuser2out@localhost')
    m1 = message.Message3(c, '#test_channel', 'mic check')
    m2 = message.Message3(c, '#test_channel', 'onetwo')

    ircclient.joined.wait()
    ircclient2.joined.wait()

    for m in [m1, m2]:
        ircclient2.send_msg(m.text)
        assert_client_got_message(ircclient, m)


def _send_messages(client):
    """Send 15 messages. Text is the index of the message.
    Send 7 private to testuser2 and 8 public ones to #test_channel.
    """
    # send 7 private
    for i in range(7):
        client.privmsg('testuser2in', '%i' % i)
    # the rest public
    for i in range(7, 15):
        client.privmsg('#test_channel', '%i' % i)


@pytest.mark.timeout(10)  # if it times out, maybe the store_message method uses a blocking put
def test_message_queue_full(ircclient, ircclient2, ircthreads, ircclient2thread):
    ircclient2.signalat = 15
    ircclient.joined.wait()
    ircclient2.joined.wait()

    _send_messages(ircclient)

    ircclient2.received.wait()

    assert ircclient2.messages.full(), '15 messages have been sent. The queue should be full.'
    assert ircclient2.messages.qsize() == 10, '15 messages have been sent, but the queue should have a maxsize of 10'
    # assert only the last ten messages are in the queue
    for i in range(5, 15):
        assert ircclient2.messages.get(timeout=1).text == '%i' % i,\
            "The message queue should only have the last ten messages.\
 So the messages should be '5', '6'... until '14'"


@pytest.fixture(scope='function')
def mock_time_sleep(monkeypatch):
    timemock = mock.Mock()
    sleepmock = mock.Mock()
    timemock.sleep = sleepmock
    monkeypatch.setattr(connection, 'time', timemock)
    return sleepmock


@pytest.fixture(scope='function')
def mock_get_waittime2(monkeypatch):
    m = mock.Mock()
    m.return_value = 10
    monkeypatch.setattr(connection.ServerConnection3, 'get_waittime', m)
    return m


@pytest.fixture(scope='function')
def mock_send_raw(monkeypatch):
    m = mock.Mock()
    monkeypatch.setattr(irc.client.ServerConnection, 'send_raw', m)
    return m


def test_send_raw_wait(mock_time_sleep, mock_get_waittime2, mock_send_raw):
    con = connection.ServerConnection3(None)
    con.send_raw('Test')
    mock_time_sleep.assert_called_with(10)
    mock_send_raw.assert_called_with('Test')


def test_not_authorized(ts, channel1):
    with pytest.raises(exceptions.NotAuthorizedError):
        chat.IRCClient(ts, channel1)
