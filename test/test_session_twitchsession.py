from __future__ import absolute_import

import contextlib
import os
import pkg_resources

import m3u8
import mock
import pytest
import requests
import requests.utils

from pytwitcherapi import session, models, exceptions, constants
from . import conftest


@pytest.fixture(scope='module')
def auth_redirect_uri():
    ruri = constants.REDIRECT_URI + '/#access_token=u7amjlndoes3xupi4bb1jrzg2wrcm1&scope=user_read'
    return ruri


@pytest.fixture(scope='function')
def auth_headers():
    return {'Authorization': 'OAuth u7amjlndoes3xupi4bb1jrzg2wrcm1'}


@pytest.fixture(scope="function")
def ts(mock_session):
    """Return a :class:`session.TwitchSession`
    and mock the request of :class:`Session`
    """
    return session.TwitchSession()


@pytest.fixture(scope='function')
def authts(ts, auth_redirect_uri):
    uri = auth_redirect_uri.replace('http://', 'https://')
    ts.token_from_fragment(uri)
    return ts


@pytest.fixture(scope="function")
def tswithbase(ts):
    """Return a :class:`session.TwitchSession` with
    baseurl 'someurl' and {'test': 'test'} in the headers
    """
    ts.baseurl = 'someurl'
    ts.headers['test'] = 'test'
    return ts


@pytest.fixture(scope="function")
def mock_fetch_viewers(monkeypatch):
    """Mock the fetch_viewers method of :class:`session.TwitchSession`"""
    monkeypatch.setattr(session.TwitchSession, "fetch_viewers", mock.Mock())


@pytest.fixture(scope="function")
def mock_session_get_viewers(monkeypatch):
    """Mock :meth:`session.TwitchSession.get` to return the summary
    result for a game
    """
    monkeypatch.setattr(session.TwitchSession, "get", mock.Mock())
    mockjson = {"viewers": 124,
                "channels": 12}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = mockjson
    session.TwitchSession.get.return_value = mockresponse


@pytest.fixture(scope='function')
def playlist():
    """Return a sample playlist text"""
    p = """#EXTM3U
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="chunked",NAME="Source"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="chunked"
sourclink
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="high",NAME="High"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="high"
highlink
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="medium",NAME="Medium"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="medium"
mediumlink
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="low",NAME="Low"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="low"
lowlink
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="mobile",NAME="Mobile"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="mobile"
mobilelink
#EXT-X-MEDIA:TYPE=VIDEO,GROUP-ID="audio_only",NAME="Audio Only"
#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=128000,CODECS="mp4a.40.2",VIDEO="audio_only"
audioonlylink"""
    return p


@pytest.fixture(scope='function')
def mock_get_channel_access_token(monkeypatch):
    """Mock :meth:`session.TwitchSession.get_channel_access_token`"""
    monkeypatch.setattr(session.TwitchSession, 'get_channel_access_token', mock.Mock())


@pytest.fixture(scope='function')
def mock_get_playlist(monkeypatch):
    """Mock :meth:`session.TwitchSession.get_playlist`"""
    monkeypatch.setattr(session.TwitchSession, 'get_playlist', mock.Mock())


@contextlib.contextmanager
def check_base_header(session):
    """Contextmanager for checking if the baseurl and headers are the same
    when exiting.
    """
    oldbaseurl = session.baseurl
    oldheaders = session.headers
    yield
    assert session.baseurl == oldbaseurl
    assert session.headers == oldheaders


@pytest.mark.parametrize("base,url,full", [
    ("testbase/url/", "hallo", "testbase/url/hallo"),
    ("", "hallo", "hallo"),
    (None, "hallo", "hallo"),
])
def test_request(ts, base, url, full, mock_session):
    ts.baseurl = base
    r = ts.request("GET", url)
    # check if the session used the full url
    requests.Session.request.assert_called_with("GET", full)
    assert r


def test_request_kraken(tswithbase, mock_session):
    url = "hallo"
    with check_base_header(tswithbase), session.kraken(tswithbase):
        tswithbase.request("GET", url)
        # assert we are using the correct headers
        # assert default headers with 'Accept' have been used
        assert 'test' not in tswithbase.headers
        assert tswithbase.headers['Accept'] == session.TWITCH_HEADER_ACCEPT
    # assert the kraken url was used
    requests.Session.request.assert_called_with("GET",
                                                session.TWITCH_KRAKENURL + url,
                                                headers=None, data=None)


