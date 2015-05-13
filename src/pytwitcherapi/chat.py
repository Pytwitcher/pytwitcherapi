"""IRC client for interacting with the chat of a channel."""
import re  # I got a bad feeling about this
import functools  # nopep8
import logging
import sys

import irc.client
import irc.events
import irc.ctcp

if sys.version_info[0] == 2:
    import Queue as queue
else:
    import queue


log = logging.getLogger(__name__)


__all__ = ['IRCClient']


class Tag(object):
    """An irc v3 tag
    """

    _tagpattern = r'^((?P<vendor>[a-zA-Z0-9\.\-]+)/)?(?P<name>[^ =]+)(=(?P<value>[^ \r\n;]+))?'
    _parse_regexp = re.compile(_tagpattern)

    def __init__(self, name, value=None, vendor=None):
        """Initialize a new tag called name

        :param name: The name of the tag
        :type name: :class:`str`
        :param value: The value of a tag
        :type value: :class:`str` | None
        :param vendor: the vendor for vendor specific tags
        :type vendor: :class:`str` | tag
        :raises: None
        """
        super(Tag, self).__init__()
        self.name = name
        self.value = value
        self.vendor = vendor

    def __repr__(self, ):  # pragma: no cover
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s name=%s, value=%s, vendor=%s>' % (self.__class__.__name__,
                                                      self.name, self.value, self.vendor)

    def __eq__(self, other):
        """Return True if the tags are equal

        :param other: the other tag
        :type other: :class:`Tag`
        :returns: True if equal
        :rtype: :class:`bool`
        :raises: None
        """
        return self.name == other.name and\
            self.value == other.value and\
            self.vendor == other.vendor

    @classmethod
    def from_str(cls, tagstring):
        """Create a tag by parsing the tag of a message

        :param tagstring: A tag string described in the irc protocol
        :type tagstring: :class:`str`
        :returns: A tag
        :rtype: :class:`Tag`
        :raises: None
        """
        m = cls._parse_regexp.match(tagstring)
        return cls(name=m.group('name'), value=m.group('value'), vendor=m.group('vendor'))


