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
