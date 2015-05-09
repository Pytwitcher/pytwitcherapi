========
Usage
========

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

--------------
Authentication
--------------

For some methods of :class:`pytwitcherapi.TwitchSession`, the user needs to grant pytwitcher authorization.
Twitch `Authentication <https://github.com/justintv/Twitch-API/blob/master/authentication.md>`_ is based on OAuth.
We use the `implicit grant workflow <https://github.com/justintv/Twitch-API/blob/master/authentication.md#implicit-grant-flow>`_.
In short, the user visits a website. Has to login, and allow pytwitcher. Twitch will redirect him to :data:`pytwitcherapi.constants.REDIRECT_URI`.
In the url fragment of that redirection, one can find the token we need.
To make it simple for the user, here is what should be done for authentication:

  - Call :meth:`pytwitcherapi.TwitchSession.start_login_server`.
    This will create a thread that serves a server on :data:`pytwitcherapi.constants.LOGIN_SERVER_ADRESS`.
    Once the user gets redirected, this server will pick up the request and
    extract the token::

      import pytwitcherapi
      
      ts = pytwitcherapi.TwitchSession()
      ts.start_login_server()

  - Get the url :meth:`pytwitcherapi.TwitchSession.get_auth_url` and send
    the user to visit that url in his favorite webbrowser. He might have to login,
    and allow pytwitcher, if he did not already::

      import webbrowser
      url = ts.get_auth_url()
      webbrowser.open(url)

  - Wait until the user finished login in. Then call
    :meth:`pytwitcherapi.TwitchSession.shutdown_login_server` to
    shutdown the server and join the thread::

      raw_input("Press ENTER when finished")
      ts.shutdown_login_server()

  - Check if the user authorized the session with
    :meth:`pytwitcherapi.TwitchSession.authorized`::

      assert ts.authorized, "Authorization failed! Did the user allow it?"

  - Now you can call methods that require authentication::

      logined user = ts.fetch_login_user()
      streams = ts.followed_streams()


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
