"""IRC client for interacting with the chat of a channel."""


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

    def __repr__(self):
        return "<%s %s, %s, %s, %s>" % (self.__class__.__name__, self.address,
                                        self.status, self.errors, self.lag)

    def __eq__(self, other):
        """Servers are equal if the address is equal.

        :param other: either an other server status or an adress
        :type other: :class:`ChatServerStatus` | :class:`str`
        :returns: True, if equal
        :rtype: :class:`bool`
        """
        if isinstance(other, basestring):
            return self.address == other
        if isinstance(other, ChatServerStatus):
            return self.address == other.address
        return self is other

    def __lt__(self, other):
        """Return whether a server status is lesser than the other.

        A server status is lesser when:

          1. it's offline but the other isn't.
          2. It has more errors.
          2. It has more lags.

        :param other: the other server status to compare
        :type other: :class:`ChatServerStatus`
        :returns: True, if lesser than other
        :rtype: :class:`bool`
        """
        if self.status != other.status:
            return self.status == 'online'
        if self.errors == other.errors:
            return self.lag < other.lag
        return self.errors < other.errors
