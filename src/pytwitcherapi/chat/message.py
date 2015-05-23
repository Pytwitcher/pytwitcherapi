import re

import irc.client


__all__ = ['Tag', 'Emote', 'Chatter', 'Message3']


class Tag(object):
    """An irc v3 tag

    `Specification <http://ircv3.net/specs/core/message-tags-3.2.html>`_ for tags.
    A tag will associate metadata with a message.

    To get tags in twitch chat, you have to specify it in the
    `capability negotiation<http://ircv3.net/specs/core/capability-negotiation-3.1.html>`_.
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

    You can get the pictures here::

        ``cdn.jtvnw.net/emoticons/v1/<emoteid>/1.0``

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

    def __repr__(self, ):  # pragma: no cover
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
        """the hex representation of the user color"""
        self._emotes = []
        """list of emotes"""
        self._subscriber = False
        """True, if the user is a subscriber"""
        self._turbo = False
        """True, if the user is a turbo user"""
        self.user_type = None
        """Turbo type. None for regular ones.
        Other user types are mod, global_mod, staff, admin.
        """
        self.set_tags(tags)

    @classmethod
    def from_event(cls, event):
        """Create a message from an event

        :param event: the event that was received of type ``pubmsg`` or ``privmsg``
        :type event: :class:`Event3`
        :returns: a message that resembles the event
        :rtype: :class:`Message3`
        :raises: None
        """
        source = Chatter(event.source)
        return cls(source, event.target, event.arguments[0], event.tags)

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
        if emotes is None:
            self._emotes = []
            return
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
