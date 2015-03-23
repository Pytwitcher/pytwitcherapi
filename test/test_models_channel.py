from pytwitcherapi import models
from test import conftest


def test_repr(channel1json):
    c = models.Channel.wrap_json(channel1json)
    assert repr(c) == '<Channel %s, id: %s>' % (c.name, c.twitchid)


def test_wrap_json(channel1json):
    c = models.Channel.wrap_json(channel1json)
    conftest.assert_channel_equals_json(c, channel1json)


def test_wrap_json_incomplete(channel1json):
    del channel1json['url']
    c = models.Channel.wrap_json(channel1json)
    conftest.assert_channel_equals_json(c, channel1json)


def test_wrap_search(search_channels_response, channel1json, channel2json):
    channels = models.Channel.wrap_search(search_channels_response)
    for c, j in zip(channels, [channel1json, channel2json]):
        conftest.assert_channel_equals_json(c, j)


def test_wrap_get_channel(get_channel_response, channel1json):
    c = models.Channel.wrap_get_channel(get_channel_response)
    conftest.assert_channel_equals_json(c, channel1json)
