import pytest

from pytwitcherapi import models


def assert_object_equals_dict(attributemap, obj, d):
    """Assert that the attributes of obj equal the dict values

    :param attributemap: a dict to map attributes to dict keys
    :type attributemap: :class:`dict`
    :param obj: the object with attributes
    :param d: the dictionary
    :type d: :class:`dict`
    :returns: None
    :rtype: None
    :raises: :class:`AssertionError`
    """
    for attr, key in attributemap.iteritems():
        assert getattr(obj, attr) == d.get(key)


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


def assert_game_equals_json(game, json):
    """Assert that the given game resembles the given json

    :param game: The game instance
    :type game: :class:`models.Game`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    attrs = ['name', 'box', 'logo']
    attrmap = {x: x for x in attrs}
    attrmap['twitchid'] = '_id'
    assert_object_equals_dict(attrmap, game, json)


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

    :rtype: :class:`models.Channel`
    """
    return models.Channel.wrap_json(channel1json)


@pytest.fixture(scope="function")
def channel2(channel2json):
    """Return a Channel instance for channel2json

    :rtype: :class:`models.Channel`
    """
    return models.Channel.wrap_json(channel2json)


def assert_channel_equals_json(channel, json):
    """Assert that the given channel resembles the given json

    :param channel: The channel instance
    :type channel: :class:`models.Channel`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    attrs = ['name', 'status', 'game', 'views', 'followers', 'broadcaster_language',
             'mature', 'logo', 'banner', 'delay', 'video_banner', 'language', 'url']
    attrmap = {x: x for x in attrs}
    attrmap['displayname'] = 'display_name'
    attrmap['twitchid'] = '_id'
    assert_object_equals_dict(attrmap, channel, json)


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


def assert_stream_equals_json(stream, json):
    """Assert that the given stream resembles the given json

    :param stream: The stream instance
    :type stream: :class:`models.Stream`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    attrs = ['game', 'viewers', 'preview']
    attrmap = {x: x for x in attrs}
    attrmap['twitchid'] = '_id'
    assert_channel_equals_json(stream.channel, json.get('channel'))
    assert_object_equals_dict(attrmap, stream, json)


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
def user1(user1json):
    return models.User.wrap_json(user1json)


def assert_user_equals_json(user, json):
    """Assert that the given user resembles the given json

    :param user: The user instance
    :type user: :class:`models.User`
    :param json: the json representation
    :type json: :class:`dict`
    :raises: :class:`AssertionError`
    """
    attrs = ['name', 'logo', 'bio']
    attrmap = {x: x for x in attrs}
    attrmap['usertype'] = 'type'
    attrmap['twitchid'] = '_id'
    attrmap['displayname'] = 'display_name'
    assert_object_equals_dict(attrmap, user, json)