class Emote(object):
    """Emote from the emotes tag

    An emote has an id and occurences in a message.
    So each emote is tied to a specific message.
    """

    def __init__(self, emoteid, occurences):
        """Initialize a new emote

        :param emoteid: The emote id
        :type emoteid: :class:`int`
        :param occurences: a list of occurences, e.g.
                           [(0, 4), (8, 12)]
        :type occurences: :class:`list`
        :raises: None
        """
        super(Emote, self).__init__()
        self.emoteid = emoteid
        """The emote identifier"""
        self.occurences = occurences
        """A list of occurences, e.g. [(0, 4), (8, 12)]"""

    def __repr__(self, ):
        """Return a canonical representation of the object

        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s at %s>' % (self.__class__.__name__,
                                  self.emoteid,
                                  self.occurences)

    @classmethod
    def from_str(cls, emotestr):
        """Create an emote from the emote tag key

        :param emotestr: the tag key, e.g. ``'123:0-4'``
        :type emotestr: :class:`str`
        :returns: an emote
        :rtype: :class:`Emote`
        :raises: None
        """
        emoteid, occstr = emotestr.split(':')
        occurences = []
        for occ in occstr.split(','):
            start, end = occ.split('-')
            occurences.append((int(start), int(end)))
        return cls(int(emoteid), occurences)

    def __eq__(self, other):
        """Return True if the emotes are the same

        :param other: the other emote
        :type other: :class:`Emote`
        :returns: True if equal
        :rtype: :class:`bool`
        """
        eq = self.emoteid == other.emoteid
        return eq and self.occurences == other.occurences


class Event3(irc.client.Event):
    """An IRC event with tags
    """

    def __init__(self, type, source, target, arguments=None, tags=None):
        """Initialize a new event

        :param type: a string describing the event
        :type type: :class:`str`
        :param source: The originator of the event. NickMask or server
        :type source: :class:`irc.client.NickMask` | :class:`str`
        :param target: The target of the event
        :type target: :class:`str`
        :param arguments: Any specific event arguments
        :type arguments: :class:`list` | None
        :raises: None
        """
        super(Event3, self).__init__(type, source, target, arguments)
        self.tags = tags


class ServerConnection3(irc.client.ServerConnection):
    """ServerConncetion that can handle irc v3 tags
    """

    _cmd_pat = "^(@(?P<tags>[^ ]+) +)?(:(?P<prefix>[^ ]+) +)?(?P<command>[^ ]+)( *(?P<argument> .+))?"
    _rfc_1459_command_regexp = re.compile(_cmd_pat)

    def _process_line(self, line):
        """Process the given line and handle the events

        :param line: the raw message
        :type line: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        m = self._rfc_1459_command_regexp.match(line)

        tags = self._process_tags(m.group('tags'))
        source = self._process_prefix(m.group('prefix'))
        command = self._process_command(m.group('command'))
        arguments = self._process_arguments(m.group('argument'))

        # Translate numerics into more readable strings.
        command = irc.events.numeric.get(command, command)

        if command not in ["privmsg", "notice"]:
            return super(ServerConnection3, self)._process_line(line)

        event = Event3("all_raw_messages", self.get_server_name(),
                       None, [line], tags=tags)
        self._handle_event(event)

        target, message = arguments[0], arguments[1]
        messages = irc.ctcp.dequote(message)

        if command == "privmsg":
            if irc.client.is_channel(target):
                command = "pubmsg"
        else:
            if irc.client.is_channel(target):
                command = "pubnotice"
            else:
                command = "privnotice"

        for m in messages:
            if isinstance(m, tuple):
                if command in ["privmsg", "pubmsg"]:
                    command = "ctcp"
                else:
                    command = "ctcpreply"

                m = list(m)
                log.debug("tags: %s, command: %s, source: %s, target: %s, "
                          "arguments: %s", tags, command, source, target, m)
                event = Event3(command, source, target, m, tags=tags)
                self._handle_event(event)
                if command == "ctcp" and m[0] == "ACTION":
                    event = Event3("action", source, target, m[1:], tags=tags)
                    self._handle_event(event)
            else:
                log.debug("tags: %s, command: %s, source: %s, target: %s, "
                          "arguments: %s", tags, command, source, target, [m])
                event = Event3(command, source, target, [m], tags=tags)
                self._handle_event(event)

    def _process_tags(self, tags):
        """Process the tags of the message

        :param tags: the tags string of a message
        :type tags: :class:`str` | None
        :returns: list of tags
        :rtype: :class:`list` of :class:`Tag`
        :raises: None
        """
        if not tags:
            return []
        return [Tag.from_str(x) for x in tags.split(';')]

    def _process_prefix(self, prefix):
        """Process the prefix of the message and return the source

        Sets :data:`ServerConnection3.real_server_name` if not already set.

        :param prefix: The prefix string of a message
        :type prefix: :class:`str` | None
        :returns: The prefix wrapped in :class:`irc.client.NickMask`
        :rtype: :class:`irc.client.NickMask` | None
        :raises: None
        """
        if not prefix:
            return None
        if not self.real_server_name:
            self.real_server_name = prefix
        return irc.client.NickMask(prefix)

    def _process_command(self, command):
        """Return a lower string version of the command

        :param command: the command of the message
        :type command: :class:`str` | None
        :returns: The lower case version
        :rtype: :class:`str` | None
        :raises: None
        """
        if not command:
            return None
        return command.lower()

    def _process_arguments(self, arguments):
        """Process the arguments

        :param arguments: arguments string of a message
        :type arguments: :class:`str` | None
        :returns: A list of arguments
        :rtype: :class:`list` of :class:`str` | None
        :raises: None
        """
        if not arguments:
            return None
        a = arguments.split(" :", 1)
        arglist = a[0].split()
        if len(a) == 2:
            arglist.append(a[1])
        return arglist


class Chatter(object):
    """A chat user object

    Stores information about a chat user (source of an ircevent).

    See :class:`irc.client.NickMask` for how the attributes are constructed.
    """

    def __init__(self, source):
        """Initialize a new chatter

        :param source: the source of an :class:`irc.client.Event`. E.g.
                       ``'pinky!username@example.com'``
        :type source:
        :raises: None
        """
        super(Chatter, self).__init__()
        self.full = irc.client.NickMask(source)
        """The full name (nickname!user@host)"""
        self.nickname = self.full.nick
        """The irc nickname"""
        self.user = self.full.user
        """The irc user"""
        self.host = self.full.user
        """The irc host"""
        self.userhost = self.full.userhost
        """The irc user @ irc host"""

    def __str__(self):
        """Return a nice string representation of the object

        :returns: :data:`Chatter.full`
        :rtype: :class:`str`
        """
        return str(self.full)

    def __repr__(self, ):  # pragma: no cover
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s>' % (self.__class__.__name__, self.full)


class Message(object):
    """A messag object

    Can be a private|public message from a server or user.
    """

    def __init__(self, source, target, text):
        """Initialize a new message from source to target with the given text

        :param source: The source chatter
        :type source: :class:`Chatter`
        :param target: the target
        :type target: str
        :param text: the content of the message
        :type text: :class:`str`
        :raises: None
        """
        super(Message, self).__init__()
        self.source = source
        self.target = target
        self.text = text

    def __repr__(self, ):
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        text = self.text
        if len(self.text) > 6:
            text = self.text[:5] + '...'
        return '<%s %s to %s: %s>' % (self.__class__.__name__, self.source, self.target, text)

    def __eq__(self, other):
        """Return True if source, target and text is the same

        :param other: the other message
        :type other: :class:`Message`
        :returns: True if equal
        :rtype: :class:`bool`
        """
        return self.source.full == other.source.full and self.target == other.target and self.text == other.text


class Message3(Message):
    """A message which stores information from irc v3 tags
    """

    def __init__(self, source, target, text, tags=None):
        """Initialize a new message from source to target with the given text

        :param source: The source chatter
        :type source: :class:`Chatter`
        :param target: the target
        :type target: str
        :param text: the content of the message
        :type text: :class:`str`
        :param tags: the irc v3 tags
        :type tags: :class:`list` of :class:`Tag`
        :raises: None
        """
        super(Message3, self).__init__(source, target, text)
        self.color = None
        self._emotes = []
        self._subscriber = False
        self._turbo = False
        self.user_type = None

        self.set_tags(tags)

    def __eq__(self, other):
        """Return True if source, target, text and tags is the same

        :param other: the other message
        :type other: :class:`Message`
        :returns: True if equal
        :rtype: :class:`bool`
        """
        eq = super(Message3, self).__eq__(other)
        return eq and self.color == other.color and\
            self.emotes == other.emotes and\
            self.subscriber == other.subscriber and\
            self.turbo == other.turbo and\
            self.user_type == other.user_type

    def set_tags(self, tags):
        """For every known tag, set the appropriate attribute.

        Known tags are:

            :color: The user color
            :emotes: A list of emotes
            :subscriber: True, if subscriber
            :turbo: True, if turbo user
            :user_type: None, mod, staff, global_mod, admin

        :param tags: a list of tags
        :type tags: :class:`list` of :class:`Tag` | None
        :returns: None
        :rtype: None
        :raises: None
        """
        if tags is None:
            return
        attrmap = {'color': 'color', 'emotes': 'emotes',
                   'subscriber': 'subscriber',
                   'turbo': 'turbo', 'user-type': 'user_type'}
        for t in tags:
            attr = attrmap.get(t.name)
            if not attr:
                continue
            else:
                setattr(self, attr, t.value)

    @property
    def emotes(self, ):
        """Return the emotes

        :returns: the emotes
        :rtype: :class:`list`
        :raises: None
        """
        return self._emotes

    @emotes.setter
    def emotes(self, emotes):
        """Set the emotes

        :param emotes: the key of the emotes tag
        :type emotes: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        es = []
        for estr in emotes.split('/'):
            es.append(Emote.from_str(estr))
        self._emotes = es

    @property
    def subscriber(self):
        """Return whether the message was sent from a subscriber

        :returns: True, if subscriber
        :rtype: :class:`bool`
        :raises: None
        """
        return self._subscriber

    @subscriber.setter
    def subscriber(self, issubscriber):
        """Set whether the message was sent from a subscriber

        :param issubsriber: '1', if subscriber
        :type issubscriber: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        self._subscriber = bool(int(issubscriber))

    @property
    def turbo(self):
        """Return whether the message was sent from a turbo user

        :returns: True, if turbo
        :rtype: :class:`bool`
        :raises: None
        """
        return self._turbo

    @turbo.setter
    def turbo(self, isturbo):
        """Set whether the message was sent from a turbo user

        :param issubsriber: '1', if turbo
        :type isturbo: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        self._turbo = bool(int(isturbo))


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


class Reactor3(Reactor):
    """Reactor that uses irc v3 connections

    Uses the :class:`ServerConnection3` class for connections.
    They support :class:`Event3` with tags.
    """

    def server(self, ):
        """Creates and returns a ServerConnection

        :returns: a server connection
        :rtype: :class:`ServerConnection3`
        :raises: None
        """
        c = ServerConnection3(self)
        with self.mutex:
            self.connections.append(c)
        return c


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
        exec("""def method(self, *args, **kwargs):
    f = getattr(self.connection, %r)
    p = functools.partial(f, *args, **kwargs)
    self.reactor.execute_delayed(0, p)""" % m, globals())
        f = getattr(irc.client.ServerConnection, m)
        method.__name__ = m  # nopep8
        method.__doc__ = f.__doc__  # nopep8
        setattr(cls, method.__name__, method)  # nopep8


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
        self.messages = queue.Queue(maxsize=queuesize)
        """A queue which stores all private and public messages.
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
        source = Chatter(event.source)
        m = Message3(source, event.target, event.arguments[0], event.tags)

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
