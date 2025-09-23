"""Custom exceptions for the connectors package."""


class ChannelError(Exception):
    """Base exception for channel-related errors."""

    pass


class ChannelAuthError(ChannelError):
    """Raised when there is an authentication error with a channel."""

    pass


class ChannelConnectionError(ChannelError):
    """Raised when there is a connection error with a channel."""

    pass


class ChannelDataError(ChannelError):
    """Raised when there is an error with the data received from a channel."""

    pass


class OrderProcessingError(ChannelError):
    """Raised when there is an error processing an order."""

    pass
