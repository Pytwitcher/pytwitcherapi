import mock
import pytest

from pytwitcherapi import models
from test import conftest


@pytest.fixture(scope='function')
def game():
    n = 'Test Game'
    g = models.Game(name=n, box={}, logo={}, twitchid=312, viewers=1, channels=1)
    return g


def test_repr(game):
    assert repr(game) == '<Game %s, id: %s>' % (game.name, game.twitchid)


def test_wrap_json(game1json):
    g = models.Game.wrap_json(game1json)
    conftest.assert_game_equals_json(g, game1json)


def test_wrap_search(games_search_response, game1json, game2json):
    games = models.Game.wrap_search(games_search_response)
    for g, j  in zip(games, [game1json, game2json]):
        conftest.assert_game_equals_json(g, j)


def test_wrap_topgames(game1json, game2json):
    topjson = {"top": [{"game": game1json, "viewers": 123, "channels": 10},
                       {"game": game2json, "viewers": 543, "channels": 42}]}
    mockresponse = mock.Mock()
    mockresponse.json.return_value = topjson
    games = models.Game.wrap_topgames(mockresponse)
    for g, j in zip(games, [game1json, game2json]):
        conftest.assert_game_equals_json(g, j)
    assert games[0].viewers == 123
    assert games[0].channels == 10
    assert games[1].viewers == 543
    assert games[1].channels == 42
