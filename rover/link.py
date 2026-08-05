"""RoverLink — the message-level handle the Brain uses to talk to the Body.

Where :class:`~rover.transport.base.Transport` moves bytes and the codec turns
bytes into messages, ``RoverLink`` ties them together and adds the one bit of
stateful bookkeeping the Brain needs: automatic, monotonically increasing
sequence numbers so replies can be correlated to commands.

It is intentionally transport-agnostic — hand it a ``SimulatedTransport`` today
or a ``SerialTransport`` in Phase 2 and nothing above this class changes.
"""

from __future__ import annotations

from dataclasses import replace

from .protocol.codec import SEQ_MAX, decode_message, encode_command
from .protocol.messages import Command, Direction, Event, Response
from .transport.base import Transport


class RoverLink:
    def __init__(self, transport: Transport, auto_seq: bool = True) -> None:
        self._transport = transport
        self._auto_seq = auto_seq
        self._seq = 0

    # -- lifecycle ---------------------------------------------------------- #
    def open(self) -> "RoverLink":
        self._transport.open()
        return self

    def close(self) -> None:
        self._transport.close()

    def __enter__(self) -> "RoverLink":
        return self.open()

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # -- sending ------------------------------------------------------------ #
    def send(self, command: Command) -> int | None:
        """Send a command; returns the seq used (or None if seq-less)."""
        seq = command.seq
        if seq is None and self._auto_seq:
            seq = self._next_seq()
            command = replace(command, seq=seq)
        self._transport.write(encode_command(command))
        return seq

    def move(self, direction: Direction, cm: int) -> int | None:
        return self.send(Command.move(direction, cm))

    def turn(self, direction: Direction, degrees: int) -> int | None:
        return self.send(Command.turn(direction, degrees))

    def stop(self) -> int | None:
        return self.send(Command.stop())

    def ping(self) -> int | None:
        return self.send(Command.ping())

    # -- receiving ---------------------------------------------------------- #
    def poll(self) -> list[Response | Event]:
        """Drain and decode all currently-available messages from the Body."""
        messages: list[Response | Event] = []
        while True:
            line = self._transport.read_line()
            if line is None:
                break
            messages.append(decode_message(line))
        return messages

    # -- internals ---------------------------------------------------------- #
    def _next_seq(self) -> int:
        self._seq = self._seq % SEQ_MAX + 1
        return self._seq
