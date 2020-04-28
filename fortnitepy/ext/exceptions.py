class ExtensionException(Exception):
    """
    Base class for all exceptions in this script
    """
    pass


class InvalidParameters(ExtensionException):
    """
    Invalid parameters passed
    """
    pass


class NoPermissionError(ExtensionException):
    """
    The user has no permission to run this code
    """
    pass
