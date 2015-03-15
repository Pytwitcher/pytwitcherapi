"""API for communicating with twitch"""
import contextlib

import m3u8
import requests
import requests.utils

TWITCH_KRAKENURL = 'https://api.twitch.tv/kraken/'
"""The baseurl for the twitch api"""

TWITCH_HEADER_ACCEPT = 'application/vnd.twitchtv.v3+json'
"""The header for the ``Accept`` key to tell twitch which api version it should use"""

TWITCH_USHERURL = 'http://usher.twitch.tv/api/'
"""The baseurl for the twitch usher api"""

TWITCH_APIURL = 'http://api.twitch.tv/api/'
"""The baseurl for the old twitch api"""

CLIENT_ID = '642a2vtmqfumca8hmfcpkosxlkmqifb'
"""The client id of pytwitcher on twitch."""


@contextlib.contextmanager
def kraken(session):
    """Contextmanager for a :class:`TwitchSession` to make
    shorter requests to the Kraken API.

    Sets the baseurl of the session to :data:`TWITCH_KRAKENURL`
    and ``Accept`` in headers to :data:`TWITCH_HEADER_ACCEPT`.

    :param session: the session to make use the Kraken API
    :type session: :class:`TwitchSession`
    :returns: None
    :rtype: None
    :raises: None
    """
    oldheaders = session.headers
    oldbaseurl = session.baseurl
    try:
        session.headers = requests.utils.default_headers()
        session.headers['Accept'] = TWITCH_HEADER_ACCEPT
        session.baseurl = TWITCH_KRAKENURL
        yield
    finally:
        session.headers = oldheaders
        session.baseurl = oldbaseurl


@contextlib.contextmanager
def usher(session):
    """Contextmanager for a :class:`TwitchSession` to make
    shorter requests to the Usher API.

    Sets the baseurl of the session to :data:`TWITCH_USHERURL`
    and uses default headers.

    :param session: the session to make use the Usher API
    :type session: :class:`TwitchSession`
    :returns: None
    :rtype: None
    :raises: None
    """
    oldheaders = session.headers
    oldbaseurl = session.baseurl
    try:
        session.headers = requests.utils.default_headers()
        session.baseurl = TWITCH_USHERURL
        yield
    finally:
        session.headers = oldheaders
        session.baseurl = oldbaseurl


@contextlib.contextmanager
def oldapi(session):
    """Contextmanager for a :class:`TwitchSession` to make
    shorter requests to the old twitch API.

    Sets the baseurl of the session to :data:`TWITCH_APIURL`
    and uses default headers.

    :param session: the session to make use the old API
    :type session: :class:`TwitchSession`
    :returns: None
    :rtype: None
    :raises: None
    """
    oldheaders = session.headers
    oldbaseurl = session.baseurl
    try:
        session.headers = requests.utils.default_headers()
        session.baseurl = TWITCH_APIURL
        yield
    finally:
        session.headers = oldheaders
        session.baseurl = oldbaseurl


