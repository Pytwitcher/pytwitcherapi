import sys
import threading
import time

import irc.server
import mock
import pytest

from pytwitcherapi import chat

if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue


class IRCChatClient(chat.IRCClient):
    """Little client that displays, when he joined a channel,
    so we can wait until sending messages"""
    def __init__(self, session, channel, queuesize=0):
        super(IRCChatClient, self).__init__(session, channel, queuesize)
        self.mutex = threading.RLock()
        self.joined = False
        self.messagecount = 0  # total messages received

    def on_join(self, connection, event):
        self.joined = True

    def store_message(self, connection, event):
        super(IRCChatClient, self).store_message(connection, event)
        self.messagecount += 1


class IRCServerClient(irc.server.IRCClient):
    """A simple handler for the server. Tracks a view
    events, so they can be checked later.

    Remember to reset him after each use, by setting the class
    variables to their default.
    """
    password = None
    joined = None
    quited = None
    messages = []

    def __init__(self, *args, **kwargs):
        irc.server.IRCClient.__init__(self, *args, **kwargs)

    def handle_quit(self, params):
        IRCServerClient.quited = (self.client_ident(), params)
        return irc.server.IRCClient.handle_quit(self, params)

    def handle_join(self, params):
        IRCServerClient.joined = (self.client_ident(), params)
        return irc.server.IRCClient.handle_join(self, params)

    def handle_pass(self, params):
        IRCServerClient.password = (self.client_ident(), params)

    def handle_privmsg(self, params):
        IRCServerClient.messages.append((self.client_ident(), params))
        return irc.server.IRCClient.handle_privmsg(self, params)


@pytest.fixture(scope='function')
def ircserver(request):
    ircserver = irc.server.IRCServer(('0.0.0.0', 0), IRCServerClient)

    def fin():
        IRCServerClient.password = None
        IRCServerClient.joined = None
        IRCServerClient.quited = None
        IRCServerClient.messages = []
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
def ircclient(ircserver, mock_get_chat_server, channel1):
    authts = mock_get_chat_server
    authts.current_user.name = 'testuser'
    client = IRCChatClient(authts, channel1)
    return client


@pytest.fixture(scope='function')
def ircclient2(ircserver, mock_get_chat_server, channel1):
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
    while not ircclient.joined:
        time.sleep(0)

    ircclient.send_msg('hahaha')
    ircclient.send_msg('hihihi')
    # wait till messages have arrived at the server
    while not len(IRCServerClient.messages) == 2:
        time.sleep(0)

    ircclient.shutdown()
    # wait till the clien (in other thread) is actually shut down
    while not IRCServerClient.quited:
        time.sleep(0)


@pytest.mark.timeout(10)
def test_client(ircserver, ircclient, ircthreads, access_token):
    simulate_client_server_interaction(ircserver, ircclient)
    testuser = 'testuser!testuser@localhost'
    expectedpw = ('None!None@localhost', 'oauth:%s' % access_token)
    expectedjoin = (testuser, '#test_channel')
    expectedmessages = [(testuser, '#test_channel :hahaha'),
                        (testuser, '#test_channel :hihihi')]
    assert IRCServerClient.password == expectedpw
    assert IRCServerClient.joined == expectedjoin
    assert IRCServerClient.quited == (testuser, '')
    assert IRCServerClient.messages == expectedmessages


def test_disconnect(ircserver, ircclient):
    ircclient.channel = None
    assert not ircclient.connection.connected, 'The client should disconnect the connection, \
when you set the channel to None'


def assert_client_got_message(client, message):
    """Assert that the client has a message in the message queue,
    that is eqaul to the given one

    :param client: an irc client
    :type client: :class:`chat.IRCClient`
    :param message: the message to test against
    :type message: :class:`chat.Message`
    :raises: :class:`AssertionError`
    """
    try:
        msg = client.messages.get(timeout=1)
        assert msg == message
    except queue.Empty:
        raise AssertionError('ircclient did not store the message in the message queue')


@pytest.mark.timeout(10)
def test_message_queue(ircclient, ircclient2, ircthreads, ircclient2thread):
    c = chat.Chatter('testuser2!testuser2@localhost')
    m1 = chat.Message3(c, '#test_channel', 'mic check')
    m2 = chat.Message3(c, '#test_channel', 'onetwo')

    while not ircclient2.joined:
        time.sleep(0)

    for m in [m1, m2]:
        ircclient2.send_msg(m.text)
        assert_client_got_message(ircclient, m)


def _send_messages(client):
    """Send 15 messages. Text is the index of the message.
    Send 7 private to testuser2 and 8 public ones to #test_channel.
    """
    # send 7 private
    for i in range(7):
        client.privmsg('testuser2', '%i' % i)
    # the rest public
    for i in range(7, 15):
        client.privmsg('#test_channel', '%i' % i)


@pytest.mark.timeout(10)  # if it times out, maybe the store_message method uses a blocking put
def test_message_queue_full(ircclient, ircclient2, ircthreads, ircclient2thread):
    while not ircclient2.joined:
        time.sleep(0)

    _send_messages(ircclient)

    while ircclient2.messagecount != 15:
        time.sleep(0)

    assert ircclient2.messages.full(), '15 messages have been sent. The queue should be full.'
    assert ircclient2.messages.qsize() == 10, '15 messages have been sent, but the queue should have a maxsize of 10'
    # assert only the last ten messages are in the queue
    for i in range(5, 15):
        assert ircclient2.messages.get(timeout=1).text == '%i' % i,\
            "The message queue should only have the last ten messages.\
 So the messages should be '5', '6'... until '14'"
