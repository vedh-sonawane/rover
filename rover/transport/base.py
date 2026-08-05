"""The Transport interface — the swappable seam between Brain and Body.

A ``Transport`` moves raw bytes, nothing more. It knows nothing about the
protocol. That separation is deliberate: today the concrete transport is USB
serial (Phase 2) or the in-process simulator (Phase 1); in Phase 6 it becomes
Wi-Fi. Because every transport implements this same tiny interface, the code
above it — the protocol codec, the link, the whole Brain — never changes when we
swap one for another.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Transport(ABC):
    """A byte-level, line-oriented, non-blocking link to the robot Body."""

    @abstractmethod
    def open(self) -> None:
        """Open the underlying connection. Idempotent where possible."""

    @abstractmethod
    def close(self) -> None:
        """Close the underlying connection."""

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Whether the transport is currently open."""

    @abstractmethod
    def write(self, data: bytes) -> None:
        """Send raw bytes (a complete, newline-terminated line) to the Body."""

    @abstractmethod
    def read_line(self) -> bytes | None:
        """Return one complete line from the Body, or ``None`` if none is
        currently available. Must not block."""

    def __enter__(self) -> "Transport":
        self.open()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()
