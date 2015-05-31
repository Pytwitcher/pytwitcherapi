import mock
import pytest
import requests

from pytwitcherapi import session, constants


def create_mockresponse(returnvalue):
    """Create a response that will return the given value when calling the json method

    :param returnvalue: the returnvalue for the response.json method
    :type returnvalue: :class:`dict`
    :returns: a mock object with a mocked json method
    :rtype: :class:`mock.Mock`
    :raises: None
    """
    mockresponse = mock.Mock()
    mockresponse.json.return_value = returnvalue
    return mockresponse


@pytest.fixture(scope="function")
def mock_session(monkeypatch):
    """Replace the request method of session with a mock."""
    monkeypatch.setattr(requests.Session, "request", mock.Mock())


@pytest.fixture(scope="function")
def ts(mock_session):
    """Return a :class:`session.TwitchSession`
    and mock the request of :class:`Session`
    """
    return session.TwitchSession()


@pytest.fixture(scope="function",
                params=[400, 499, 500, 599])
def mock_session_error_status(request, mock_session):
    """Make sessions return a response with error codes"""
    response = requests.Response()
    response.status_code = request.param
    requests.Session.request.return_value = response


@pytest.fixture(scope="function")
def games_search_response(game1json, game2json):
    """Return a response mock that returns the searchresult json
    with game1json and game2json when you call the json method.
    """
    searchjson = {"games": [game1json, game2json]}
    return create_mockresponse(searchjson)


@pytest.fixture(scope="function")
def top_games_response(game1json, game2json):
    """Return a response mock that returns the topgames result
    json with game1json and game2json when you call the json method.
    """
    topjson = {"top": [{'game': game1json,
                        'viewers': 123,
                        'channels': 32},
                       {'game': game2json,
                        'viewers': 7312,
                        'channels': 95}]}
    return create_mockresponse(topjson)


@pytest.fixture(scope="function")
def search_channels_response(channel1json, channel2json):
    """Return a response mock that returns the search result
    with channel1json and channel2json when you call the json method
    """
    searchjson = {"channels": [channel1json,
                               channel2json]}
    return create_mockresponse(searchjson)


@pytest.fixture(scope="function")
def get_channel_response(channel1json):
    """Return a response mock that returns channel1json
    when calling the json method
    """
    return create_mockresponse(channel1json)


@pytest.fixture(scope="function")
def search_streams_response(stream1json, stream2json):
    """Return a response mock that returns the searchresult
    with stream1json and stream2json when calling the json method
    """
    searchjson = {"streams": [stream1json,
                              stream2json]}
    return create_mockresponse(searchjson)


@pytest.fixture(scope="function")
def get_stream_response(stream1json):
    """Return a response mock that returns the get stream result
    with stream1json when calling the json method
    """
    json = {"stream": stream1json}
    return create_mockresponse(json)


@pytest.fixture(scope="function")
def get_offline_stream_response():
    """Return a response mock that returns the get stream result
    with no stream when calling the json method
    """
    return create_mockresponse({'stream': None})


@pytest.fixture(scope="function")
def get_user_response(user1json):
    """Return a mock response that returns user1json
    when calling the json method
    """
    return create_mockresponse(user1json)


@pytest.fixture(scope='function')
def access_token_response():
    return create_mockresponse(
        {u'token': u'{"channel":"test_channel"}',
         u'mobile_restricted': False,
         u'sig': u'f63275898c8aa0b88a6e22acf95088323f006b9d'})


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
def login_server(request, user1, monkeypatch):
    monkeypatch.setattr(constants, 'LOGIN_SERVER_ADRESS', ('', 0))

    def query_login_user():
        return user1
    ts = session.TwitchSession()
    ts.query_login_user = query_login_user

    def shutdown():
        ts.shutdown_login_server()
    request.addfinalizer(shutdown)
    ts.start_login_server()
    port = ts.login_server.socket.getsockname()[1]
    redirecturi = constants.REDIRECT_URI.replace('42420', str(port))
    monkeypatch.setattr(constants, 'REDIRECT_URI', redirecturi)
    return ts
