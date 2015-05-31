import threading

import pytwitcherapi

session = ...  # we assume an authenticated TwitchSession
channel = session.get_channel('somechannel')
client = pytwitcherapi.IRCClient(session, channel)
t = threading.Thread(target=client.process_forever)
t.start()

try:
    while True:
        m = input('Send Message:')
        if not m: break;
        # will be processed in other thread
        # sends a message to the server
        client.send_msg(m)
finally:
    client.shutdown()
    t.join()
