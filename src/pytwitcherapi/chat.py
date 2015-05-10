"""IRC client for interacting with the chat of a channel."""
import logging

import irc.client


log = logging.getLogger(__name__)


class Reactor(irc.client.Reactor):
    """Reactor that can exit the process_forever loop.

    Simply call :meth:`Reactor.shutdown`.

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
        self._looping = True

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
        self._looping = True
        while self._looping:
            self.process_once(timeout)

    def shutdown(self):
        """Disconnect all connections and end the loop

        :returns: None
        :rtype: None
        :raises: None
        """
        log.debug('Shutting down %s' % self)
        self.disconnect_all()
        with self.mutex:
            self._looping = False


def add_serverconnection_methods(cls):
    """Add a bunch of methods to an :class:`irc.client.SimpleIRCClient`
    to send commands and messages.

    Basically it wraps a bunch of methdos from
    :class:`irc.client.ServerConnection` to be
    :meth:`irc.client.Reactor.execute_delayed`.
    That way, you can easily send, even if the IRCClient is running in
    :class:`IRCClient.process_forever` in another thread.

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
        exec("""def method(self, *args):
    f = getattr(self.connection, %r)
    self.reactor.execute_delayed(0, f, arguments=args)""" % m)
        f = getattr(irc.client.ServerConnection, m)
        method.__name__ = m
        method.__doc__ = f.__doc__
        setattr(cls, method.__name__, method)


class IRCClient(irc.client.SimpleIRCClient):
    """Simple IRC client which can connect to a single
    :class:`pytwitcherapi.Channel`.

    You need an authenticated session with scope ``chat_login``.
    Call :meth:`IRCClient.process_forever` to start the event loop.
    This will block the current thread though.
    Calling :meth:`IRCClient.shutdown` will stop the loop.

    To send a message while the client is in its event loop, use
    :meth:`IRCClient.send_msg`.

    Little example with threads. Change ``input`` to ``raw_input`` for
    python 2::

      import threading

      from pytwitcherapi import chat

      session = ...  # we assume an authenticated TwitchSession
      channel = session.get_channel('somechannel')
      client = chat.IRCClient(session, channel)
      t = threading.Thread(target=ircclient.process_forever,
                           kwargs={'timeout': 0.2})
      t.start()

      try:
          while True:
              m = input('Send Message:')
              if not m: break;
              # will be processed in other thread
              client.send_privmsg(m)
      finally:
          client.shutdown()
          t.join()

    """

    reactor_class = Reactor

    def __init__(self, session, channel):
        """Initialize a new irc client which can connect to the given
        channel.

        :param session: a authenticated session. Used for quering
                        the right server and the login username.
        :type session: :class:`pytwitcherapi.TwitchSession`
        :param channel: a channel
        :type channel: :class:`pytwitcherapi.Channel`
        :raises: None
        """
        super(IRCClient, self).__init__()
        self.session = session
        """a authenticated session. Used for quering
        the right server and the login username."""
        self.login_user = self.session.current_user or self.session.fetch_login_user()
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

    def __repr__(self, ):
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
        self._channel = channel
        if not channel:
            self.target = None
            if self.connection.connected:
                self.connection.disconnect("Disconnect.")
            return
        self.target = '#%s' % channel.name
        ip, port = self.session.get_chat_server(channel)
        nickname = username = self.login_user.name
        password = 'oauth:%s' % self.session.token['access_token']
        self.log = logging.getLogger(str(self))
        self.connection.connect(server=ip, port=port,
                                nickname=nickname,
                                username=username,
                                password=password)

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
            self.log.debug('Joining %s, %s', connection, event)
            connection.join(self.target)

    def on_pubmsg(self, connection, event):
        """Handle the public message event

        This does nothing. Override to handle public messages.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        self.log.info('%s :%s', event.target, event.arguments[0])

    def on_privmsg(self, connection, event):
        """Handle the private message event

        This does nothing. Override to handle private messages.

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        self.log.info('%s :%s', event.target, event.arguments[0])


add_serverconnection_methods(IRCClient)


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
