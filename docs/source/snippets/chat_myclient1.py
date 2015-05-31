import pytwitcherapi

class MyIRCClient(pytwitcherapi.IRCClient):

    def on_join(self, connection, event):
        """Handles the join event and greets everone

        :param connection: the connection with the event
        :type connection: :class:`irc.client.ServerConnection`
        :param event: the event to handle
        :type event: :class:`irc.client.Event`
        :returns: None
        """
        target = event.source
        self.privmsg(target, 'Hello %s!' % target)
