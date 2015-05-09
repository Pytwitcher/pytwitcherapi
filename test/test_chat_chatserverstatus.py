import pytest

from pytwitcherapi import chat


@pytest.fixture(scope='module')
def servers():
    j = [{"server": "192.16.64.11:80",
          "ip": "192.16.64.11", "port": 80,
          "description": "Chat Server",
          "status": "online", "errors": 1,
          "lag": 157},
         {"server": "192.16.64.12:80",
          "ip": "192.16.64.12", "port": 80,
          "description": "Chat Server",
          "status": "offline", "errors": 0,
          "lag": 0},
         {"server": "192.16.64.13:80",
          "ip": "192.16.64.13", "port": 80,
          "description": "Chat Server",
          "status": "online", "errors": 0,
          "lag": 200},
         {"server": "192.16.64.14:80",
          "ip": "192.16.64.14", "port": 80,
          "description": "Chat Server",
          "status": "online", "errors": 1,
          "lag": 20}]
    return [chat.ChatServerStatus(**d) for d in j]


def test_eq_str(servers):
    assert servers[0] == '192.16.64.11:80',\
        "Server should be equal to the same address."


def test_noteq_str(servers):
    assert servers[0] != '192.16.64.50:89',\
        """Server should not be equal to a different address"""


def test_eq(servers):
    s1 = chat.ChatServerStatus('192.16.64.11:80')
    assert servers[0] == s1,\
        """Servers with same address should be equal"""


def test_noteq(servers):
    assert servers[0] != servers[1],\
        """Servers with different address should not be equal"""


def test_lt(servers):
    sortedservers = sorted(servers)
    expected = [servers[2], servers[3], servers[0], servers[1]]
    assert sortedservers == expected,\
        """Server should be sorted like this: online, then offline,
little errors, then more errors, little lag, then more lag."""
