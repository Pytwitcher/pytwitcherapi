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
Change ``input`` to ``raw_input`` for python 2:

.. literalinclude:: /snippets/chat_sendmsg.py
   :linenos:

.. important:: The connection will wait/block if you send more messages than
	       twitch allows. See :class:`pytwitcherapi.chat.ServerConnection3`.

You can make the client handle different IRC events. Subclass the client and create a method ``on_<eventtype>``.
For example to greet everyone who joins an IRC channel:

.. literalinclude:: /snippets/chat_myclient1.py
   :linenos:

If you override :meth:`pytwitcherapi.IRCClient.on_pubmsg` or :meth:`pytwitcherapi.IRCClient.on_privmsg` make sure to call
the super method:

.. literalinclude:: /snippets/chat_myclient2.py
   :linenos:

But printing out messages is not really useful. You probably want to access them in another thread.
All private and public messages are stored in a thread safe message queue. By default the queue stores the last 100 messages.
You can alter the queuesize when creating a client. ``0`` will make the queue store all messages.

.. Note:: The Client is using two connections. One for sending messages (:data:`pytwitcherapi.IRCClient.in_connection`) and
	  one for receiving (:data:`pytwitcherapi.IRCClient.in_connection`) them.
          With one message, you wouldn't revceive your own messages processed from the server (with tags).


Here is a little example. To quit press ``CTRL-C``:

.. literalinclude:: /snippets/chat_queue.py
   :linenos:


-----------------
Tags and metadata
-----------------

Twitch does support `tags <http://ircv3.net/specs/core/message-tags-3.2.html>`_.
Tags store metadata about a message, like the color of the user,
whether he is a subscriber, the :class:`pytwichterapi.chat.Emote` etc.
These messages get safed id the message queue: :data:`pytwitcherapi.IRCClient.messages`.
See the :class:`pytwitcherapi.chat.Message3` documentation for the additional metadata.


Here is a little example. To quit press ``CTRL-C``:

.. literalinclude:: /snippets/chat_tags.py
   :linenos:
