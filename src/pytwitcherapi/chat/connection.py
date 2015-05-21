import collections
import logging
import re
import time

import irc.client

from . import message

__all__ = ['Event3', 'ServerConnection3']

log = logging.getLogger(__name__)


class Event3(irc.client.Event):
    """An IRC event with tags

    See `tag specification <http://ircv3.net/specs/core/message-tags-3.2.html>`_.
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

    def __repr__(self, ):  # pragma: no cover
        """Return a canonical representation of the object

        :rtype: :class:`str`
        :raises: None
        """
        args = (self.__class__.__name__, self.type, self.source, self.target, self.arguments, self.tags)
        return '<%s %s, %s to %s, %s, tags: %s>' % args

    def __eq__(self, other):
        """Return True, if the events share equal attributes

        :param other: the other event to compare
        :type other: :class:`Event3`
        :returns: True, if equal
        :rtype: :class:`bool`
        :raises: None
        """
        return self.type == other.type and\
            self.source == other.source and\
            self.target == other.target and\
            self.arguments == other.arguments and\
            self.tags == other.tags


class ServerConnection3(irc.client.ServerConnection):
    """ServerConncetion that can handle irc v3 tags

    Tags are only handled for privmsg, pubmsg, notice events.
    All other events might be handled the old way.
    """

    _cmd_pat = "^(@(?P<tags>[^ ]+) +)?(:(?P<prefix>[^ ]+) +)?(?P<command>[^ ]+)( *(?P<argument> .+))?"
    _rfc_1459_command_regexp = re.compile(_cmd_pat)

    def __init__(self, reactor, msglimit=20, limitinterval=30):
        """Initialize a connection that has a limit to sending messages

        :param reactor: the reactor of the connection
        :type reactor: :class:`irc.client.Reactor`
        :param msglimit: the maximum number of messages to send in limitinterval
        :type msglimit: :class:`int`
        :param limitinterval: the timeframe in seconds in which you can only send
                              as many messages as in msglimit
        :type limitinterval: :class:`int`
        :raises: None
        """
        super(ServerConnection3, self).__init__(reactor)
        self.sentmessages = collections.deque(maxlen=msglimit + 1)
        """A queue with timestamps form the last sent messages.
        So we can track if we send to many messages."""
        self.limitinterval = limitinterval
        """the timeframe in seconds in which you can only send
        as many messages as in :data:`ServerConncetion3msglimit`"""

    def get_waittime(self):
        """Return the appropriate time to wait, if we sent too many messages

        :returns: the time to wait in seconds
        :rtype: :class:`float`
        :raises: None
        """
        now = time.time()
        self.sentmessages.appendleft(now)
        if len(self.sentmessages) == self.sentmessages.maxlen:
            # check if the oldes message is older than
            # limited by self.limitinterval
            oldest = self.sentmessages[-1]
            waittime = self.limitinterval - (now - oldest)
            if waittime > 0:
                return waittime + 1  # add a little buffer
        return 0

    def send_raw(self, string):
        """Send raw string to the server.

        The string will be padded with appropriate CR LF.
        If too many messages are sent, this will call
        :func:`time.sleep` until it is allowed to send messages again.

        :param string: the raw string to send
        :type string: :class:`str`
        :returns: None
        :raises: :class:`irc.client.InvalidCharacters`,
                 :class:`irc.client.MessageTooLong`,
                 :class:`irc.client.ServerNotConnectedError`
        """
        waittime = self.get_waittime()
        if waittime:
            log.debug('Sent too many messages. Waiting %s seconds',
                      waittime)
            time.sleep(waittime)
        return super(ServerConnection3, self).send_raw(string)

    def _process_line(self, line):
        """Process the given line and handle the events

        :param line: the raw message
        :type line: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        m = self._rfc_1459_command_regexp.match(line)
        prefix = m.group('prefix')
        tags = self._process_tags(m.group('tags'))
        source = self._process_prefix(prefix)
        command = self._process_command(m.group('command'))
        arguments = self._process_arguments(m.group('argument'))
        if not self.real_server_name:
            self.real_server_name = prefix

        # Translate numerics into more readable strings.
        command = irc.events.numeric.get(command, command)
        if command not in ["privmsg", "notice"]:
            return super(ServerConnection3, self)._process_line(line)

        event = Event3("all_raw_messages", self.get_server_name(),
                       None, [line], tags=tags)
        self._handle_event(event)

        target, msg = arguments[0], arguments[1]
        messages = irc.ctcp.dequote(msg)
        command = self._resolve_command(command, target)
        for m in messages:
            self._handle_message(tags, source, command, target, m)

    def _resolve_command(self, command, target):
        """Get the correct event for the command

        Only for 'privmsg' and 'notice' commands.

        :param command: The command string
        :type command: :class:`str`
        :param target: either a user or a channel
        :type target: :class:`str`
        :returns: the correct event type
        :rtype: :class:`str`
        :raises: None
        """
        if command == "privmsg":
            if irc.client.is_channel(target):
                command = "pubmsg"
        else:
            if irc.client.is_channel(target):
                command = "pubnotice"
            else:
                command = "privnotice"
        return command

    def _handle_message(self, tags, source, command, target, msg):
        """Construct the correct events and handle them

        :param tags: the tags of the message
        :type tags: :class:`list` of :class:`message.Tag`
        :param source: the sender of the message
        :type source: :class:`str`
        :param command: the event type
        :type command: :class:`str`
        :param target: the target of the message
        :type target: :class:`str`
        :param msg: the content
        :type msg: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        if isinstance(msg, tuple):
            if command in ["privmsg", "pubmsg"]:
                command = "ctcp"
            else:
                command = "ctcpreply"

            msg = list(msg)
            log.debug("tags: %s, command: %s, source: %s, target: %s, "
                      "arguments: %s", tags, command, source, target, msg)
            event = Event3(command, source, target, msg, tags=tags)
            self._handle_event(event)
            if command == "ctcp" and msg[0] == "ACTION":
                event = Event3("action", source, target, msg[1:], tags=tags)
                self._handle_event(event)
        else:
            log.debug("tags: %s, command: %s, source: %s, target: %s, "
                      "arguments: %s", tags, command, source, target, [msg])
            event = Event3(command, source, target, [msg], tags=tags)
            self._handle_event(event)

    def _process_tags(self, tags):
        """Process the tags of the message

        :param tags: the tags string of a message
        :type tags: :class:`str` | None
        :returns: list of tags
        :rtype: :class:`list` of :class:`message.Tag`
        :raises: None
        """
        if not tags:
            return []
        return [message.Tag.from_str(x) for x in tags.split(';')]

    def _process_prefix(self, prefix):
        """Process the prefix of the message and return the source

        :param prefix: The prefix string of a message
        :type prefix: :class:`str` | None
        :returns: The prefix wrapped in :class:`irc.client.NickMask`
        :rtype: :class:`irc.client.NickMask` | None
        :raises: None
        """
        if not prefix:
            return None

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
