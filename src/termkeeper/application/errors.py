"""Errors raised by application use cases."""


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass


class InitializationError(RuntimeError):
    """Raised when TermKeeper cannot initialize its local resources."""