def test_request_default(tswithbase, mock_session):
    url = "hallo"
    with check_base_header(tswithbase), session.default(tswithbase):
        tswithbase.request("GET", url)
        assert tswithbase.headers == requests.utils.default_headers()
    # assert that the no baseurl was used
    requests.Session.request.assert_called_with("GET", url)


def test_request_oldapi(tswithbase, mock_session):
    url = "hallo"
    with check_base_header(tswithbase), session.oldapi(tswithbase):
        tswithbase.request("GET", url)
        assert tswithbase.headers == requests.utils.default_headers()
    # assert that the api url as baseurl was used
    requests.Session.request.assert_called_with("GET", session.TWITCH_APIURL + url)


def test_request_usher(tswithbase, mock_session):
    url = "hallo"
    with check_base_header(tswithbase), session.usher(tswithbase):
        tswithbase.request("GET", url)
        assert tswithbase.headers == requests.utils.default_headers()
    # assert that the usherurl as baseurl was used
    requests.Session.request.assert_called_with("GET", session.TWITCH_USHERURL + url)


def test_raise_httperror(ts, mock_session_error_status):
    # assert that responses with error status_codes
    # immediately get raised as errors
    with pytest.raises(requests.HTTPError):
        ts.request("GET", "test")


@pytest.mark.parametrize('sessionfixture',
    ['authts',
     pytest.mark.xfail(raises=exceptions.NotAuthorizedError)('ts')])
def test_needs_auth(sessionfixture, request):
    ts = request.getfuncargvalue(sessionfixture)

    @session.needs_auth
    def authorized_request(session, *args, **kwargs):
        return args, kwargs

    r = authorized_request(ts, 1, kwarg=2)
    # assert return is correct
    assert r == ((1,), {'kwarg': 2}), "Returnvalue incorrect"


def test_search_games(ts, games_search_response,
                      game1json, game2json, mock_fetch_viewers):
    requests.Session.request.return_value = games_search_response
    games = ts.search_games(query='test', live=True)

    # check result
    assert len(games) == 2
    for g, j in zip(games, [game1json, game2json]):
        conftest.assert_game_equals_json(g, j)

    # check if request was correct
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'search/games',
        params={'query': 'test',
                'type': 'suggest',
                'live': True},
        allow_redirects=True, headers=None, data=None)

    # check if mocked fetch viewers was called correctly
    ts.fetch_viewers.assert_has_calls([mock.call(g) for g in games],
                                      any_order=True)


def test_fetch_viewers(ts, mock_session_get_viewers):
    game = models.Game(name="Test", box={}, logo={}, twitchid=214)
    game2 = ts.fetch_viewers(game)
    # assert that attributes have been set
    assert game.viewers == 124
    assert game.channels == 12
    # assert the game was also returned
    assert game2 is game
    # assert the request was correct
    ts.get.assert_called_with("streams/summary", params={"game": "Test"})


def test_top_games(ts, game1json, game2json,
                   top_games_response):
    requests.Session.request.return_value = top_games_response
    games = ts.top_games(limit=10, offset=0)
    # check result
    assert len(games) == 2
    for g, j in zip(games, [game1json, game2json]):
        conftest.assert_game_equals_json(g, j)
    # assert the viewers and channels from the response were already set
    assert games[0].viewers == 123
    assert games[0].channels == 32
    assert games[1].viewers == 7312
    assert games[1].channels == 95
    # assert the request was correct
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'games/top',
        params={'limit': 10,
                'offset': 0},
        allow_redirects=True, headers=None, data=None)


def test_get_game(ts, mock_fetch_viewers,
                  games_search_response, game2json):
    requests.Session.request.return_value = games_search_response
    g = ts.get_game(game2json['name'])
    conftest.assert_game_equals_json(g, game2json)


