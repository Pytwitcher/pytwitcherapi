------------
API requests
------------

:class:`pytwitcherapi.TwitchSession` class is the central class for interacting with `twitch.tv  <https://github.com/justintv/Twitch-API>`_::

  import pytwitcherapi

  ts = pytwitcherapi.TwitchSession()

To query all top games use::

  topgames = ts.top_games()

Get streams and playlist for every game::

  for game in topgames:
      streams = ts.get_streams(game=game)
      for stream in streams:
          channel = stream.channel
          playlist = ts.get_playlist(channel)

As you can see games, channels, streams are wrapped into objects.
See :class:`pytwitcherapi.Game`, :class:`pytwitcherapi.Channel`, :class:`pytwitcherapi.Stream`, :class:`pytwitcherapi.User`.
