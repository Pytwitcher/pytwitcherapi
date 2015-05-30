#!/usr/bin/env python
"""Execute this script and follow the instructions.
First it authorizes the session, so we can login to the chat.
Then we create an irc client. The client will print out messages.
You can also type messages and send them.
To exit, press CTRL-C.
"""

import sys
import threading
import webbrowser

import pytwitcherapi

if sys.version_info[0] == 3:
    raw_input = input


class IRCClient(pytwitcherapi.IRCClient):
    """This client will print out private and public messages"""
    def on_pubmsg(self, connection, event):
        super(IRCClient, self).on_pubmsg(connection, event)
        message = self.messages.get()
        print '%s: %s' % (message.source.nickname, message.text)

    def on_privmsg(self, connection, event):
        super(IRCClient, self).on_pubmsg(connection, event)
        message = self.messages.get()
        print '%s: %s' % (message.source.nickname, message.text)


def authorize(session):
    session.start_login_server()
    url = session.get_auth_url()
    webbrowser.open(url)
    raw_input("Please authorize Pytwitcher in the browser then press ENTER!")
    assert session.authorized, "Authorization failed! Did the user allow it?"


def create_client(session):
    channelname = raw_input("Type in the channel to join:")
    channel = session.get_channel(channelname)
    return IRCClient(session, channel)


def main():
    session = pytwitcherapi.TwitchSession()
    authorize(session)
    client = create_client(session)

    t = threading.Thread(target=client.process_forever)
    t.start()

    try:
        while True:
            message = raw_input('Type your message and hit ENTER to send:\n')
            client.send_msg(message)
            print '%s: %s' % (session.current_user.name, message)
    finally:
        client.shutdown()
        t.join()

if __name__ == '__main__':
    main()
