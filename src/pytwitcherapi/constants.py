"""Collection of constants

These constants might be needed in multiple modules, so we pull them together here.
"""
LOGIN_SERVER_ADRESS = ('', 42420)
"""Server adress of server that catches the redirection and the oauth token."""

REDIRECT_URI = 'http://localhost:42420'
"""The redirect url of pytwitcher. We do not need to redirect anywhere so
localhost is set in the twitch prefrences of pytwitcher"""
