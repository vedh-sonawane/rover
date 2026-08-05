"""Protocol-level exceptions."""


class ProtocolError(ValueError):
    """Raised when a message cannot be parsed or fails validation.

    Subclasses ``ValueError`` so callers can catch either. The Body responds to a
    ``ProtocolError`` on an incoming command with ``ERR <seq> BADCMD``.
    """
