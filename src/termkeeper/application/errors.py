"""Errors raised by application use cases."""


class ValidationError(ValueError):
    pass


class NotFoundError(LookupError):
    pass
