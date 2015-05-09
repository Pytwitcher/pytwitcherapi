import sys
import webbrowser
import logging
import threading

import pytwitcherapi
from pytwitcherapi import chat

logging.basicConfig(level=logging.INFO)

ts = pytwitcherapi.TwitchSession()
ts.start_login_server()
url = ts.get_auth_url()
webbrowser.open(url)
raw_input("Press ENTER when finished")
ts.shutdown_login_server()
assert ts.authorized, "Authorization failed! Did the user allow it?"
ts.fetch_login_user()

channel = ts.get_channel(sys.argv[1])

client = chat.IRCClient(ts, channel)

t = threading.Thread(target=client.reactor.process_forever, kwargs={'timeout': 0.2})
t.start()


def sendmsg(msg):
    print 'SENDING', msg
    client.connection.privmsg(client.target, msg)


def raiseerror():
    raise KeyboardInterrupt


try:
    while True:
        m = raw_input("Message:")
        if not m:
            break
        client.send_privmsg(m)
except Exception as e:
    print e
finally:
    client.shutdown()
    t.join()
