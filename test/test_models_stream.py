from pytwitcherapi import models
from test import conftest


def test_wrap_json(stream1json):
    s = models.Stream.wrap_json(stream1json)
    conftest.assert_stream_equals_json(s, stream1json)


def test_repr(stream1json):
    s = models.Stream.wrap_json(stream1json)
    assert repr(s) == '<Stream %s, id: %s>' % (s.channel.name, s.twitchid)


def test_wrap_search(search_streams_response, stream1json, stream2json):
    streams = models.Stream.wrap_search(search_streams_response)
    for s, j in zip(streams, [stream1json, stream2json]):
        conftest.assert_stream_equals_json(s, j)


def test_wrap_get_stream(get_stream_response, stream1json):
    s = models.Stream.wrap_get_stream(get_stream_response)
    conftest.assert_stream_equals_json(s, stream1json)


def test_wrap_get_offline_stream(get_offline_stream_response):
    s = models.Stream.wrap_get_stream(get_offline_stream_response)
    assert s is None
