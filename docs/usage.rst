========
Usage
========

To use pytwitcherapi in a project::

  from pytwitcherapi import twitch

The :mod:`pytwitcherapi.twitch` module centers around the
:class:`pytwitcherapi.twitch.TwitchSession` class::

  ts = twitch.TwitchSession()

To query all top games use::

  topgames = ts.top_games()

Get streams and playlist for every game::

  for game in topgames:
      streams = ts.get_streams(game=game)
      for stream in streams:
          channel = stream.channel
          playlist = ts.get_playlist(channel)

As you can see games, channels, streams are wrapped into objects.
See :class:`pytwitcherapi.twitch.Game`, :class:`pytwitcherapi.twitch.Channel`, :class:`pytwitcherapi.twitch.Stream`, :class:`pytwitcherapi.twitch.User`.


---------------
Custom requests
---------------

You can also issue custom requests. The :class:`pytwitcherapi.twitch.TwitchSession`
is actually a subclass of :class:`requests.Session`. So basically
you can use :meth:`pytwitcherapi.twitch.TwitchSession.request` to issue
arbitrary requests.
To make it easier to use the different twitch APIs there are a few helpers.

You can get easy access to three different twitch APIs:

  * `Kraken API <https://github.com/justintv/Twitch-API>`_ witch uses :data:`pytwitcherapi.twitch.TWITCH_KRAKENURL`.
  * Usher API with uses :data:`pytwitcherapi.twitch.TWITCH_USHERURL`.
  * The old twitch API :data:`pytwitcherapi.twitch.TWITCH_APIURL`.

There are three contextmangers to help accessing the api.
When you use one of the contextmangers, it will set the baseurl and headers on the session. So you can ommit the baseurl from your request::

  from pytwitcherapi import twitch
  
  ts = twitch.TwitchSession()
  # use kraken api
  with twitch.kraken(ts):
      # no need to use the baseurl or headers
      response = ts.get('games/top')
  # baseurl and headers are back to normal again
  respone = ts.get('http://google.com')
