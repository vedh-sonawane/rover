"""A tiny, runnable demonstration of the Phase 1 Brain talking to a simulated Body.

Run it from the project root:

    python examples/hello_rover.py

Nothing here is faked: the Brain sends real protocol messages over a real
Transport interface, and the simulated Body replies exactly as the Arduino
firmware will. Watch the obstacle watchdog kick in as Rover approaches the wall.
"""

from __future__ import annotations

from rover import RoverLink, SimulatedTransport
from rover.protocol.messages import Direction, Event, EventKind


def show(link: RoverLink) -> None:
    for msg in link.poll():
        arrow = "  <EVT" if isinstance(msg, Event) else "  <   "
        print(f"{arrow} {msg}")


def main() -> None:
    # A wall 35 cm ahead; the Body refuses to drive closer than 15 cm.
    transport = SimulatedTransport(distance_cm=35, safety_stop_cm=15)
    with RoverLink(transport) as link:
        print("Body booted:")
        show(link)

        print("\nPinging the Body...")
        link.ping()
        show(link)

        print("\nDriving forward in 10 cm steps until the watchdog stops us:")
        for _ in range(5):
            link.move(Direction.FWD, 10)
            messages = link.poll()
            for msg in messages:
                arrow = "  <EVT" if isinstance(msg, Event) else "  <   "
                print(f"{arrow} {msg}")
            if any(isinstance(m, Event) and m.kind is EventKind.HALT for m in messages):
                print("  -> Rover stopped itself before hitting the wall. Good robot.")
                break


if __name__ == "__main__":
    main()
