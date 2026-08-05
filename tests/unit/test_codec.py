"""Unit tests for the protocol codec — the contract both sides implement."""

import pytest

from rover.protocol.codec import (
    decode_command,
    decode_message,
    encode_command,
    encode_event,
    encode_response,
)
from rover.protocol.errors import ProtocolError
from rover.protocol.messages import (
    Command,
    Direction,
    Event,
    EventKind,
    Response,
    ResponseKind,
)


# -- Commands: Brain -> Body ------------------------------------------------ #
def test_move_command_encodes_to_expected_wire_text():
    assert encode_command(Command.move(Direction.FWD, 30, seq=5)) == b"5 MOVE FWD 30\n"


def test_command_round_trips():
    for cmd in [
        Command.move(Direction.FWD, 30, seq=5),
        Command.move(Direction.BWD, 12, seq=6),
        Command.turn(Direction.LEFT, 90, seq=7),
        Command.turn(Direction.RIGHT, 45),
        Command.stop(seq=8),
        Command.ping(),
    ]:
        assert decode_command(encode_command(cmd)) == cmd


def test_command_without_seq_has_none():
    assert decode_command("STOP") == Command.stop()
    assert decode_command("STOP").seq is None


@pytest.mark.parametrize(
    "line",
    [
        "",
        "FLY UP",  # unknown verb
        "MOVE SIDEWAYS 5",  # bad direction
        "MOVE FWD",  # missing arg
        "MOVE FWD abc",  # non-integer
        "MOVE FWD -3",  # below minimum
        "TURN LEFT 999",  # out of range
        "PING 5",  # takes no args
        "70000 STOP",  # seq out of range
    ],
)
def test_malformed_commands_raise(line):
    with pytest.raises(ProtocolError):
        decode_command(line)


# -- Replies & events: Body -> Brain --------------------------------------- #
def test_response_round_trips():
    for resp in [
        Response(ResponseKind.ACK, 5),
        Response(ResponseKind.DONE, 5),
        Response(ResponseKind.PONG, 7),
        Response(ResponseKind.ERR, 9, "BADCMD"),
        Response(ResponseKind.ERR, None, "BADCMD"),  # seq-less error
    ]:
        assert decode_message(encode_response(resp)) == resp


def test_seqless_error_uses_dash_placeholder():
    assert encode_response(Response(ResponseKind.ERR, None, "BADCMD")) == b"ERR - BADCMD\n"


def test_event_round_trips():
    for evt in [
        Event(EventKind.READY),
        Event(EventKind.SENS, ("US", "24.5")),
        Event(EventKind.HALT, ("WATCHDOG",)),
    ]:
        assert decode_message(encode_event(evt)) == evt


def test_decode_message_distinguishes_events_from_replies():
    assert isinstance(decode_message("EVT READY"), Event)
    assert isinstance(decode_message("ACK 5"), Response)
