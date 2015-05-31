import mock
import pytest
import requests

from test import docs_snippets


@pytest.fixture(scope='function')
def mock_request(mock_session, top_games_response, search_streams_response,
                 access_token_response, playlist):
    playlist_response = mock.Mock()
    playlist_response.text = playlist
    effectsperstream = [access_token_response,
                        playlist_response]
    effectspergame = [search_streams_response] + effectsperstream * 2
    effects = [top_games_response] + effectspergame * 2
    requests.Session.request.side_effect = effects


def test_api_requests_snippet(mock_request):
    docs_snippets.execute_snippet('apirequest.py')
