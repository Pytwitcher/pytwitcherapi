import mock
import pytest
import requests

from pytwitcherapi import twitch


@pytest.fixture(scope="function")
def mock_session(monkeypatch):
    """Replace the request method of session with a mock."""
    monkeypatch.setattr(requests.Session, "request", mock.Mock())


@pytest.fixture(scope="function",
                params=[400, 499, 500, 599])
def mock_session_error_status(request, mock_session):
    """Make sessions return a response with error codes"""
    response = requests.Response()
    response.status_code = request.param
    requests.Session.request.return_value = response


@pytest.fixture(scope="function")
def game1json():
    """Return a dict for a game

    Name: Gaming Talk Shows
    box: {}
    logo: {}
    _id: 1252
    """
    return {"name": "Gaming Talk Shows", "box": {}, "logo": {}, "_id": 1252}


@pytest.fixture(scope="function")
def game2json():
    """Return a dict for a game

    Name: Test2
    box: {}
    logo: {}
    _id: 1212
    """
    return {"name": "Test2", "box": {}, "logo": {}, "_id": 1212}


@pytest.fixture(scope="function")
def games_search_response(game1json, game2json):
    """Return a response mock that returns the searchresult json
    with game1json and game2json when you call the json method.
    """
    searchjson = {"games": [game1json, game2json]}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = searchjson
    return mockresponse


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
    mockresponse = mock.Mock()
    mockresponse.json.return_value = topjson
    return mockresponse


def assert_game_equals_json(game, json):
    """Assert that the given game resembles the given json

    :param game: The game instance
    :type game: :class:`twitch.Game`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    assert game.name == json.get("name")
    assert game.box == json.get("box")
    assert game.logo == json.get("logo")
    assert game.twitchid == json.get("_id")


@pytest.fixture(scope="function")
def channel1json():
    """Return a dict for a channel

    Name: test_channel
    """
    c = {"mature": False,
         "status": "test status",
         "broadcaster_language": "en",
         "display_name": "test_channel",
         "game": "Gaming Talk Shows",
         "delay": 0,
         "language": "en",
         "_id": 12345,
         "name": "test_channel",
         "logo": "test_channel_logo_url",
         "banner": "test_channel_banner_url",
         "video_banner": "test_channel_video_banner_url",
         "url": "http://www.twitch.tv/test_channel",
         "views": 49144894,
         "followers": 215780}
    return c


@pytest.fixture(scope="function")
def channel2json():
    """Return a dict for a channel

    Name: loremipsum
    """
    c = {"mature": False,
         "status": "test my status",
         "broadcaster_language": "de",
         "display_name": "huehue",
         "game": "Tetris",
         "delay": 30,
         "language": "kr",
         "_id": 63412,
         "name": "loremipsum",
         "logo": "loremipsum_logo_url",
         "banner": "loremipsum_banner_url",
         "video_banner": "loremipsum_video_banner_url",
         "url": "http://www.twitch.tv/loremipsum",
         "views": 4976,
         "followers": 642}
    return c


@pytest.fixture(scope="function")
def channel1(channel1json):
    """Return a Channel instance for channel1json

    :rtype: :class:`twitch.Channel`
    """
    return twitch.Channel.wrap_json(channel1json)


@pytest.fixture(scope="function")
def channel2(channel2json):
    """Return a Channel instance for channel2json

    :rtype: :class:`twitch.Channel`
    """
    return twitch.Channel.wrap_json(channel2json)


@pytest.fixture(scope="function")
def search_channels_response(channel1json, channel2json):
    """Return a response mock that returns the search result
    with channel1json and channel2json when you call the json method
    """
    searchjson = {"channels": [channel1json,
                               channel2json]}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = searchjson
    return mockresponse


@pytest.fixture(scope="function")
def get_channel_response(channel1json):
    """Return a response mock that returns channel1json
    when calling the json method
    """
    mockresponse = mock.Mock()
    mockresponse.json.return_value = channel1json
    return mockresponse




def assert_channel_equals_json(channel, json):
    """Assert that the given channel resembles the given json

    :param channel: The channel instance
    :type channel: :class:`twitch.Channel`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    assert channel.name == json.get('name')
    assert channel.status == json.get('status')
    assert channel.displayname == json.get('display_name')
    assert channel.game == json.get('game')
    assert channel.twitchid == json.get('_id')
    assert channel.views == json.get('views')
    assert channel.followers == json.get('followers')
    assert channel.url == json.get('url')
    assert channel.language == json.get('language')
    assert channel.broadcaster_language == json.get('broadcaster_language')
    assert channel.mature == json.get('mature')
    assert channel.logo == json.get('logo')
    assert channel.banner == json.get('banner')
    assert channel.delay == json.get('delay')
    assert channel.video_banner == json.get('video_banner')