class TwitchSession(requests.Session):
    """Session that stores a baseurl that will be prepended for every request

    You can use the contextmanagers :func:`kraken`, :func:`usher` and
    :func:`oldapi` to easily use the different APIs.
    They will set the baseurl and headers.
    """

    def __init__(self):
        """Initialize a new TwitchSession

        :raises: None
        """
        super(TwitchSession, self).__init__()
        self.baseurl = ''
        """The baseurl that gets prepended to every request url"""

    def request(self, method, url, **kwargs):
        """Constructs a :class:`requests.Request`, prepares it and sends it.
        Raises HTTPErrors by default.

        :param method: method for the new :class:`Request` object.
        :type method: :class:`str`
        :param url: URL for the new :class:`Request` object.
        :type url: :class:`str`
        :param kwargs: keyword arguments of :meth:`requests.Session.request`
        :returns: a resonse object
        :rtype: :class:`requests.Response`
        :raises: :class:`requests.HTTPError`
        """
        fullurl = self.baseurl + url if self.baseurl else url
        r = super(TwitchSession, self).request(method, fullurl, **kwargs)
        r.raise_for_status()
        return r

    def fetch_viewers(self, game):
        """Query the viewers and channels of the given game and
        set them on the object

        :returns: the given game
        :rtype: :class:`Game`
        :raises: None
        """
        with kraken(self):
            r = self.get('streams/summary', params={'game': game.name}).json()
        game.viewers = r['viewers']
        game.channels = r['channels']
        return game

    def search_games(self, query, live=True):
        """Search for games that are similar to the query

        :param query: the query string
        :type query: :class:`str`
        :param live: If true, only returns games that are live on at least one
                     channel
        :type live: :class:`bool`
        :returns: A list of games
        :rtype: :class:`list` of :class:`Game` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/games',
                         params={'query': query,
                                 'type': 'suggest',
                                 'live': live})
        games = Game.wrap_search(r)
        for g in games:
            self.fetch_viewers(g)
        return games

    def top_games(self, limit=10, offset=0):
        """Return the current top games

        :param limit: the maximum amount of top games to query
        :type limit: :class:`int`
        :param offset: the offset in the top games
        :type offset: :class:`int`
        :returns: a list of top games
        :rtype: :class:`list` of :class:`Game`
        :raises: None
        """
        with kraken(self):
            r = self.get('games/top',
                         params={'limit': limit,
                                 'offset': offset})
        return Game.wrap_topgames(r)

    def get_game(self, name):
        """Get the game instance for a game name

        :param name: the name of the game
        :type name: :class:`str`
        :returns: the game instance
        :rtype: :class:`Game` | None
        :raises: None
        """
        games = self.search_games(query=name, live=False)
        for g in games:
            if g.name == name:
                return g

    def get_channel(self, name):
        """Return the channel for the given name

        :param name: the channel name
        :type name: :class:`str`
        :returns: :class:`Channel`
        :rtype: None
        :raises: None
        """
        with kraken(self):
            r = self.get('channels/' + name)
        return Channel.wrap_get_channel(r)

    def search_channels(self, query, limit=25, offset=0):
        """Search for channels and return them

        :param query: the query string
        :type query: :class:`str`
        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of channels
        :rtype: :class:`list` of :class:`Channel` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/channels',
                         params={'query': query,
                                 'limit': limit,
                                 'offset': offset})
        return Channel.wrap_search(r)

    def get_stream(self, channel):
        """Return the stream of the given channel

        :param channel: the channel that is broadcasting.
                        Either name or Channel instance
        :type channel: :class:`str` | :class:`Channel`
        :returns: the stream or None, if the channel is offline
        :rtype: :class:`Stream` | None
        :raises: None
        """
        if isinstance(channel, Channel):
            channel = channel.name

        with kraken(self):
            r = self.get('streams/' + channel)
        return Stream.wrap_get_stream(r)

    def get_streams(self, game=None, channels=None, limit=25, offset=0):
        """Return a list of streams queried by a number of parameters
        sorted by number of viewers descending

        :param game: the game or name of the game
        :type game: :class:`str` | :class:`Game`
        :param channels: list of Channels or channel names (can be mixed)
        :type channels: :class:`list` of :class:`Channel` or :class:`str`
        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of streams
        :rtype: :class:`list` of :class:`Stream`
        :raises: None
        """
        if isinstance(game, Game):
            game = game.name

        cs = []
        cparam = None
        if channels:
            for c in channels:
                if isinstance(c, Channel):
                    c = c.name
                cs.append(c)
            cparam = ','.join(cs)

        params = {'limit': limit,
                  'offset': offset}
        if game:
            params['game'] = game
        if cparam:
            params['channel'] = cparam

        with kraken(self):
            r = self.get('streams', params=params)
        return Stream.wrap_search(r)

    def search_streams(self, query, hls=False, limit=25, offset=0):
        """Search for streams and return them

        :param query: the query string
        :type query: :class:`str`
        :param hls: If true, only return streams that have hls stream
        :type hls: :class:`bool`
        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of streams
        :rtype: :class:`list` of :class:`Stream` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/streams',
                         params={'query': query,
                                 'hls': hls,
                                 'limit': limit,
                                 'offset': offset})
        return Stream.wrap_search(r)

    def get_user(self, name):
        """Get the user for the given name

        :param name: The username
        :type name: :class:`str`
        :returns: the user instance
        :rtype: :class:`User`
        :raises: None
        """
        with kraken(self):
            r = self.get('user/' + name)
        return User.wrap_get_user(r)

    def get_playlist(self, channel):
        """Return the playlist for the given channel

        :param channel: the channel
        :type channel: :class:`Channel` | :class:`str`
        :returns: the playlist
        :rtype: :class:`m3u8.M3U8`
        :raises: :class:`requests.HTTPError` if channel is offline.
        """
        if isinstance(channel, Channel):
            channel = channel.name

        token, sig = self.get_channel_access_token(channel)
        params = {'token': token, 'sig': sig,
                  'allow_audio_only': True,
                  'allow_source_only': True}
        with usher(self):
            r = self.get('channel/hls/%s.m3u8' % channel, params=params)
        playlist = m3u8.loads(r.text)
        return playlist

    def get_quality_options(self, channel):
        """Get the available quality options for streams of the given channel

        Possible values in the list:

          * source
          * high
          * medium
          * low
          * mobile
          * audio

        :param channel: the channel or channel name
        :type channel: :class:`Channel` | :class:`str`
        :returns: list of quality options
        :rtype: :class:`list` of :class:`str`
        :raises: :class:`requests.HTTPError` if channel is offline.
        """
        optionmap = {'chunked': 'source',
                     'high': 'high',
                     'medium': 'medium',
                     'low': 'low',
                     'mobile': 'mobile',
                     'audio_only': 'audio'}
        p = self.get_playlist(channel)
        options = []
        for pl in p.playlists:
            q = pl.media[0].group_id
            options.append(optionmap[q])
        return options

    def get_channel_access_token(self, channel):
        """Return the token and sig for the given channel

        :param channel: the channel or channel name to get the access token for
        :type channel: :class:`channel` | :class:`str`
        :returns: The token and sig for the given channel
        :rtype: (:class:`unicode`, :class:`unicode`)
        :raises: None
        """
        if isinstance(channel, Channel):
            channel = channel.name
        with oldapi(self):
            r = self.get('channels/%s/access_token' % channel).json()
        return r['token'], r['sig']


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
        g = cls(name=json['name'],
                box=json['box'],
                logo=json['logo'],
                twitchid=json['_id'],
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
        c = cls(name=json['name'],
                status=json['status'],
                displayname=json['display_name'],
                game=json['game'],
                twitchid=json['_id'],
                views=json['views'],
                followers=json['followers'],
                url=json['url'],
                language=json['language'],
                broadcaster_language=json['broadcaster_language'],
                mature=json['mature'],
                logo=json['logo'],
                banner=json['banner'],
                video_banner=json['video_banner'],
                delay=json['delay'])
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
        :type video_banner::class:`str`
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
        channel = Channel.wrap_json(json['channel'])
        s = cls(game=json['game'],
                channel=channel,
                twitchid=json['_id'],
                viewers=json['viewers'],
                preview=json['preview'])
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
        :rtype: :class:`list` of :class:`user`
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
        u = cls(usertype=json['type'],
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
