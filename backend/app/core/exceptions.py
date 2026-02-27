class DeviceConnectionError(Exception):
    """Raised when a device cannot be reached."""
    pass


class DeviceAuthenticationError(Exception):
    """Raised when device credentials are invalid."""
    pass


class DeviceNotFoundError(Exception):
    """Raised when a device is not found in the database."""
    pass


class StreamError(Exception):
    """Raised when stream operations fail."""
    pass
