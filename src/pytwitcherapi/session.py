"""API for communicating with twitch"""
from __future__ import absolute_import

import functools
import logging
import threading

import m3u8
import oauthlib.oauth2
import requests
import requests.utils
import requests_oauthlib

from pytwitcherapi.chat import client

from . import constants, exceptions, models, oauth

__all__ = ['needs_auth', 'TwitchSession']

log = logging.getLogger(__name__)

TWITCH_KRAKENURL = 'https://api.twitch.tv/kraken/'
"""The baseurl for the twitch api"""

TWITCH_HEADER_ACCEPT = 'application/vnd.twitchtv.v3+json'
"""The header for the ``Accept`` key to tell twitch which api version it should use"""

TWITCH_USHERURL = 'http://usher.twitch.tv/api/'
"""The baseurl for the twitch usher api"""

TWITCH_APIURL = 'http://api.twitch.tv/api/'
"""The baseurl for the old twitch api"""

TWITCH_STATUSURL = 'http://twitchstatus.com/api/status?type=chat'

AUTHORIZATION_BASE_URL = 'https://api.twitch.tv/kraken/oauth2/authorize'
"""Authorisation Endpoint"""

CLIENT_ID = '642a2vtmqfumca8hmfcpkosxlkmqifb'
"""The client id of pytwitcher on twitch."""

SCOPES = ['user_read', 'chat_login']
"""The scopes that PyTwitcher needs"""


def needs_auth(meth):
    """Wraps a method of :class:`TwitchSession` and
    raises an :class:`exceptions.NotAuthorizedError`
    if before calling the method, the session isn't authorized.

    :param meth:
    :type meth:
    :returns: the wrapped method
    :rtype: Method
    :raises: None
    """
    @functools.wraps(meth)
    def wrapped(*args, **kwargs):
        if not args[0].authorized:
            raise exceptions.NotAuthorizedError('Please login first!')
        return meth(*args, **kwargs)
    return wrapped


class OAuthSession(requests_oauthlib.OAuth2Session):
    """Session with oauth2 support.

    You can still use http requests.
    """

    def __init__(self):
        """Initialize a new oauth session

        :raises: None
        """
        client = oauth.TwitchOAuthClient(client_id=CLIENT_ID)
        super(OAuthSession, self).__init__(client_id=CLIENT_ID,
                                           client=client,
                                           scope=SCOPES,
                                           redirect_uri=constants.REDIRECT_URI)
        self.login_server = None
        """The server that handles the login redirect"""
        self.login_thread = None
        """The thread that serves the login server"""

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
        if oauthlib.oauth2.is_secure_transport(url):
            m = super(OAuthSession, self).request
        else:
            m = super(requests_oauthlib.OAuth2Session, self).request
        log.debug("%s \"%s\" with %s", method, url, kwargs)
        response = m(method, url, **kwargs)
        response.raise_for_status()
        return response

    def start_login_server(self, ):
        """Start a server that will get a request from a user logging in.

        This uses the Implicit Grant Flow of OAuth2. The user is asked
        to login to twitch and grant PyTwitcher authorization.
        Once the user agrees, he is redirected to an url.
        This server will respond to that url and get the oauth token.

        The server serves in another thread. To shut him down, call
        :meth:`TwitchSession.shutdown_login_server`.

        This sets the :data:`TwitchSession.login_server`,
        :data:`TwitchSession.login_thread` variables.

        :returns: The created server
        :rtype: :class:`BaseHTTPServer.HTTPServer`
        :raises: None
        """
        self.login_server = oauth.LoginServer(session=self)
        target = self.login_server.serve_forever
        self.login_thread = threading.Thread(target=target)
        self.login_thread.setDaemon(True)
        log.debug('Starting login server thread.')
        self.login_thread.start()

    def shutdown_login_server(self, ):
        """Shutdown the login server and thread

        :returns: None
        :rtype: None
        :raises: None
        """
        log.debug('Shutting down the login server thread.')
        self.login_server.shutdown()
        self.login_server.server_close()
        self.login_thread.join()

    def get_auth_url(self, ):
        """Return the url for the user to authorize PyTwitcher

        :returns: The url the user should visit to authorize PyTwitcher
        :rtype: :class:`str`
        :raises: None
        """
        return self.authorization_url(AUTHORIZATION_BASE_URL)[0]


