import pytwitcherapi

ts = pytwitcherapi.TwitchSession()
ts.start_login_server()

import webbrowser
url = ts.get_auth_url()
webbrowser.open(url)

raw_input("Press ENTER when finished")
ts.shutdown_login_server()

assert ts.authorized, "Authorization failed! Did the user allow it?"
print "Login User: %s" % ts.current_user

streams = ts.followed_streams()
