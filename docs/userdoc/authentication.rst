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
