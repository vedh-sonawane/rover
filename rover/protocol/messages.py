"""In-memory message model for the Rover wire protocol.

This module defines *what* the messages are; :mod:`rover.protocol.codec` defines
how they are turned into and out of wire text. See ``docs/protocol.md`` for the
authoritative specification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Verb(str, Enum):
    """Command verbs (Brain -> Body)."""

    MOVE = "MOVE"
    TURN = "TURN"
    STOP = "STOP"
    PING = "PING"


class Direction(str, Enum):
    """Movement directions used as the first argument of MOVE/TURN."""

    FWD = "FWD"
    BWD = "BWD"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class ResponseKind(str, Enum):
    """Kinds of correlated reply (Body -> Brain)."""

    ACK = "ACK"
    DONE = "DONE"
    PONG = "PONG"
    ERR = "ERR"


class EventKind(str, Enum):
    """Kinds of unsolicited event (Body -> Brain)."""

    READY = "READY"
    SENS = "SENS"
    HALT = "HALT"
    LOG = "LOG"


@dataclass(frozen=True)
class Command:
    """A command from the Brain to the Body.

    ``args`` are kept as raw strings (as they appear on the wire); the codec
    validates them. Use the constructor helpers for correct, typed creation.
    """

    verb: Verb
    args: tuple[str, ...] = ()
    seq: int | None = None

    @staticmethod
    def move(direction: Direction, cm: int, seq: int | None = None) -> "Command":
        return Command(Verb.MOVE, (direction.value, str(int(cm))), seq)

    @staticmethod
    def turn(direction: Direction, degrees: int, seq: int | None = None) -> "Command":
        return Command(Verb.TURN, (direction.value, str(int(degrees))), seq)

    @staticmethod
    def stop(seq: int | None = None) -> "Command":
        return Command(Verb.STOP, (), seq)

    @staticmethod
    def ping(seq: int | None = None) -> "Command":
        return Command(Verb.PING, (), seq)


@dataclass(frozen=True)
class Response:
    """A correlated reply from the Body to the Brain."""

    kind: ResponseKind
    seq: int | None = None
    detail: str | None = None


@dataclass(frozen=True)
class Event:
    """An unsolicited event from the Body to the Brain."""

    kind: EventKind
    args: tuple[str, ...] = ()


# A decoded Body->Brain message is one of these two.
Message = "Response | Event"
