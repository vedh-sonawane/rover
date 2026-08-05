"""Rover — AI-powered autonomous mobile assistant (Brain-side Python package)."""

from __future__ import annotations

__version__ = "0.1.0"

from .link import RoverLink
from .protocol.messages import Command, Direction, Event, Response
from .transport.simulated import SimulatedTransport

__all__ = [
    "__version__",
    "RoverLink",
    "SimulatedTransport",
    "Command",
    "Direction",
    "Event",
    "Response",
]
