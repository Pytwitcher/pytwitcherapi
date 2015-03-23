"""API for communicating with twitch"""
import contextlib

import m3u8
import requests
import requests.utils

from pytwitcherapi import models

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
        :rtype: :class:`models.Game`
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
        :rtype: :class:`list` of :class:`models.Game` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/games',
                         params={'query': query,
                                 'type': 'suggest',
                                 'live': live})
        games = models.Game.wrap_search(r)
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
        :rtype: :class:`list` of :class:`models.Game`
        :raises: None
        """
        with kraken(self):
            r = self.get('games/top',
                         params={'limit': limit,
                                 'offset': offset})
        return models.Game.wrap_topgames(r)

    def get_game(self, name):
        """Get the game instance for a game name

        :param name: the name of the game
        :type name: :class:`str`
        :returns: the game instance
        :rtype: :class:`models.Game` | None
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
        :returns: :class:`models.Channel`
        :rtype: None
        :raises: None
        """
        with kraken(self):
            r = self.get('channels/' + name)
        return models.Channel.wrap_get_channel(r)

    def search_channels(self, query, limit=25, offset=0):
        """Search for channels and return them

        :param query: the query string
        :type query: :class:`str`
        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of channels
        :rtype: :class:`list` of :class:`models.Channel` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/channels',
                         params={'query': query,
                                 'limit': limit,
                                 'offset': offset})
        return models.Channel.wrap_search(r)

    def get_stream(self, channel):
        """Return the stream of the given channel

        :param channel: the channel that is broadcasting.
                        Either name or models.Channel instance
        :type channel: :class:`str` | :class:`models.Channel`
        :returns: the stream or None, if the channel is offline
        :rtype: :class:`models.Stream` | None
        :raises: None
        """
        if isinstance(channel, models.Channel):
            channel = channel.name

        with kraken(self):
            r = self.get('streams/' + channel)
        return models.Stream.wrap_get_stream(r)

    def get_streams(self, game=None, channels=None, limit=25, offset=0):
        """Return a list of streams queried by a number of parameters
        sorted by number of viewers descending

        :param game: the game or name of the game
        :type game: :class:`str` | :class:`models.Game`
        :param channels: list of models.Channels or channel names (can be mixed)
        :type channels: :class:`list` of :class:`models.Channel` or :class:`str`
        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of streams
        :rtype: :class:`list` of :class:`models.Stream`
        :raises: None
        """
        if isinstance(game, models.Game):
            game = game.name

        cs = []
        cparam = None
        if channels:
            for c in channels:
                if isinstance(c, models.Channel):
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
        return models.Stream.wrap_search(r)

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
        :rtype: :class:`list` of :class:`models.Stream` instances
        :raises: None
        """
        with kraken(self):
            r = self.get('search/streams',
                         params={'query': query,
                                 'hls': hls,
                                 'limit': limit,
                                 'offset': offset})
        return models.Stream.wrap_search(r)

    def get_user(self, name):
        """Get the user for the given name

        :param name: The username
        :type name: :class:`str`
        :returns: the user instance
        :rtype: :class:`models.User`
        :raises: None
        """
        with kraken(self):
            r = self.get('user/' + name)
        return models.User.wrap_get_user(r)

    def get_playlist(self, channel):
        """Return the playlist for the given channel

        :param channel: the channel
        :type channel: :class:`models.Channel` | :class:`str`
        :returns: the playlist
        :rtype: :class:`m3u8.M3U8`
        :raises: :class:`requests.HTTPError` if channel is offline.
        """
        if isinstance(channel, models.Channel):
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
        :type channel: :class:`models.Channel` | :class:`str`
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
        if isinstance(channel, models.Channel):
            channel = channel.name
        with oldapi(self):
            r = self.get('channels/%s/access_token' % channel).json()
        return r['token'], r['sig']
