====
Chat
====

The twitch chat is based on the IRC protocol `RFC1459 <tools.ietf.org/html/rfc1459.html>`_.
The official documentation on the twitch chat is here: `Twitch IRC Doc <https://github.com/justintv/Twitch-API/blob/master/IRC.md>`_.
The `irc python lib <https://pythonhosted.org/irc/index.html>`_ might also be useful, because we use it as backend.

:class:`pytwitcherapi.IRCClient` is a simple client, which can only connect to one channel/server at a time.
When building applications, you probably wanna run the IRCClient in another thread, so it doesn't block your application.
The client is thread safe and has quite a few methods to send IRC commands, if the client is running in another thread.
They are wrapped versions of methods from :class:`irc.client.ServerConnection`. E.g. you can simply call :meth:`pytwitcherapi.IRCClient.quit` from another thread. Here is a simple example, where we send messages to the channel.
Change ``input`` to ``raw_input`` for python 2::

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


You can make the client handle different IRC events. Subclass the client and create a method ``on_<eventtype>``.
For example to greet everyone who joins an IRC channel::

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

If you override :meth:`pytwitcherapi.IRCClient.on_pubmsg` or :meth:`pytwitcherapi.IRCClient.on_privmsg` make sure to call
the super method::


     class MyIRCClient(pytwitcherapi.IRCClient):

         def on_privmsg(self, connection, event):
             super(MyIRCClient, self).on_privmsg(connection, event)
	     print 'Received message from %s: %s' % (event.source, event.arguments[0])


But printing out messages is not really useful. You probably want to access them in another thread.
All private and public messages are stored in a thread safe message queue. By default the queue stores the last 100 messages.
You can alter the queuesize when creating a client. ``0`` will make the queue store all messages.
Here is a little example. To quit press ``CTRL-C``::

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
                  # Now you have the message in the main thread and can display the message in the
                  # GUI or whatever you want
                  print "Message from %s to %s: %s" % (m.source, m.target, m.text)
      finally:
          client.shutdown()
          t.join()


-----------------
Tags and metadata
-----------------

Twitch does support `tags <http://ircv3.net/specs/core/message-tags-3.2.html>`_.
Tags store metadata about a message, like the color of the user,
whether he is a subscriber, the :class:`pytwichterapi.chat.Emote` etc.
These messages get safed id the message queue: :data:`pytwitcherapi.IRCClient.messages`.
See the :class:`pytwitcherapi.chat.Message3` documentation for the additional metadata.


Here is a little example. To quit press ``CTRL-C``::

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
