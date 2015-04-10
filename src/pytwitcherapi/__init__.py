__author__ = 'David Zuber'
__email__ = 'zuber.david@gmx.de'
__version__ = '0.1.4'


# this will get rid of some insecure platform warnings
# and enable SNI-support
import urllib3.contrib.pyopenssl
urllib3.contrib.pyopenssl.inject_into_urllib3()
