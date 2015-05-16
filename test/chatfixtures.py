import pytest

from pytwitcherapi import chat


@pytest.fixture(scope='session')
def servers_json():
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
    return j


@pytest.fixture(scope='function')
def servers(servers_json):
    return [chat.ChatServerStatus(**d) for d in servers_json]
