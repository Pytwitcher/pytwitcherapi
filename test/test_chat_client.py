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
def ircclient(ircserver, authts, channel1):
    def get_chat_server(channel):
        return ircserver.socket.getsockname()
    authts.get_chat_server = get_chat_server
    user = mock.Mock()
    user.name = 'testuser'
    authts.current_user = user
    client = IRCChatClient(authts, channel1)
    return client


@pytest.fixture(scope='function')
def ircclient2(ircserver, authts, channel1):
    def get_chat_server(channel):
        return ircserver.socket.getsockname()
    authts.get_chat_server = get_chat_server
    user = mock.Mock()
    user.name = 'testuser2'
    authts.current_user = user
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


@pytest.mark.timeout(10)
def test_client(ircserver, ircclient, ircthreads, access_token):
    while not ircclient.joined:
        time.sleep(0.1)

    ircclient.send_msg('hahaha')
    ircclient.send_msg('hihihi')
    # wait till messages have arrived at the server
    while not IRCServerClient.messages:
        time.sleep(0.1)

    ircclient.shutdown()
    # wait till the clien (in other thread) is actually shut down
    while not IRCServerClient.quited:
        time.sleep(0.1)

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
    assert not ircclient.connection.connected


@pytest.mark.timeout(10)
def test_message_queue(ircclient, ircclient2, ircthreads, ircclient2thread):
    c = chat.Chatter('testuser2!testuser2@localhost')
    m1 = chat.Message3(c, '#test_channel', 'mic check')
    m2 = chat.Message3(c, '#test_channel', 'onetwo')

    while not ircclient2.joined:
        time.sleep(0)

    for m in [m1, m2]:
        ircclient2.send_msg(m.text)
        try:
            msg = ircclient.messages.get(timeout=1)
            assert msg == m
        except queue.Empty:
            raise AssertionError('ircclient did not store the message in the message queue')


@pytest.mark.timeout(10)  # if it times out, maybe the store_message method uses a blocking put
def test_message_queue_full(ircclient, ircclient2, ircthreads, ircclient2thread):
    while not ircclient2.joined:
        time.sleep(0)

    # send 7 private
    for i in range(7):
        ircclient.privmsg('testuser2', '%i' % i)
    # the rest public
    for i in range(7, 15):
        ircclient.privmsg('#test_channel', '%i' % i)

    while ircclient2.messagecount != 15:
        time.sleep(0)

    assert ircclient2.messages.full()
    assert ircclient2.messages.qsize() == 10
    # assert only the last ten messages are in the queue
    for i in range(5, 15):
        assert ircclient2.messages.get(timeout=1).text == '%i' % i,\
            "The message queue should only have the last ten messages.\
 So the messages should be '5', '6'... until '14'"
