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
            # Now you have the message in the main thread
            # and can display the message in the
            # GUI or wherever you want
            print "Message from %s to %s: %s" % (m.source, m.target, m.text)
finally:
    client.shutdown()
    t.join()