def test_get_channel(ts, get_channel_response, channel1json):
    requests.Session.request.return_value = get_channel_response
    channel = ts.get_channel(channel1json['name'])

    conftest.assert_channel_equals_json(channel, channel1json)
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'channels/'+ channel1json['name'],
        allow_redirects=True, headers=None, data=None)


def test_search_channels(ts, search_channels_response,
                         channel1json, channel2json):
    requests.Session.request.return_value = search_channels_response
    channels = ts.search_channels(query='test',
                                  limit=35,
                                  offset=10)

    # check result
    assert len(channels) == 2
    for c, j in zip(channels, [channel1json, channel2json]):
        conftest.assert_channel_equals_json(c, j)

    # assert the request was correct
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'search/channels',
        params={'query': 'test',
                'limit': 35,
                'offset': 10},
        allow_redirects=True, headers=None, data=None)


def test_get_stream(ts, get_stream_response, stream1json):
    requests.Session.request.return_value = get_stream_response
    s1 = ts.get_stream(stream1json['channel']['name'])
    s2 = ts.get_stream(models.Channel.wrap_json(stream1json['channel']))

    # check result
    for s in [s1, s2]:
        conftest.assert_stream_equals_json(s, stream1json)

    # assert the request was correct
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'streams/' +
        stream1json['channel']['name'],
        allow_redirects=True, headers=None, data=None)


def test_get_streams(ts, search_streams_response, channel1,
                     stream1json, stream2json, game1json):
    requests.Session.request.return_value = search_streams_response
    # check with different input types
    games = [game1json['name'],
             models.Game.wrap_json(game1json)]
    channels = [[channel1, 'asdf'], None]
    params = [{'game': game1json['name'],
               'channel': 'test_channel,asdf',
               'limit': 35,
               'offset': 10},
              {'game': game1json['name'],
               'limit': 35,
               'offset': 10}]

    for g, c, p in zip(games, channels, params):
        streams = ts.get_streams(game=g,
                                 channels=c,
                                 limit=35,
                                 offset=10)

        # check the result
        assert len(streams) == 2
        for s, j in zip(streams, [stream1json, stream2json]):
            conftest.assert_stream_equals_json(s, j)

        # assert the request was correct
        requests.Session.request.assert_called_with('GET',
            session.TWITCH_KRAKENURL + 'streams',
            params=p,
            allow_redirects=True, headers=None, data=None)


def test_search_streams(ts, search_streams_response,
                        stream1json, stream2json):
    requests.Session.request.return_value = search_streams_response
    streams = ts.search_streams(query='testquery',
                                hls=False,
                                limit=25,
                                offset=10)

    # check the result
    assert len(streams) == 2
    for s, j in zip(streams, [stream1json, stream2json]):
        conftest.assert_stream_equals_json(s, j)

    p = {'query': 'testquery',
         'hls': False,
         'limit': 25,
         'offset': 10}
    requests.Session.request.assert_called_with('GET',
            session.TWITCH_KRAKENURL + 'search/streams',
            params=p,
            allow_redirects=True, headers=None, data=None)


@pytest.mark.parametrize('sessionfixture',
                         ['authts',
                          pytest.mark.xfail(raises=exceptions.NotAuthorizedError)('ts')])
def test_followed_streams(request, sessionfixture, search_streams_response,
                          stream1json, stream2json, auth_headers):
    ts = request.getfuncargvalue(sessionfixture)
    requests.Session.request.return_value = search_streams_response
    streams = ts.followed_streams(limit=42, offset=13)
    # check result
    assert len(streams) == 2
    for s, j in zip(streams, [stream1json, stream2json]):
        conftest.assert_stream_equals_json(s, j)
    # check call
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'streams/followed',
        params={'limit': 42, 'offset': 13},
        allow_redirects=True, headers=auth_headers, data=None)


def test_get_user(ts, get_user_response,
                  user1json):
    requests.Session.request.return_value = get_user_response
    user = ts.get_user('nameofuser')

    conftest.assert_user_equals_json(user, user1json)


@pytest.mark.parametrize('sessionfixture',
                         ['authts',
                          pytest.mark.xfail(raises=exceptions.NotAuthorizedError)('ts')])
