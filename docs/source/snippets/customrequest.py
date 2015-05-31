import pytwitcherapi

ts = pytwitcherapi.TwitchSession()

# use kraken api
# no need to use the baseurl to api or headers
response1 = ts.kraken_request('GET', 'games/top')

channel = 'some_channel'
response2 = ts.usher_request('GET', 'channels/%s/access_token' % channel)

# regular request
response2 = ts.get('http://localhost')
