--------------
Authentication
--------------

For some methods of :class:`pytwitcherapi.TwitchSession`, the user needs to grant pytwitcher authorization.
Twitch `Authentication <https://dev.twitch.tv/docs/v5/guides/authentication/>`_ is based on OAuth.
We use the `implicit grant workflow <https://dev.twitch.tv/docs/v5/guides/authentication/#oauth-implicit-code-flow-user-access-tokens>`_.
In short, the user visits a website. Has to login, and allow pytwitcher. Twitch will redirect him to :data:`pytwitcherapi.constants.REDIRECT_URI`.
In the url fragment of that redirection, one can find the token we need.
To make it simple for the user, here is what should be done for authentication:

  - Call :meth:`pytwitcherapi.TwitchSession.start_login_server`.
    This will create a thread that serves a server on :data:`pytwitcherapi.constants.LOGIN_SERVER_ADRESS`.
    Once the user gets redirected, this server will pick up the request and
    extract the token:

    .. literalinclude:: /snippets/auth.py
       :linenos:
       :lineno-match:
       :lines: 1-4

  - Get the url :meth:`pytwitcherapi.TwitchSession.get_auth_url` and send
    the user to visit that url in his favorite webbrowser. He might have to login,
    and allow pytwitcher, if he did not already:

    .. literalinclude:: /snippets/auth.py
       :linenos:
       :lineno-match:
       :lines: 6-8

  - Wait until the user finished login in. Then call
    :meth:`pytwitcherapi.TwitchSession.shutdown_login_server` to
    shutdown the server and join the thread:

    .. literalinclude:: /snippets/auth.py
       :linenos:
       :lineno-match:
       :lines: 10-11

  - Check if the user authorized the session with
    :meth:`pytwitcherapi.TwitchSession.authorized`:

    .. literalinclude:: /snippets/auth.py
       :linenos:
       :lineno-match:
       :lines: 13-14

  - Now you can call methods that require authentication:

    .. literalinclude:: /snippets/auth.py
       :linenos:
       :lineno-match:
       :lines: 16
