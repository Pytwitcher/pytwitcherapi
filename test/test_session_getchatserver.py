import mock
import pytest
import requests

from pytwitcherapi import session


@pytest.fixture(scope="function")
def ts(mock_session):
    """Return a :class:`session.TwitchSession`
    and mock the request of :class:`Session`
    """
    return session.TwitchSession()


@pytest.fixture(scope='function')
def mock_chatpropresponse(servers, mock_session):
    chatservers = [s.address for s in servers]
    channelprop = {"chat_servers": chatservers}
    chatpropresponse = mock.Mock()
    chatpropresponse.json.return_value = channelprop
    return chatpropresponse


@pytest.fixture(scope='function')
def mock_serverstatresponse(servers_json, mock_session):
    serverstatresponse = mock.Mock()
    serverstatresponse.json.return_value = servers_json
    return serverstatresponse


@pytest.fixture(scope='function')
def mock_chatserverresponse(mock_serverstatresponse, mock_chatpropresponse,
                            servers_json):
    requests.Session.request.side_effect = [mock_chatpropresponse,
                                            mock_serverstatresponse]
    # if serverstatresponse is successful return the best
    s = servers_json[2]
    return s['ip'], s['port']


@pytest.fixture(scope='function')
def mock_failchatserverresponse(mock_chatpropresponse, servers_json):
    serverstatresponse = mock.Mock()
    serverstatresponse.raise_for_status.side_effect = requests.HTTPError()
    requests.Session.request.side_effect = [mock_chatpropresponse,
                                            serverstatresponse]
    # if serverstatresponse fails just return the first
    s = servers_json[0]
    return s['ip'], s['port']


@pytest.fixture(scope='function')
def mock_nochatserverresponse(mock_serverstatresponse):
    # random server status that will not be in the available ones
    chatprop = {"chat_servers": ['0.16.64.11:80', '0.16.24.11:123']}
    chatpropresponse = mock.Mock()
    chatpropresponse.json.return_value = chatprop
    requests.Session.request.side_effect = [chatpropresponse,
                                            mock_serverstatresponse]
    # if no server stat for the chat servers can be found just return the first
    return '0.16.64.11', 80


@pytest.mark.parametrize('fix', ['mock_chatserverresponse',
                                 'mock_failchatserverresponse',
                                 'mock_nochatserverresponse'])
def test_get_chat_server(ts, channel1, fix, request):
    expected = request.getfuncargvalue(fix)
    server, port = ts.get_chat_server(channel1)
    assert (server, port) == expected
