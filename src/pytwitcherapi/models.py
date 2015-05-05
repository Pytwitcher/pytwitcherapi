"""Contains classes that wrap the jsons returned by the twitch.tv API"""

__all__ = ['Game', 'Channel', 'Stream', 'User']


class Game(object):
    """Game on twitch.tv
    """

    @classmethod
    def wrap_search(cls, response):
        """Wrap the response from a game search into instances
        and return them

        :param response: The response from searching a game
        :type response: :class:`requests.Response`
        :returns: the new game instances
        :rtype: :class:`list` of :class:`Game`
        :raises: None
        """
        games = []
        json = response.json()
        gamejsons = json['games']
        for j in gamejsons:
            g = cls.wrap_json(j)
            games.append(g)
        return games

    @classmethod
    def wrap_topgames(cls, response):
        """Wrap the response from quering the top games into instances
        and return them

        :param response: The response for quering the top games
        :type response: :class:`requests.Response`
        :returns: the new game instances
        :rtype: :class:`list` of :class:`Game`
        :raises: None
        """
        games = []
        json = response.json()
        topjsons = json['top']
        for t in topjsons:
            g = cls.wrap_json(json=t['game'],
                              viewers=t['viewers'],
                              channels=t['channels'])
            games.append(g)
        return games

    @classmethod
    def wrap_json(cls, json, viewers=None, channels=None):
        """Create a Game instance for the given json

        :param json: the dict with the information of the game
        :type json: :class:`dict`
        :param viewers: The viewer count
        :type viewers: :class:`int`
        :param channels: The viewer count
        :type channels: :class:`int`
        :returns: the new game instance
        :rtype: :class:`Game`
        :raises: None
        """
        g = Game(name=json.get('name'),
                 box=json.get('box'),
                 logo=json.get('logo'),
                 twitchid=json.get('_id'),
                 viewers=viewers,
                 channels=channels)
        return g

    def __init__(self, name, box, logo, twitchid, viewers=None, channels=None):
        """Initialize a new game

        :param name: The name of the game
        :type name: :class:`str`
        :param box: Links for the box logos
        :type box: :class:`dict`
        :param logo: Links for the game logo
        :type logo: :class:`dict`
        :param twitchid: The id used by twitch
        :type twitchid: :class:`int`
        :param viewers: The current amount of viewers
        :type viewers: :class:`int`
        :param channels: The current amount of channels
        :type channels: :class:`int`
        :raises: None
        """
        self.name = name
        """The name of the game"""
        self.box = box
        """Links for the box logos"""
        self.logo = logo
        """Links for the logos"""
        self.twitchid = twitchid
        """Id used by twitch"""
        self.viewers = viewers
        """Current amount of viewers"""
        self.channels = channels
        """Current amount of channels"""

    def __repr__(self, ):
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s, id: %s>' % (self.__class__.__name__,
                                    self.name,
                                    self.twitchid)


class Channel(object):
    """Channel on twitch.tv
    """

    @classmethod
    def wrap_search(cls, response):
        """Wrap the response from a channel search into instances
        and return them

        :param response: The response from searching a channel
        :type response: :class:`requests.Response`
        :returns: the new channel instances
        :rtype: :class:`list` of :class:`channel`
        :raises: None
        """
        channels = []
        json = response.json()
        channeljsons = json['channels']
        for j in channeljsons:
            c = cls.wrap_json(j)
            channels.append(c)
        return channels

    @classmethod
    def wrap_get_channel(cls, response):
        """Wrap the response from getting a channel into an instance
        and return it

        :param response: The response from getting a channel
        :type response: :class:`requests.Response`
        :returns: the new channel instance
        :rtype: :class:`list` of :class:`channel`
        :raises: None
        """
        json = response.json()
        c = cls.wrap_json(json)
        return c

    @classmethod
    def wrap_json(cls, json):
        """Create a Channel instance for the given json

        :param json: the dict with the information of the channel
        :type json: :class:`dict`
        :returns: the new channel instance
        :rtype: :class:`Channel`
        :raises: None
        """
        c = Channel(name=json.get('name'),
                    status=json.get('status'),
                    displayname=json.get('display_name'),
                    game=json.get('game'),
                    twitchid=json.get('_id'),
                    views=json.get('views'),
                    followers=json.get('followers'),
                    url=json.get('url'),
                    language=json.get('language'),
                    broadcaster_language=json.get('broadcaster_language'),
                    mature=json.get('mature'),
                    logo=json.get('logo'),
                    banner=json.get('banner'),
                    video_banner=json.get('video_banner'),
                    delay=json.get('delay'))
        return c

    def __init__(self, name, status, displayname, game, twitchid, views,
                 followers, url, language, broadcaster_language, mature,
                 logo, banner, video_banner, delay):
        """Initialize a new channel

        :param name: The name of the channel
        :type name: :class:`str`
        :param status: The status
        :type status: :class:`str`
        :param displayname: The name displayed by the interface
        :type displayname: :class:`str`
        :param game: the game of the channel
        :type game: :class:`str`
        :param twitchid: the internal twitch id
        :type twitchid: :class:`int`
        :param views: the overall views
        :type views: :class:`int`
        :param followers: the follower count
        :type followers: :class:`int`
        :param url: the url to the channel
        :type url: :class:`str`
        :param language: the language of the channel
        :type language: :class:`str`
        :param broadcaster_language: the language of the broadcaster
        :type broadcaster_language: :class:`str`
        :param mature: If true, the channel is only for mature audiences
        :type mature: :class:`bool`
        :param logo: the link to the logos
        :type logo: :class:`str`
        :param banner: the link to the banner
        :type banner: :class:`str`
        :param video_banner: the link to the video banner
        :type video_banner: :class:`str`
        :param delay: stream delay
        :type delay: :class:`int`
        :raises: None
        """
        self.name = name
        """The name of the channel"""
        self.status = status
        """The current status message"""
        self.displayname = displayname
        """The name displayed by the interface"""
        self.game = game
        """The game of the channel"""
        self.twitchid = twitchid
        """THe internal twitch id"""
        self.views = views
        """The overall views"""
        self.followers = followers
        """The follower count"""
        self.url = url
        """the link to the channel page"""
        self.language = language
        """Language of the channel"""
        self.broadcaster_language = broadcaster_language
        """Language of the broadcaster"""
        self.mature = mature
        """If true, the channel is only for mature audiences"""
        self.logo = logo
        """the link to the logo"""
        self.banner = banner
        """the link to the banner"""
        self.video_banner = video_banner
        """the link to the video banner"""
        self.delay = delay
        """stream delay"""

    def __repr__(self, ):
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s, id: %s>' % (self.__class__.__name__,
                                    self.name,
                                    self.twitchid)


