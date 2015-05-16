import pytest

from pytwitcherapi import constants


@pytest.fixture(scope='session')
def access_token():
    return 'u7amjlndoes3xupi4bb1jrzg2wrcm1'


@pytest.fixture(scope='session')
def auth_redirect_uri(access_token):
    ruri = constants.REDIRECT_URI +\
        '/#access_token=%s&scope=user_read' % access_token
    return ruri


@pytest.fixture(scope='function')
def auth_headers():
    return {'Authorization': 'OAuth u7amjlndoes3xupi4bb1jrzg2wrcm1'}


@pytest.fixture(scope='function')
def authts(ts, auth_redirect_uri, user1):
    def query_login_user():
        return user1

    oldquery = ts.query_login_user
    ts.query_login_user = query_login_user
    uri = auth_redirect_uri.replace('http://', 'https://')
    ts.token_from_fragment(uri)
    ts.query_login_user = oldquery
    return ts