@pytest.fixture(scope="function")
def stream1json(channel1json):
    """Return a dict for a stream

    Game: Gaming Talk Shows
    Channel: channel1json
    """
    s = {'game': 'Gaming Talk Shows',
         'viewers': 9865,
         '_id': 34238,
         'preview': {"small": "test_channel-80x45.jpg",
                     "medium": "test_channel-320x180.jpg",
                     "large": "test_channel-640x360.jpg",
                     "template": "test_channel-{width}x{height}.jpg"},
         'channel': channel1json}
    return s


@pytest.fixture(scope="function")
def stream2json(channel2json):
    """Return a dict for a stream

    Game: Tetris
    Channel: channel2json
    """
    s = {'game': 'Tetris',
         'viewers': 7563,
         '_id': 145323,
         'preview': {"small": "loremipsum-80x45.jpg",
                     "medium": "loremipsum-320x180.jpg",
                     "large": "loremipsum-640x360.jpg",
                     "template": "loremipsum-{width}x{height}.jpg"},
         'channel': channel2json}
    return s


@pytest.fixture(scope="function")
def search_streams_response(stream1json, stream2json):
    """Return a response mock that returns the searchresult
    with stream1json and stream2json when calling the json method
    """
    searchjson = {"streams": [stream1json,
                               stream2json]}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = searchjson
    return mockresponse


@pytest.fixture(scope="function")
def get_stream_response(stream1json):
    """Return a response mock that returns the get stream result
    with stream1json when calling the json method
    """
    json = {"stream": stream1json}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = json
    return mockresponse


@pytest.fixture(scope="function")
def get_offline_stream_response():
    """Return a response mock that returns the get stream result
    with no stream when calling the json method
    """
    mockresponse = mock.Mock()
    mockresponse.json.return_value = {'stream': None}
    return mockresponse


def assert_stream_equals_json(stream, json):
    """Assert that the given stream resembles the given json

    :param stream: The stream instance
    :type stream: :class:`twitch.Stream`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    assert_channel_equals_json(stream.channel, json.get('channel'))
    assert stream.game == json.get('game')
    assert stream.viewers == json.get('viewers')
    assert stream.twitchid == json.get('_id')
    assert stream.preview == json.get('preview')


@pytest.fixture(scope="function")
def user1json():
    """Return a dict for a user

    Name: test_user1
    """
    u = {'type': 'user',
         'name': 'test_user1',
         'logo': 'test_user1_logo.jpeg',
         '_id': 21229404,
         'display_name': 'test_user1',
         'bio': 'test bio woo I am a test user'}
    return u


@pytest.fixture(scope="function")
def get_user_response(user1json):
    """Return a mock response that returns user1json
    when calling the json method
    """
    mockresponse = mock.Mock()
    mockresponse.json.return_value = user1json
    return mockresponse


def assert_user_equals_json(user, json):
    """Assert that the given user resembles the given json

    :param user: The user instance
    :type user: :class:`twitch.User`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    assert user.usertype == json['type']
    assert user.name == json['name']
    assert user.logo == json['logo']
    assert user.twitchid == json['_id']
    assert user.displayname == json['display_name']
    assert user.bio == json['bio']
