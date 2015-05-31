import pytwitcherapi

ts = pytwitcherapi.TwitchSession()

topgames = ts.top_games()

for game in topgames:
    streams = ts.get_streams(game=game)
    for stream in streams:
        channel = stream.channel
        playlist = ts.get_playlist(channel)
