import threading
import queue  # Queue for python 2

import pytwitcherapi

session = ...  # we assume an authenticated TwitchSession
channel = session.get_channel('somechannel')
client = pytwitcherapi.IRCClient(session, channel, queuesize=0)
t = threading.Thread(target=client.process_forever)
t.start()

try:
    while True:
        try:
            m = client.messages.get(block=False)
        except queue.Empty:
            pass
        else:
            print m.color
            print m.subscriber
            print m.turbo
            print m.emotes
            print m.user_type
finally:
    client.shutdown()
    t.join()
