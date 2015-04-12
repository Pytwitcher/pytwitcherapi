import urllib3.contrib.pyopenssl

__author__ = 'David Zuber'
__email__ = 'zuber.david@gmx.de'
__version__ = '0.1.4'


REDIRECT_URI = 'http://localhost:42420'
"""The redirect url of pytwitcher. We do not need to redirect anywhere so localhost is set in the twitch prefrences of pytwitcher"""

# this will get rid of some insecure platform warnings
# and enable SNI-support
urllib3.contrib.pyopenssl.inject_into_urllib3()
