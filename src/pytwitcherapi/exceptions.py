"""Collection exceptions"""


__all__ = ['PytwitcherException', 'NotAuthorizedError']


class PytwitcherException(Exception):
    """Base exception for pytwitcher"""
    pass


class NotAuthorizedError(PytwitcherException):
    """Exception that is raised, when the session is not authorized.
    The user has to login first"""
    pass
