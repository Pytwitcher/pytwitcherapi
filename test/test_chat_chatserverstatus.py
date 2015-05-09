from pytwitcherapi import chat


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
