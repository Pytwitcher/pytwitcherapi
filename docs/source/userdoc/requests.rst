========
Requests
========

.. include:: ../basicrequests.rst

---------------
Custom requests
---------------

You can also issue custom requests. The :class:`pytwitcherapi.TwitchSession`
is actually a subclass of :class:`requests.Session`. So basically
you can use :meth:`pytwitcherapi.TwitchSession.request` to issue
arbitrary requests.
To make it easier to use the different twitch APIs there are a few helpers.

You can get easy access to three different twitch APIs:

  * `Kraken API <https://github.com/justintv/Twitch-API>`_ witch uses :data:`pytwitcherapi.session.TWITCH_KRAKENURL`. Use :meth:`pytwitcherapi.session.TwitchSession.kraken_request`.
  * Usher API with uses :data:`pytwitcherapi.session.TWITCH_USHERURL`. Use :meth:`pytwitcherapi.session.TwitchSession.usher_request`.
  * The old twitch API :data:`pytwitcherapi.session.TWITCH_APIURL`. Use :meth:`pytwitcherapi.session.TwitchSession.oldapi_request`.

.. literalinclude:: /snippets/apirequest.py
   :linenos:
