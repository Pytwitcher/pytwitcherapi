"""Twitch.tv uses OAuth2 for authorization.
We use the Implicit Grant Workflow.
The user has to visit an authorization site, login, authorize
PyTwitcher. Once he allows PyTwitcher, twitch will redirect him to
:data:`pytwitcherapi.REDIRECT_URI`.
In the url fragment, there is the access token.

This module features a server, that will respond to the redirection of
the user. So if twitch is redirecting to :data:`pytwitcherapi.REDIRECT_URI`,
the server is gonna send a website, which will extract the access token,
send it as a post request and give the user a response,
that everything worked.
"""
import logging
import os
import pkg_resources

import oauthlib.oauth2

from pytwitcherapi import constants

try:
    from http import server
except ImportError:
    import BaseHTTPServer as server


log = logging.getLogger(__name__)


class RedirectHandler(server.BaseHTTPRequestHandler):
    """This request handler will handle the redirection of the user
    when he grants authorization to PyTwitcher and twitch redirects him.
    """

    extract_site_url = '/'
    success_site_url = '/success'

    def _set_headers(self):
        """Set the response and headers

        :returns: None
        :raises: None
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self, ):
        """Handle GET requests

        If the path is '/', a site which extracts the token will be generated.
        This will redirect the user to the '/sucess' page, which shows
        a success message.

        :returns: None
        :rtype: None
        :raises: None
        """
        urld = {self.extract_site_url: 'extract_token_site.html',
                self.success_site_url: 'success_site.html'}
        site = urld.get(self.path)
        if not site:
            log.debug("Requesting false url on login server.")
            self.send_error(404)
            return
        log.debug('Requesting the login server. Responding with %s.', urld)
        self._set_headers()
        self._write_html(site)

    def _write_html(self, filename):
        """Read the html site with the given filename
        from the data directory and write it to :data:`RedirectHandler.wfile`.

        :param filename: the filename to read
        :type filename: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        datapath = os.path.join('html', filename)
        sitepath = pkg_resources.resource_filename('pytwitcherapi', datapath)
        with open(sitepath, 'r') as f:
            html = f.read()
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self, ):
        """Handle POST requests

        When the user is redirected, this handler will respond with a website
        which will send a post request with the url fragment as parameters.
        This will get the parameters and store the original redirection
        url and fragments in :data:`LoginServer.tokenurl`.

        :returns: None
        :rtype: None
        :raises: None
        """
        self._set_headers()
        # convert the parameters back to the original fragment
        # because we need to send the original uri to set_token
        # url fragments will not show up in self.path though.
        # thats why we make the hassle to send it as a post request.
        # Note: oauth does not allow for http connections
        # but twitch does, so we fake it
        ruri = constants.REDIRECT_URI.replace('http://', 'https://')
        self.server.set_token(ruri + self.path.replace('?', '#'))


class LoginServer(server.HTTPServer):
    """This server responds to the redirection of the user
    after he granted authorization.
    """

    def __init__(self, session):
        """Initialize a new server.

        The server will be on :data:`constants.LOGIN_SERVER_ADRESS`.

        :param session: the session that needs a token
        :type session: :class:`requests_oauthlib.OAuth2Session`
        :raises: None
        """
        server.HTTPServer.__init__(self,
                                   constants.LOGIN_SERVER_ADRESS,
                                   RedirectHandler)
        self.session = session
        """The session that needs a token"""

    def set_token(self, redirecturl):
        """Set the token on the session

        :param redirecturl: the original full redirect url
        :type redirecturl: :class:`str`
        :returns: None
        :rtype: None
        :raises: None
        """
        log.debug('Setting the token on %s.' % self.session)
        self.session.token_from_fragment(redirecturl)


class TwitchOAuthClient(oauthlib.oauth2.MobileApplicationClient):
    """This is a client needed for :class:`oauthlib.oauth2.OAuth2Session`.
    It fixes the Authorization header for twitch.

    Usually the Authorization Header looks like this::

        {'Authorization': 'Bearer <<token>>'}

    But Twitch needs it to be like this::

        {'Authorization': 'OAuth <<token>>'}

    So we override :meth:`TwitchOAuthClient._add_bearer_token` to fix the header.
    """

    def _add_bearer_token(self, *args, **kwargs):
        """Add a bearer token to the request uri, body or authorization header.

        This is overwritten to change the headers slightly.
        """
        s = super(TwitchOAuthClient, self)
        uri, headers, body = s._add_bearer_token(*args, **kwargs)
        authheader = headers.get('Authorization')
        if authheader:
            headers['Authorization'] = authheader.replace('Bearer', 'OAuth')
        return uri, headers, body
