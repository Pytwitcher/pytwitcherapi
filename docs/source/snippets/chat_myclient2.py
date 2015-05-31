from pytwitcherapi import chat

class MyIRCClient(pytwitcherapi.IRCClient):

    def on_privmsg(self, connection, event):
        super(MyIRCClient, self).on_privmsg(connection, event)

        print chat.Message3.from_event(event)
