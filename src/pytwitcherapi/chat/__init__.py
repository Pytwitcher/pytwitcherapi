"""Package for interacting with the IRC chat of a channel.

The main client for connecting to the channel is :class:`IRCClient`.
"""
from __future__ import absolute_import

from .client import *
from .message import *
from .connection import *

__all__ = ['IRCClient']
