import threading
import time

import mock
import pytest
import irc.server

from pytwitcherapi import chat


class IRCChatClient(chat.IRCClient):
    """Little client that displays, when he joined a channel,
    so we can wait until sending messages"""
    def __init__(self, session, channel):
        super(IRCChatClient, self).__init__(session, channel)
        self.joined = False

    def on_join(self, connection, event):
        self.joined = True


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
def ircthreads(request, ircserver, ircclient):
    t1 = threading.Thread(target=ircserver.serve_forever)
    t2 = threading.Thread(target=ircclient.process_forever,
                          kwargs={'timeout': 0.2})

    def fin():
        ircclient.shutdown()
        ircserver.shutdown()
        t2.join()
        t1.join()
    request.addfinalizer(fin)
    t1.start()
    t2.start()


@pytest.mark.timeout(10)
def test_client(ircserver, ircclient, ircthreads, access_token):
    while not ircclient.joined:
        time.sleep(0.1)

    ircclient.send_privmsg('hahaha')
    ircclient.send_privmsg('hihihi')
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
