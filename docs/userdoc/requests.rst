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

  * `Kraken API <https://github.com/justintv/Twitch-API>`_ witch uses :data:`pytwitcherapi.session.TWITCH_KRAKENURL`.
  * Usher API with uses :data:`pytwitcherapi.session.TWITCH_USHERURL`.
  * The old twitch API :data:`pytwitcherapi.session.TWITCH_APIURL`.

There are three contextmangers to help accessing the api.
When you use one of the contextmangers, it will set the baseurl and headers on the session. So you can ommit the baseurl from your request. For regular requests,
it is recommended to use the :func:`pytwitcherapi.default` context manager. This will make sure that no headers or baserul is set.::

  import pytwitcherapi
  
  ts = pytwitcherapi.TwitchSession()
  # use kraken api
  with pytwitcherapi.kraken(ts):
      # no need to use the baseurl or headers
      response1 = ts.get('games/top')
      # now use default again 
      with pytwitcherapi.default(ts):
          response2 = ts.get('http://localhost')
      # goes back to the kraken api
      response3 = ts.get('games/top')
  # baseurl and headers are back to normal again
  response3 = ts.get('http://localhost')
