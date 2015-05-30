"""IRC client for interacting with the chat of a channel."""
from __future__ import absolute_import

import functools
import logging
import sys
import threading

import irc.client

from . import message
from . import connection
from pytwitcherapi import exceptions

if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue

log = logging.getLogger(__name__)

__all__ = ['IRCClient']


class Reactor(irc.client.Reactor):
    """Reactor that can exit the process_forever loop.

    The reactor is responsible for managing the connections,
    and handling the events that come in to the connections.

    Simply call :meth:`Reactor.shutdown` while the reactor is in a loop.

    For more information see :class:`irc.client.Reactor`.
    """
    def __do_nothing(*args, **kwargs):
        pass

    def __init__(self, on_connect=__do_nothing,
                 on_disconnect=__do_nothing,
                 on_schedule=__do_nothing):
        """Initialize a reactor.

        :param on_connect: optional callback invoked when a new connection
                           is made.
        :param on_disconnect: optional callback invoked when a socket is
                              disconnected.
        :param on_schedule: optional callback, usually supplied by an external
                            event loop, to indicate in float seconds that the
                            client needs to process events that many seconds
                            in the future. An external event loop will
                            implement this callback to schedule a call to
                            process_timeout.
        """
        super(Reactor, self).__init__(on_connect=on_connect,
                                      on_disconnect=on_disconnect,
                                      on_schedule=on_schedule)
        self._looping = threading.Event()

    def process_forever(self, timeout=0.2):
        """Run an infinite loop, processing data from connections.

        This method repeatedly calls process_once.

        :param timeout: Parameter to pass to
                        :meth:`irc.client.Reactor.process_once`
        :type timeout: :class:`float`
        """
        # This loop should specifically *not* be mutex-locked.
        # Otherwise no other thread would ever be able to change
        # the shared state of a Reactor object running this function.
        log.debug("process_forever(timeout=%s)", timeout)
        self._looping.set()
        while self._looping.is_set():
            self.process_once(timeout)

    def shutdown(self):
        """Disconnect all connections and end the loop

        :returns: None
        :rtype: None
        :raises: None
        """
        log.debug('Shutting down %s' % self)
        self.disconnect_all()
        self._looping.clear()


class Reactor3(Reactor):
    """Reactor that uses irc v3 connections

    Uses the :class:`ServerConnection3` class for connections.
    They support :class:`Event3` with tags.
    """

    def server(self, ):
        """Creates and returns a ServerConnection

        :returns: a server connection
        :rtype: :class:`connection.ServerConnection3`
        :raises: None
        """
        c = connection.ServerConnection3(self)
        with self.mutex:
            self.connections.append(c)
        return c


def _wrap_execute_delayed(funcname):
    """Warp the given method, so it gets executed by the reactor

    Wrap a method of :data:`IRCCLient.out_connection`.

    The returned function should be assigned to a :class:`irc.client.SimpleIRCClient` class.

    :param funcname: the name of a :class:`irc.client.ServerConnection` method
    :type funcname: :class:`str`
    :returns: a new function, that executes the given one via :class:`irc.client.Reactor.execute_delayed`
    :raises: None
    """
    def method(self, *args, **kwargs):
        f = getattr(self.out_connection, funcname)
        p = functools.partial(f, *args, **kwargs)
        self.reactor.execute_delayed(0, p)
    method.__name__ = funcname
    return method


def add_serverconnection_methods(cls):
    """Add a bunch of methods to an :class:`irc.client.SimpleIRCClient`
    to send commands and messages.

    Basically it wraps a bunch of methdos from
    :class:`irc.client.ServerConnection` to be
    :meth:`irc.client.Reactor.execute_delayed`.
    That way, you can easily send, even if the IRCClient is running in
    :class:`IRCClient.process_forever` in another thread.

    On the plus side you can use positional and keyword arguments instead of just positional ones.

    :param cls: The class to add the methods do.
    :type cls: :class:`irc.client.SimpleIRCClient`
    :returns: None
    """
    methods = ['action', 'admin', 'cap', 'ctcp', 'ctcp_reply',
               'globops', 'info', 'invite', 'ison', 'join',
               'kick', 'links', 'list', 'lusers', 'mode',
               'motd', 'names', 'nick', 'notice', 'oper', 'part',
               'part', 'pass_', 'ping', 'pong', 'privmsg',
               'privmsg_many', 'quit', 'send_raw', 'squit',
               'stats', 'time', 'topic', 'trace', 'user', 'userhost',
               'users', 'version', 'wallops', 'who', 'whois', 'whowas']
    for m in methods:
        method = _wrap_execute_delayed(m)
        f = getattr(irc.client.ServerConnection, m)
        method.__doc__ = f.__doc__
        setattr(cls, method.__name__, method)
    return cls


@add_serverconnection_methods
class IRCClient(irc.client.SimpleIRCClient):
    """Simple IRC client which can connect to a single
    :class:`pytwitcherapi.Channel`.

    You need an authenticated session with scope ``chat_login``.
    Call :meth:`IRCClient.process_forever` to start the event loop.
    This will block the current thread though.
    Calling :meth:`IRCClient.shutdown` will stop the loop.

    There are a lot of methods that can make the client send
    commands while the client is in its event loop.
    These methods are wrapped ones of :class:`irc.client.ServerConnection`.
    They will always use :data:`IRCClient.out_connection`!

    You can implement handlers for all sorts of events by
    subclassing and creating a method called ``on_<event.type>``.
    Note that :data:`IRCClient.out_connection` will only get to the
    :meth:`IRCClient.on_welcome` event (and then join a channel)
    and the :meth:`IRCClient.on_join` event.
    For all other events, the :data:`IRCClient.in_connection` will
    handle it and the other one will ignore it.
    This behaviour is implemented in :meth:`IRCCLient._dispatcher`

    Little example with threads. Change ``input`` to ``raw_input`` for
    python 2::

      import threading

      from pytwitcherapi import chat

      session = ...  # we assume an authenticated TwitchSession
      channel = session.get_channel('somechannel')
      client = chat.IRCClient(session, channel)
      t = threading.Thread(target=client.process_forever,
                           kwargs={'timeout': 0.2})
      t.start()

      try:
          while True:
              m = input('Send Message:')
              if not m: break;
              # will be processed in other thread
              client.send_msg(m)
      finally:
          client.shutdown()
          t.join()

    """

    reactor_class = Reactor3

    def __init__(self, session, channel, queuesize=100):
        """Initialize a new irc client which can connect to the given
        channel.

        :param session: a authenticated session. Used for quering
                        the right server and the login username.
        :type session: :class:`pytwitcherapi.TwitchSession`
        :param channel: a channel
        :type channel: :class:`pytwitcherapi.Channel`
        :param queuesize: The queuesize for storing messages in :data:`IRCClient.messages`.
                          If 0, unlimited size.
        :type queuesize: :class:`int`
        :raises: :class:`exceptions.NotAuthorizedError`
        """
        super(IRCClient, self).__init__()
        del self.connection
        self.in_connection = self.reactor.server()
        """Connection that receives messages"""
        self.out_connection = self.reactor.server()
        """Connection that sends messages"""
        self.session = session
        """an authenticated session. Used for quering
        the right server and the login username."""
        if not self.session.authorized:
            raise exceptions.NotAuthorizedError('Please authorize the session first.')
        self.login_user = self.session.current_user
        """The user that is used for logging in to the chat"""
        self.channel = channel
        """The channel to connect to.
        When setting the channel, automatically connect to it.
        If channel is None, disconnect.
        """
        self.shutdown = self.reactor.shutdown
        """Call this method for shutting down the client. This is thread safe."""
        self.process_forever = self.reactor.process_forever
        """Call this method to process messages until shutdown() is called.

        :param timeout: timeout for waiting on data in seconds
        :type timeout: :class:`float`
        """
        self.messages = queue.Queue(maxsize=queuesize)
        """A queue which stores all private and public
        :class:`pytwitcherapi.chat.message.Message3`.
        Usefull for accessing messages from another thread.
        """

    def __repr__(self, ):  # pragma: no cover
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        if self.channel:
            r = '<%s #%s>' % (self.__class__.__name__, self.channel.name)
        else:
            r = '<%s>' % (self.__class__.__name__)
        return r

    @property
    def channel(self, ):
        """Get the channel

        :returns: The channel to connect to
        :rtype: :class:`pytwitcherapi.Channel`
        :raises: None
        """
        return self._channel

    @channel.setter
    def channel(self, channel):
        """Set the channel and connect to it

        If the channel is None, disconnect.

        :param channel: The channel to connect to
        :type channel: :class:`pytwitcherapi.Channel` | None
        :returns: None
        :rtype: None
        :raises: None
        """
        connections = [self.in_connection, self.out_connection]
        self._channel = channel
        if not channel:
            self.target = None
            for c in connections:
                if c.connected:
                    c.disconnect("Disconnect.")
            return
        self.target = '#%s' % channel.name
        ip, port = self.session.get_chat_server(channel)
        nickname = self.login_user.name
        password = 'oauth:%s' % self.session.token['access_token']
        self.log = logging.getLogger(str(self))
        for c in connections:
            self._connect(c, ip, port, nickname, password)

    def _connect(self, connection, ip, port, nickname, password):
        """Connect the given connection

        :param connection: the connection to connect to an irc server
        :type connection: :class:`irc.client.ServerConnection`
        :param ip: the ip to connect to
        :type ip: :class:`str`
        :param port: the port of the server
        :type port: :class:`int`
        :param nickname: the nickname to use
        :type nickname: :class:`str`
        :param password: the password to use. includes the oauth token
        :type password: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        connection.connect(server=ip, port=port,
                           nickname=nickname,
                           username=nickname,
                           password=password)

    def _dispatcher(self, connection, event):
        """Dispatch events to on_<event.type> method, if present.

        For out_connection only dispatch the welcome and join method, so
        it can join a channel.

        :param connection: the connection that received an event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to dispatch
        :type event: :class:`irc.client.Event`
        :returns: None
        :raises: None
        """
        log.debug("_dispatcher: %s", event.type)

        if connection is self.out_connection and event.type not in ('welcome', 'join'):
            return
        method = getattr(self, "on_" + event.type, lambda c, e: None)
        method(connection, event)

    def on_welcome(self, connection, event):
        """Handle the welcome event

        Automatically join the channel.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        if irc.client.is_channel(self.target):
            connection.cap('LS')
            connection.cap('REQ', 'twitch.tv/tags')
            connection.cap('END')
            self.log.debug('Joining %s, %s', connection, event)
            connection.join(self.target)

    def store_message(self, connection, event):
        """Store the message of event in :data:`IRCClient.messages`.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        m = message.Message3.from_event(event)
        while True:
            try:
                self.messages.put(m, block=False)
                break
            except queue.Full:
                self.messages.get()

    def on_pubmsg(self, connection, event):
        """Handle the public message event

        This stores the message in :data:`IRCClient.messages` via :meth:`IRCClient.store_message`.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        self.store_message(connection, event)

    def on_privmsg(self, connection, event):
        """Handle the private message event

        This stores the message in :data:`IRCClient.messages` via :meth:`IRCClient.store_message`.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        self.store_message(connection, event)

    def send_msg(self, message):
        """Send the given message to the channel

        This is a convenience method for :meth:`IRCClient.privmsg`, which uses the
        current channel as target. This method is thread safe and can be called
        from another thread even if the client is running in :meth:`IRCClient.process_forever`.

        :param message: The message to send
        :type message: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        self.privmsg(target=self.target, text=message)


class ChatServerStatus(object):
    """Useful for comparing the performance of servers.

    You can query the `status <http://twitchstatus.com/api/status?type=chat>`_
    of twitch chat servers. This class can easily wrap the result and
    sort the servers.
    """

    def __init__(self, server, ip=None, port=None,
                 status=None, errors=None,
                 lag=None, description=''):
        """Initialize a chat server status.

        :param server: the server address including port. E.g. ``"0.0.0.0:80"``
        :type server: :class:`str`
        :param ip: the ip address
        :type ip: :class:`str`
        :param port: the port number
        :type port: :class:`int`
        :param status: the server status. E.g. ``"offline"``, ``"online"``
        :type status: :class:`str`
        :param errors: the amount of errors in the last 5 min.
        :type errors: :class:`int`
        :param lag: the latency in ms
        :type lag: :class:`int`
        :param description: Wheter it is a main chat server or
                            event server or group chat.
        :type description: :class:`str`
        """
        self.address = server
        i, p = self.address.split(':')
        self.ip = ip or i
        self.port = port or int(p)
        self.status = status
        self.errors = errors
        self.lag = lag
        self.description = description

    def __repr__(self):  # pragma: no cover
        return "<%s %s, %s, %s, %s>" % (self.__class__.__name__, self.address,
                                        self.status, self.errors, self.lag)

    def __eq__(self, other):
        """Servers are equal if the address is equal.

        :param other: either an other server status or an adress
        :type other: :class:`ChatServerStatus` | :class:`str`
        :returns: True, if equal
        :rtype: :class:`bool`
        """
        if isinstance(other, str):
            return self.address == other
        if isinstance(other, ChatServerStatus):
            return self.address == other.address
        return self is other

    def __lt__(self, other):
        """Return whether a server status is lesser than the other.

        A server status is lesser when:

          1. it's status is worse than other. Status values:

             * online - 1
             * slow - 2
             * everything else - 3
             * offline - 99

          2. It has more errors.
          3. It has more lags.

        :param other: the other server status to compare
        :type other: :class:`ChatServerStatus`
        :returns: True, if lesser than other
        :rtype: :class:`bool`
        """
        statusd = {'online': 0,
                   'slow': 1,
                   'offline': 99}
        if self.status != other.status:
            return statusd.get(self.status, 2) < statusd.get(other.status, 2)
        if self.errors == other.errors:
            return self.lag < other.lag
        return self.errors < other.errors