def test_fetch_login_user(request, sessionfixture, get_user_response,
                          user1json, auth_headers):
    ts = request.getfuncargvalue(sessionfixture)
    requests.Session.request.return_value = get_user_response
    user = ts.fetch_login_user()
    conftest.assert_user_equals_json(user, user1json)
    assert user == ts.current_user
    requests.Session.request.assert_called_with('GET',
        session.TWITCH_KRAKENURL + 'user',
        allow_redirects=True,
        headers=auth_headers, data=None)


def test_get_channel_access_token(ts, channel1):
    # test with different input types
    channels = [channel1.name, channel1]
    mocktoken = {u'token': u'{"channel":"test_channel"}',
                 u'mobile_restricted': False,
                 u'sig': u'f63275898c8aa0b88a6e22acf95088323f006b9d'}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = mocktoken
    requests.Session.request.return_value = mockresponse

    for c in channels:
        token, sig = ts.get_channel_access_token(c)
        requests.Session.request.assert_called_with('GET',
            session.TWITCH_APIURL + 'channels/%s/access_token' % channel1.name,
            allow_redirects=True)
        assert token == mocktoken['token']
        assert sig == mocktoken['sig']


def test_get_playlist(ts, mock_get_channel_access_token,
                      channel1, playlist):
    token = 'sometoken'
    sig = 'somesig'
    session.TwitchSession.get_channel_access_token.return_value = (token, sig)
    mockresponse = mock.Mock()
    mockresponse.text = playlist
    requests.Session.request.return_value = mockresponse
    # test with different input types
    channels = ['test_channel', channel1]
    params = {'token': token, 'sig': sig,
              'allow_audio_only': True,
              'allow_source': True}
    # assert the playlist finds these media ids
    mediaids = ['chunked', 'high', 'medium', 'low', 'mobile', 'audio_only']
    for c in channels:
        p = ts.get_playlist(c)
        for pl, mi in zip(p.playlists, mediaids):
            assert pl.media[0].group_id == mi
        # assert the request was correct
        requests.Session.request.assert_called_with('GET',
            session.TWITCH_USHERURL + 'channel/hls/test_channel.m3u8',
            params=params, allow_redirects=True)
        # assert the mocked get_channel_access_token was called correctly
        session.TwitchSession.get_channel_access_token.assert_called_with('test_channel')


def test_get_quality_options(ts, mock_get_playlist, playlist, channel1):
    p = m3u8.loads(playlist)
    ts.get_playlist.return_value = p
    channels = ['test_channel', channel1]
    for c in channels:
        options = ts.get_quality_options(c)
        assert options == ['source', 'high', 'medium', 'low', 'mobile', 'audio']
        ts.get_playlist.assert_called_with(c)


def assert_html_response(r, filename):
    datapath = os.path.join('html', filename)
    sitepath = pkg_resources.resource_filename('pytwitcherapi', datapath)
    with open(sitepath, 'r') as f:
        html = f.read()
    assert r.content == html.encode('utf-8')


@pytest.fixture(scope='function')
def login_server(request):
    ts = session.TwitchSession()

    def shutdown():
        ts.shutdown_login_server()
    request.addfinalizer(shutdown)
    ts.start_login_server()
    return ts


def test_login(login_server, auth_redirect_uri):
    ruri = constants.REDIRECT_URI
    ts = login_server
    with pytest.raises(requests.HTTPError):
        ts.get(ruri + '/failingurl')
    r = ts.get(auth_redirect_uri)
    assert_html_response(r, 'extract_token_site.html')
    r = ts.get(ruri + '/success')
    assert_html_response(r, 'success_site.html')
    ts.post(ruri + '/?access_token=u7amjlndoes3xupi4bb1jrzg2wrcm1&scope=channel_read')
    assert ts.token == {'access_token': 'u7amjlndoes3xupi4bb1jrzg2wrcm1',
                        'scope': ['channel_read']}


def test_get_authurl(ts):
    ts.state = 'a'
    url = ts.get_auth_url()
    assert url == 'https://api.twitch.tv/kraken/oauth2/authorize?\
response_type=token&client_id=642a2vtmqfumca8hmfcpkosxlkmqifb\
&redirect_uri=http%3A%2F%2Flocalhost%3A42420&scope=user_read&state=a'
