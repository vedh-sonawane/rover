"""An in-process simulation of the robot Body.

This is NOT a fake. It implements the exact same :class:`Transport` byte
interface the real serial link will implement, and it speaks the exact same
protocol (``docs/protocol.md``) that the Arduino firmware will speak. Brain-side
code cannot tell it apart from real hardware — which is the whole point: we can
build and test the Brain, including its handling of the safety watchdog, before
any firmware exists.

The simulated Body maintains one piece of virtual world state: the distance to
whatever is ahead of it (``distance_cm``). Driving forward reduces it; driving
backward increases it. If a forward move is attempted while too close, the Body
refuses and reports ``EVT HALT WATCHDOG`` — exactly as the real firmware's
obstacle watchdog will.
"""

from __future__ import annotations

from collections import deque

from ..protocol.codec import decode_command, encode_event, encode_response
from ..protocol.errors import ProtocolError
from ..protocol.messages import (
    Command,
    Direction,
    Event,
    EventKind,
    Response,
    ResponseKind,
    Verb,
)
from .base import Transport

DEFAULT_DISTANCE_CM = 50.0
DEFAULT_SAFETY_STOP_CM = 15.0


class SimulatedTransport(Transport):
    def __init__(
        self,
        distance_cm: float = DEFAULT_DISTANCE_CM,
        safety_stop_cm: float = DEFAULT_SAFETY_STOP_CM,
    ) -> None:
        self._outbox: deque[bytes] = deque()
        self._open = False
        self._distance = float(distance_cm)
        self._safety_stop = float(safety_stop_cm)

    # -- Transport interface ------------------------------------------------ #
    @property
    def is_open(self) -> bool:
        return self._open

    def open(self) -> None:
        self._open = True
        self._emit(encode_event(Event(EventKind.READY)))

    def close(self) -> None:
        self._open = False

    def write(self, data: bytes) -> None:
        if not self._open:
            raise RuntimeError("SimulatedTransport is not open")
        try:
            cmd = decode_command(data)
        except ProtocolError:
            self._emit(encode_response(Response(ResponseKind.ERR, _leading_seq(data), "BADCMD")))
            return
        self._handle(cmd)

    def read_line(self) -> bytes | None:
        if self._outbox:
            return self._outbox.popleft()
        return None

    # -- Simulated Body behavior ------------------------------------------- #
    def _handle(self, cmd: Command) -> None:
        seq = cmd.seq
        if cmd.verb is Verb.PING:
            self._emit(encode_response(Response(ResponseKind.PONG, seq)))
        elif cmd.verb is Verb.STOP:
            self._ack(seq)
            self._done(seq)
        elif cmd.verb is Verb.TURN:
            self._ack(seq)
            self._done(seq)
            self._emit_sensor()
        elif cmd.verb is Verb.MOVE:
            self._handle_move(cmd, seq)

    def _handle_move(self, cmd: Command, seq: int | None) -> None:
        direction, amount = cmd.args[0], int(cmd.args[1])
        if direction == Direction.FWD.value:
            if self._distance <= self._safety_stop:
                # Obstacle watchdog: refuse to drive into what's ahead.
                self._ack(seq)
                self._emit(encode_event(Event(EventKind.HALT, ("WATCHDOG",))))
                return
            self._distance = max(0.0, self._distance - amount)
        else:  # BWD
            self._distance += amount
        self._ack(seq)
        self._done(seq)
        self._emit_sensor()

    # -- Emit helpers ------------------------------------------------------- #
    def _emit(self, data: bytes) -> None:
        self._outbox.append(data)

    def _ack(self, seq: int | None) -> None:
        self._emit(encode_response(Response(ResponseKind.ACK, seq)))

    def _done(self, seq: int | None) -> None:
        self._emit(encode_response(Response(ResponseKind.DONE, seq)))

    def _emit_sensor(self) -> None:
        self._emit(encode_event(Event(EventKind.SENS, ("US", f"{self._distance:.1f}"))))

    # -- Test / inspection hooks ------------------------------------------- #
    @property
    def distance_cm(self) -> float:
        return self._distance

    def set_distance(self, cm: float) -> None:
        """Place a virtual obstacle at ``cm`` centimeters ahead."""
        self._distance = float(cm)


def _leading_seq(data: bytes) -> int | None:
    """Best-effort extraction of a leading seq from a possibly-malformed line,
    so an ``ERR`` can still be correlated to the offending command."""
    try:
        tokens = data.decode("ascii", errors="replace").strip().split()
    except Exception:  # pragma: no cover - decode with replace won't raise
        return None
    if tokens and tokens[0].isdigit():
        try:
            return int(tokens[0])
        except ValueError:  # pragma: no cover
            return None
    return None
