"""Central configuration for Rover.

Plain dataclasses with sensible defaults, overridable from environment variables
via :func:`load_config`. Nothing here reaches out to hardware or the network on
import — it just holds values. Keep it small; add fields only when a component
actually needs them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SerialConfig:
    """USB-serial link to the Arduino (used from Phase 2 onward)."""

    port: str = "COM3"  # e.g. "COM3" on Windows, "/dev/ttyUSB0" on Linux
    baud: int = 115200


@dataclass(frozen=True)
class SafetyConfig:
    """Parameters for the Body's safety behavior."""

    watchdog_timeout_ms: int = 500
    safety_stop_cm: float = 15.0


@dataclass(frozen=True)
class ReasoningConfig:
    """Local LLM (Ollama) settings for the reasoning layer (Phase 5)."""

    ollama_host: str = "http://localhost:11434"
    fast_model: str = "llama3.2:3b"  # low-latency command->intent parsing
    reasoning_model: str = "gpt-oss:20b"  # heavier multi-step planning


@dataclass(frozen=True)
class RoverConfig:
    serial: SerialConfig = field(default_factory=SerialConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)
    reasoning: ReasoningConfig = field(default_factory=ReasoningConfig)


def load_config() -> RoverConfig:
    """Build a config from defaults, applying any ``ROVER_*`` env overrides."""
    return RoverConfig(
        serial=SerialConfig(
            port=os.environ.get("ROVER_SERIAL_PORT", SerialConfig.port),
            baud=int(os.environ.get("ROVER_SERIAL_BAUD", SerialConfig.baud)),
        ),
        safety=SafetyConfig(
            watchdog_timeout_ms=int(
                os.environ.get("ROVER_WATCHDOG_MS", SafetyConfig.watchdog_timeout_ms)
            ),
            safety_stop_cm=float(
                os.environ.get("ROVER_SAFETY_STOP_CM", SafetyConfig.safety_stop_cm)
            ),
        ),
        reasoning=ReasoningConfig(
            ollama_host=os.environ.get("ROVER_OLLAMA_HOST", ReasoningConfig.ollama_host),
            fast_model=os.environ.get("ROVER_FAST_MODEL", ReasoningConfig.fast_model),
            reasoning_model=os.environ.get(
                "ROVER_REASONING_MODEL", ReasoningConfig.reasoning_model
            ),
        ),
    )
