.. :changelog:

History
-------

0.1.1 (2015-03-15)
+++++++++++++++++++++++++++++++++++++++

* First release on PyPI.
* Pulled pytwitcherapi out of main project pytwitcher

0.1.2 (2015-03-15)
+++++++++++++++++++++++++++++++++++++++

* Fix wrapping search stream results due to incomplete channel json

0.1.3 (2015-03-23)
+++++++++++++++++++++++++++++++++++++++

* Refactor twitch module into models and session module

0.1.4 (2015-03-23)
+++++++++++++++++++++++++++++++++++++++

* Fix wrap json using actual class instead of cls

0.2.0 (2015-04-12)
+++++++++++++++++++++++++++++++++++++++

* Authentication: User can login and TwitchSession can retrieve followed streams.

0.3.0 (2015-05-08)
+++++++++++++++++++++++++++++++++++++++

* Easier imports. Only import the package for most of the cases.
* Added logging. Configure your logger and pytwitcher will show debug messages.

0.3.1 (2015-05-09)
+++++++++++++++++++++++++++++++++++++++

* Fix login server shutdown by correctly closing the socket

0.4.0 (2015-05-12)
+++++++++++++++++++++++++++++++++++++++

* IRC client for twitch chat

0.5.0 (2015-05-13)
++++++++++++++++++++++++++++++++++++++++

* IRC v3 Tags for messages

0.5.1 (2015-05-13)
++++++++++++++++++++++++++++++++++++++++

* Fix coverage reports via travis

0.6.0 (2015-05-16)
++++++++++++++++++++++++++++++++++++++++

* Add limit for sending messages

0.7.0 (2015-05-16)
++++++++++++++++++++++++++++++++++++++++

* IRCCLient manages two connections. Receives own messages from the server (with tags).
* Improved test thread saftey

0.7.1 (2015-05-22)
++++++++++++++++++++++++++++++++++++++++

* IRCClient shutdown is now thread-safe through events

0.7.2 (2015-05-30)
+++++++++++++++++++++++++++++++++++++++++

* Add TwitchSession.get_emote_picture(emote, size).
* Capabilities for chat: twitch.tv/membership, twitch.tv/commands, twitch.tv/tags

0.8.0 (2015-05-31)
+++++++++++++++++++++++++++++++++++++++++

* Replace context managers for apis with dedicated methods. The context managers
  made it difficult to use a session thread-safe because they relied (more heavily)
  on the state of the session.

0.9.0 (2016-09-16)
+++++++++++++++++++++++++++++++++++++++++

* Remove ``on_schedule`` argument for irc client. ``irc >=15.0`` required.
* `#17 <https://github.com/Pytwitcher/pytwitcherapi/pull/17>`_: Always submit a client id in the headers. Credits to `Coriou <https://github.com/Coriou>`_.
* Client ID can be provided via environment variable ``PYTWITCHER_CLIENT_ID``.

0.9.1 (2016-09-18)
+++++++++++++++++++++++++++++++++++++++++

* Make example chat client python 3 compatible
* `#16 <https://github.com/Pytwitcher/pytwitcherapi/issues/16>`_: Ignore unknown arguments from twitchstatus
* Use Client ID for old api requests as well

0.9.2 (2017-08-27)
+++++++++++++++++++++++++++++++++++++++++

* Fix compatibility to ``irc>=16.0``. Thanks to `crey4fun <https://github.com/crey4fun>`_.

0.9.3 (2017-08-27)
+++++++++++++++++++++++++++++++++++++++++

* Re-release of ``0.9.2``
