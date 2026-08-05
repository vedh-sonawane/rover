"""Serialization between :mod:`rover.protocol.messages` objects and wire text.

Four entry points, mirroring the two directions of traffic:

- Brain side encodes commands / decodes replies:
  :func:`encode_command`, :func:`decode_message`
- Body side (and the simulator) decodes commands / encodes replies:
  :func:`decode_command`, :func:`encode_response`, :func:`encode_event`

All ``encode_*`` functions return ``bytes`` including the trailing newline, ready
to hand to a :class:`rover.transport.base.Transport`.
"""

from __future__ import annotations

from .errors import ProtocolError
from .messages import (
    Command,
    Direction,
    Event,
    EventKind,
    Response,
    ResponseKind,
    Verb,
)

TERMINATOR = "\n"
ENCODING = "ascii"

SEQ_MIN = 1
SEQ_MAX = 65535

_MOVE_DIRS = {Direction.FWD.value, Direction.BWD.value}
_TURN_DIRS = {Direction.LEFT.value, Direction.RIGHT.value}


# --------------------------------------------------------------------------- #
# Commands: Brain -> Body
# --------------------------------------------------------------------------- #
def encode_command(cmd: Command) -> bytes:
    """Serialize a :class:`Command` to a wire line (with trailing newline)."""
    _validate_command(cmd.verb, cmd.args)
    tokens: list[str] = []
    if cmd.seq is not None:
        _check_seq(cmd.seq)
        tokens.append(str(cmd.seq))
    tokens.append(cmd.verb.value)
    tokens.extend(cmd.args)
    return _line(tokens)


def decode_command(line: bytes | str) -> Command:
    """Parse a wire line into a :class:`Command`, validating its arguments."""
    tokens = _tokenize(line)
    seq: int | None = None
    if tokens[0].isdigit():
        seq = _check_seq(int(tokens[0]))
        tokens = tokens[1:]
    if not tokens:
        raise ProtocolError("command is missing a verb")
    try:
        verb = Verb(tokens[0])
    except ValueError:
        raise ProtocolError(f"unknown command verb: {tokens[0]!r}") from None
    args = tuple(tokens[1:])
    _validate_command(verb, args)
    return Command(verb, args, seq)


def _validate_command(verb: Verb, args: tuple[str, ...]) -> None:
    if verb is Verb.MOVE:
        _require(len(args) == 2, "MOVE needs <FWD|BWD> <cm>")
        _require(args[0] in _MOVE_DIRS, f"bad MOVE direction: {args[0]!r}")
        _require_int(args[1], minimum=1, name="cm")
    elif verb is Verb.TURN:
        _require(len(args) == 2, "TURN needs <LEFT|RIGHT> <deg>")
        _require(args[0] in _TURN_DIRS, f"bad TURN direction: {args[0]!r}")
        _require_int(args[1], minimum=0, maximum=360, name="deg")
    elif verb in (Verb.STOP, Verb.PING):
        _require(len(args) == 0, f"{verb.value} takes no arguments")
    else:  # pragma: no cover - Verb is exhaustive above
        raise ProtocolError(f"unhandled verb: {verb!r}")


# --------------------------------------------------------------------------- #
# Replies & events: Body -> Brain
# --------------------------------------------------------------------------- #
def encode_response(resp: Response) -> bytes:
    """Serialize a correlated :class:`Response` to a wire line."""
    seq_tok = "-" if resp.seq is None else str(resp.seq)
    tokens = [resp.kind.value, seq_tok]
    if resp.detail is not None:
        tokens.append(resp.detail)
    return _line(tokens)


def encode_event(evt: Event) -> bytes:
    """Serialize an unsolicited :class:`Event` to a wire line."""
    return _line(["EVT", evt.kind.value, *evt.args])


def decode_message(line: bytes | str) -> Response | Event:
    """Parse a Body->Brain line into a :class:`Response` or :class:`Event`."""
    tokens = _tokenize(line)
    if tokens[0] == "EVT":
        return _decode_event(tokens[1:])
    return _decode_response(tokens)


def _decode_response(tokens: list[str]) -> Response:
    try:
        kind = ResponseKind(tokens[0])
    except ValueError:
        raise ProtocolError(f"unknown reply kind: {tokens[0]!r}") from None
    seq: int | None = None
    detail: str | None = None
    if len(tokens) >= 2:
        seq = None if tokens[1] == "-" else _parse_int(tokens[1], name="seq")
    if len(tokens) >= 3:
        detail = " ".join(tokens[2:])
    return Response(kind, seq, detail)


def _decode_event(tokens: list[str]) -> Event:
    if not tokens:
        raise ProtocolError("EVT is missing its kind")
    try:
        kind = EventKind(tokens[0])
    except ValueError:
        raise ProtocolError(f"unknown event kind: {tokens[0]!r}") from None
    return Event(kind, tuple(tokens[1:]))


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _line(tokens: list[str]) -> bytes:
    return (" ".join(tokens) + TERMINATOR).encode(ENCODING)


def _tokenize(line: bytes | str) -> list[str]:
    if isinstance(line, (bytes, bytearray)):
        line = line.decode(ENCODING, errors="strict")
    tokens = line.strip().split()
    if not tokens:
        raise ProtocolError("empty message line")
    return tokens


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _require_int(
    value: str, *, minimum: int | None = None, maximum: int | None = None, name: str
) -> int:
    n = _parse_int(value, name=name)
    if minimum is not None and n < minimum:
        raise ProtocolError(f"{name} must be >= {minimum}, got {n}")
    if maximum is not None and n > maximum:
        raise ProtocolError(f"{name} must be <= {maximum}, got {n}")
    return n


def _parse_int(value: str, *, name: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ProtocolError(f"{name} must be an integer, got {value!r}") from None


def _check_seq(seq: int) -> int:
    if not SEQ_MIN <= seq <= SEQ_MAX:
        raise ProtocolError(f"seq must be in {SEQ_MIN}..{SEQ_MAX}, got {seq}")
    return seq