class TwitchSession(OAuthSession):
    """Session for making requests to the twitch api

    Use :meth:`TwitchSession.kraken_request`,
    :meth:`TwitchSession.usher_request`,
    :meth:`TwitchSession.oldapi_request` to make easier calls to the api
    directly.

    To get authorization, the user has to grant PyTwitcher access.
    The workflow goes like this:

      1. Start the login server with :meth:`TwitchSession.start_login_server`.
      2. User should visit :meth:`TwitchSession.get_auth_url` in his
         browser and follow insturctions (e.g Login and Allow PyTwitcher).
      3. Check if the session is authorized with :meth:`TwitchSession.authorized`.
      4. Shut the login server down with :meth:`TwitchSession.shutdown_login_server`.

    Now you can use methods that need authorization.
    """

    def __init__(self):
        """Initialize a new TwitchSession

        :raises: None
        """
        super(TwitchSession, self).__init__()
        self.baseurl = ''
        """The baseurl that gets prepended to every request url"""
        self.current_user = None
        """The currently logined user."""
        self._token = None
        """The oauth token"""

    @property
    def token(self, ):
        """Return the oauth token

        :returns: the token
        :rtype: :class:`dict`
        :raises: None
        """
        return self._token

    @token.setter
    def token(self, token):
        """Set the oauth token and the current_user

        :param token: the oauth token
        :type token: :class:`dict`
        :returns: None
        :rtype: None
        :raises: None
        """
        self._token = token
        if token:
            self.current_user = self.query_login_user()

    def kraken_request(self, method, endpoint, **kwargs):
        """Make a request to one of the kraken api endpoints.

        Headers are automatically set to accept :data:`TWITCH_HEADER_ACCEPT`.
        The url will be constructed of :data:`TWITCH_KRAKENURL` and
        the given endpoint.

        :param method: the request method
        :type method: :class:`str`
        :param endpoint: the endpoint of the kraken api.
                         The base url is automatically provided.
        :type endpoint: :class:`str`
        :param kwargs: keyword arguments of :meth:`requests.Session.request`
        :returns: a resonse object
        :rtype: :class:`requests.Response`
        :raises: :class:`requests.HTTPError`
        """
        url = TWITCH_KRAKENURL + endpoint
        headers = kwargs.setdefault('headers', {})
        headers['Accept'] = TWITCH_HEADER_ACCEPT
        return self.request(method, url, **kwargs)

    def usher_request(self, method, endpoint, **kwargs):
        """Make a request to one of the usher api endpoints.

        The url will be constructed of :data:`TWITCH_USHERURL` and
        the given endpoint.

        :param method: the request method
        :type method: :class:`str`
        :param endpoint: the endpoint of the usher api.
                         The base url is automatically provided.
        :type endpoint: :class:`str`
        :param kwargs: keyword arguments of :meth:`requests.Session.request`
        :returns: a resonse object
        :rtype: :class:`requests.Response`
        :raises: :class:`requests.HTTPError`
        """
        url = TWITCH_USHERURL + endpoint
        return self.request(method, url, **kwargs)

    def oldapi_request(self, method, endpoint, **kwargs):
        """Make a request to one of the old api endpoints.

        The url will be constructed of :data:`TWITCH_APIURL` and
        the given endpoint.

        :param method: the request method
        :type method: :class:`str`
        :param endpoint: the endpoint of the old api.
                         The base url is automatically provided.
        :type endpoint: :class:`str`
        :param kwargs: keyword arguments of :meth:`requests.Session.request`
        :returns: a resonse object
        :rtype: :class:`requests.Response`
        :raises: :class:`requests.HTTPError`
        """
        url = TWITCH_APIURL + endpoint
        return self.request(method, url, **kwargs)

    def fetch_viewers(self, game):
        """Query the viewers and channels of the given game and
        set them on the object

        :returns: the given game
        :rtype: :class:`models.Game`
        :raises: None
        """
        r = self.kraken_request('GET', 'streams/summary',
                                params={'game': game.name}).json()
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
        r = self.kraken_request('GET', 'search/games',
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
        r = self.kraken_request('GET', 'games/top',
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
        :returns: the model instance
        :rtype: :class:`models.Channel`
        :raises: None
        """
        r = self.kraken_request('GET', 'channels/' + name)
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
        r = self.kraken_request('GET', 'search/channels',
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

        r = self.kraken_request('GET', 'streams/' + channel)
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

        channelnames = []
        cparam = None
        if channels:
            for c in channels:
                if isinstance(c, models.Channel):
                    c = c.name
                channelnames.append(c)
            cparam = ','.join(channelnames)

        params = {'limit': limit,
                  'offset': offset,
                  'game': game,
                  'channel': cparam}

        r = self.kraken_request('GET', 'streams', params=params)
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
        r = self.kraken_request('GET', 'search/streams',
                                params={'query': query,
                                        'hls': hls,
                                        'limit': limit,
                                        'offset': offset})
        return models.Stream.wrap_search(r)

    @needs_auth
    def followed_streams(self, limit=25, offset=0):
        """Return the streams the current user follows.

        Needs authorization ``user_read``.

        :param limit: maximum number of results
        :type limit: :class:`int`
        :param offset: offset for pagination
        :type offset: :class:`int`
        :returns: A list of streams
        :rtype: :class:`list`of :class:`models.Stream` instances
        :raises: :class:`exceptions.NotAuthorizedError`
        """
        r = self.kraken_request('GET', 'streams/followed',
                                params={'limit': limit,
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
        r = self.kraken_request('GET', 'user/' + name)
        return models.User.wrap_get_user(r)

    @needs_auth
    def query_login_user(self, ):
        """Query and return the currently logined user

        :returns: The user instance
        :rtype: :class:`models.User`
        :raises: :class:`exceptions.NotAuthorizedError`
        """
        r = self.kraken_request('GET', 'user')
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
                  'allow_source': True}
        r = self.usher_request(
            'GET', 'channel/hls/%s.m3u8' % channel, params=params)
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
        r = self.oldapi_request(
            'GET', 'channels/%s/access_token' % channel).json()
        return r['token'], r['sig']

    def get_chat_server(self, channel):
        """Get an appropriate chat server for the given channel

        Usually the server is irc.twitch.tv. But because of the delicate
        twitch chat, they use a lot of servers. Big events are on special
        event servers. This method tries to find a good one.

        :param channel: the channel with the chat
        :type channel: :class:`models.Channel`
        :returns: the server address and port
        :rtype: (:class:`str`, :class:`int`)
        :raises: None
        """
        r = self.oldapi_request(
            'GET', 'channels/%s/chat_properties' % channel.name)
        json = r.json()
        servers = json['chat_servers']

        try:
            r = self.get(TWITCH_STATUSURL)
        except requests.HTTPError:
            log.debug('Error getting chat server status. Using random one.')
            address = servers[0]
        else:
            stats = [client.ChatServerStatus(**d) for d in r.json()]
            address = self._find_best_chat_server(servers, stats)

        server, port = address.split(':')
        return server, int(port)

    @staticmethod
    def _find_best_chat_server(servers, stats):
        """Find the best from servers by comparing with the stats

        :param servers: a list if server adresses, e.g. ['0.0.0.0:80']
        :type servers: :class:`list` of :class:`str`
        :param stats: list of server statuses
        :type stats: :class:`list` of :class:`chat.ChatServerStatus`
        :returns: the best server adress
        :rtype: :class:`str`
        :raises: None
        """
        best = servers[0]  # In case we sind no match with any status
        stats.sort()  # gets sorted for performance
        for stat in stats:
            for server in servers:
                if server == stat:
                    # found a chatserver that has the same address
                    # than one of the chatserverstats.
                    # since the stats are sorted for performance
                    # the first hit is the best, thus break
                    best = server
                    break
            if best:
                # already found one, so no need to check the other
                # statuses, which are worse
                break
        return best

    def get_emote_picture(self, emote, size=1.0):
        """Return the picture for the given emote

        :param emote: the emote object
        :type emote: :class:`pytwitcherapi.chat.message.Emote`
        :param size: the size of the picture.
                     Choices are: 1.0, 2.0, 3.0
        :type size: :class:`float`
        :returns: A string resembling the picturedata of the emote
        :rtype: :class:`str`
        :raises: None
        """
        r = self.get('http://static-cdn.jtvnw.net/emoticons/v1/%s/%s' %
                     (emote.emoteid, size))
        return r.content
