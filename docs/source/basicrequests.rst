------------
API requests
------------

:class:`pytwitcherapi.TwitchSession` class is the central class for interacting with `twitch.tv  <https://github.com/justintv/Twitch-API>`_:

.. literalinclude:: /snippets/apirequest.py
   :linenos:
   :lineno-match:
   :lines: 1-3

To query all top games use:

.. literalinclude:: /snippets/apirequest.py
   :linenos:
   :lineno-match:
   :lines: 5

Get streams and playlist for every game:

.. literalinclude:: /snippets/apirequest.py
   :linenos:
   :lineno-match:
   :lines: 7-

As you can see games, channels, streams are wrapped into objects.
See :class:`pytwitcherapi.Game`, :class:`pytwitcherapi.Channel`, :class:`pytwitcherapi.Stream`, :class:`pytwitcherapi.User`.
