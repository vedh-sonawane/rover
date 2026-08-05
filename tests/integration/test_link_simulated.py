"""Integration tests: RoverLink driving the SimulatedTransport end to end.

These exercise the full Brain->Body->Brain path (encode -> simulated firmware ->
decode) without any hardware, including the obstacle watchdog.
"""

from rover.link import RoverLink
from rover.protocol.codec import decode_message
from rover.protocol.messages import (
    Direction,
    Event,
    EventKind,
    Response,
    ResponseKind,
)
from rover.transport.simulated import SimulatedTransport


def _responses(messages):
    return [m for m in messages if isinstance(m, Response)]


def _events(messages):
    return [m for m in messages if isinstance(m, Event)]


def test_body_announces_ready_on_open():
    with RoverLink(SimulatedTransport()) as link:
        assert any(e.kind is EventKind.READY for e in _events(link.poll()))


def test_move_forward_is_acked_completed_and_reports_distance():
    transport = SimulatedTransport(distance_cm=40)
    with RoverLink(transport) as link:
        link.poll()  # drain READY
        seq = link.move(Direction.FWD, 10)
        messages = link.poll()

        assert Response(ResponseKind.ACK, seq) in messages
        assert Response(ResponseKind.DONE, seq) in messages
        sensor = [e for e in _events(messages) if e.kind is EventKind.SENS]
        assert sensor and sensor[0].args[0] == "US"
        assert transport.distance_cm == 30  # advanced 10 cm toward the wall


def test_ping_is_answered_with_correlated_pong():
    with RoverLink(SimulatedTransport()) as link:
        link.poll()
        seq = link.ping()
        pongs = [r for r in _responses(link.poll()) if r.kind is ResponseKind.PONG]
        assert pongs and pongs[0].seq == seq


def test_forward_into_obstacle_triggers_watchdog_halt():
    transport = SimulatedTransport(distance_cm=10, safety_stop_cm=15)
    with RoverLink(transport) as link:
        link.poll()
        link.move(Direction.FWD, 5)
        messages = link.poll()

        assert any(e.kind is EventKind.HALT for e in _events(messages))
        assert not any(r.kind is ResponseKind.DONE for r in _responses(messages))
        assert transport.distance_cm == 10  # refused to move


def test_malformed_command_yields_correlated_error():
    transport = SimulatedTransport()
    transport.open()
    transport.read_line()  # drain READY
    transport.write(b"9 FLY UP\n")
    reply = decode_message(transport.read_line())
    assert reply == Response(ResponseKind.ERR, 9, "BADCMD")