class Stream(object):
    """A stream on twitch.tv
    """

    @classmethod
    def wrap_search(cls, response):
        """Wrap the response from a stream search into instances
        and return them

        :param response: The response from searching a stream
        :type response: :class:`requests.Response`
        :returns: the new stream instances
        :rtype: :class:`list` of :class:`stream`
        :raises: None
        """
        streams = []
        json = response.json()
        streamjsons = json['streams']
        for j in streamjsons:
            s = cls.wrap_json(j)
            streams.append(s)
        return streams

    @classmethod
    def wrap_get_stream(cls, response):
        """Wrap the response from getting a stream into an instance
        and return it

        :param response: The response from getting a stream
        :type response: :class:`requests.Response`
        :returns: the new stream instance
        :rtype: :class:`list` of :class:`stream`
        :raises: None
        """
        json = response.json()
        s = cls.wrap_json(json['stream'])
        return s

    @classmethod
    def wrap_json(cls, json):
        """Create a Stream instance for the given json

        :param json: the dict with the information of the stream
        :type json: :class:`dict` | None
        :returns: the new stream instance
        :rtype: :class:`Stream` | None
        :raises: None
        """
        if json is None:
            return None
        channel = Channel.wrap_json(json.get('channel'))
        s = Stream(game=json.get('game'),
                   channel=channel,
                   twitchid=json.get('_id'),
                   viewers=json.get('viewers'),
                   preview=json.get('preview'))
        return s

    def __init__(self, game, channel, twitchid, viewers, preview):
        """Initialize a new stream

        :param game: name of the game
        :type game: :class:`str`
        :param channel: the channel that is streaming
        :type channel: :class:`Channel`
        :param twitchid: the internal twitch id
        :type twitchid: :class:`int`
        :param viewers: the viewer count
        :type viewers: :class:`int`
        :param preview: a dict with preview picture links of the stream
        :type preview: :class:`dict`
        :raises: None
        """
        self.game = game
        """Name of the game that is beeing streamed"""
        self.channel = channel
        """The channel instance"""
        self.twitchid = twitchid
        """The internal twitch id"""
        self.viewers = viewers
        """the viewer count"""
        self.preview = preview
        """A dict with preview picture links of the stream"""

    def __repr__(self, ):
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s, id: %s>' % (self.__class__.__name__,
                                    self.channel.name,
                                    self.twitchid)


class User(object):
    """A user on twitch.tv
    """

    @classmethod
    def wrap_get_user(cls, response):
        """Wrap the response from getting a user into an instance
        and return it

        :param response: The response from getting a user
        :type response: :class:`requests.Response`
        :returns: the new user instance
        :rtype: :class:`list` of :class:`User`
        :raises: None
        """
        json = response.json()
        u = cls.wrap_json(json)
        return u

    @classmethod
    def wrap_json(cls, json):
        """Create a User instance for the given json

        :param json: the dict with the information of the user
        :type json: :class:`dict` | None
        :returns: the new user instance
        :rtype: :class:`User`
        :raises: None
        """
        u = User(usertype=json['type'],
                 name=json['name'],
                 logo=json['logo'],
                 twitchid=json['_id'],
                 displayname=json['display_name'],
                 bio=json['bio'])
        return u

    def __init__(self, usertype, name, logo, twitchid, displayname, bio):
        """Initialize a new user

        :param usertype: the user type on twitch, e.g. ``"user"``
        :type usertype: :class:`str`
        :param name: the username
        :type name: :class:`str`
        :param logo: the link to the logo
        :type logo: :class:`str`
        :param twitchid: the internal twitch id
        :type twitchid: :class:`int`
        :param displayname: the name diplayed by the interface
        :type displayname: :class:`str`
        :param bio: the user bio
        :type bio: :class:`str`
        :raises: None
        """
        self.usertype = usertype
        """the user type on twitch, e.g. ``"user"``"""
        self.name = name
        """the username"""
        self.logo = logo
        """link to the logo"""
        self.twitchid = twitchid
        """internal twitch id"""
        self.displayname = displayname
        """name displayed by the interface"""
        self.bio = bio
        """the user bio"""

    def __repr__(self, ):
        """Return the canonical string representation of the object

        :returns: string representation
        :rtype: :class:`str`
        :raises: None
        """
        return '<%s %s, id: %s>' % (self.__class__.__name__,
                                    self.name,
                                    self.twitchid)
